"""Explicit HA boundary doubles, NOT a fake installed Home Assistant.

The production adapter/bootstrap/API are imported unchanged. Store, event bus,
service registry, panel registration, schemas and websocket decorators are test
substitutes. Their presence must never be reported as an actual HA integration run.
"""
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
from functools import wraps
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from uuid import uuid4
from unittest.mock import patch

import load_core


def module(name, **items):
    m=ModuleType(name)
    for key,value in items.items(): setattr(m,key,value)
    return m


def callback(func): return func


class Context:
    def __init__(self, *, user_id=None, parent_id=None):
        self.id=uuid4().hex; self.user_id=user_id; self.parent_id=parent_id


class Store:
    def __init__(self,hass,version,key,*,atomic_writes=False):
        self.hass=hass; self.version=version; self.key=key; self.atomic_writes=atomic_writes
        self.path=Path(hass.path)/key
    async def async_load(self):
        return json.loads(self.path.read_text())["data"] if self.path.exists() else None
    async def async_save(self,data):
        target=self.path.with_suffix(".tmp")
        target.write_text(json.dumps({"version":self.version,"key":self.key,"data":data}))
        target.replace(self.path)


class States:
    def __init__(self,hass): self.hass=hass; self.values={}
    def get(self,key): return self.values.get(key)
    def set(self,key,state,attributes=None,context=None,*,timestamp=None):
        old=self.get(key)
        new=SimpleNamespace(entity_id=key,state=state,attributes=attributes or {},last_reported=timestamp or datetime.now(timezone.utc),context=context or Context())
        self.values[key]=new
        report=bool(old and old.state==new.state and old.attributes==new.attributes)
        event=SimpleNamespace(data={"entity_id":key,"old_state":old,"new_state":new},context=new.context)
        for kind,ids,fn in list(self.hass.listeners):
            if kind==("report" if report else "change") and key in ids: fn(event)


class Services:
    def __init__(self,hass): self.hass=hass; self.calls=[]; self.available=True
    def has_service(self,domain,service): return self.available and domain=="switch" and service in ("turn_on","turn_off")
    async def async_call(self,domain,service,data,*,blocking,context):
        assert blocking is True
        self.calls.append((domain,service,data,context))
        for entity_id in ([data["entity_id"]] if isinstance(data["entity_id"], str) else data["entity_id"]):
            self.hass.states.set(entity_id,"on" if service=="turn_on" else "off",context=context)


class Hass:
    def __init__(self,path):
        self.path=path; self.data={}; self.listeners=[]; self.timers=[]; self.panels={}; self.commands={}; self.tasks=[]; self.old_entries=[]
        self.states=States(self); self.services=Services(self)
        self.http=SimpleNamespace(paths=[],async_register_static_paths=self.register_paths)
        self.config_entries=SimpleNamespace(async_entries=lambda domain:self.old_entries if domain=="round_robin_hood" else [])
        self.bus=SimpleNamespace(async_listen_once=lambda name,fn:lambda:None)
    async def async_add_executor_job(self,fn,*args): return await asyncio.to_thread(fn,*args)
    async def register_paths(self,paths): self.http.paths.extend(paths)
    async def drain(self):
        while self.tasks:
            tasks,self.tasks=self.tasks,[]; await asyncio.gather(*tasks)
        rt=self.data.get("round_robin_hood",{}).get("runtime")
        if rt: await rt.controller.settle()


def watch(hass,ids,fn,kind):
    item=(kind,ids,fn); hass.listeners.append(item)
    return lambda:hass.listeners.remove(item) if item in hass.listeners else None


def interval(hass,fn,delta):
    hass.timers.append(fn)
    return lambda:hass.timers.remove(fn) if fn in hass.timers else None


def ws_command(schema):
    def decorate(fn): fn.command_type=schema["type"]; fn.schema=schema; return fn
    return decorate


def admin(fn):
    @wraps(fn)
    def wrapped(hass,conn,msg):
        if conn.user is None or not conn.user.is_admin: raise PermissionError("admin required (double)")
        return fn(hass,conn,msg)
    return wrapped


def response(fn):
    @wraps(fn)
    def wrapped(hass,conn,msg): hass.tasks.append(asyncio.create_task(fn(hass,conn,msg)))
    return wrapped


async def register_panel(hass,**kwargs): hass.panels[kwargs["frontend_url_path"]]=kwargs


class StaticPath:
    def __init__(self,url_path,path,cache_headers): self.url_path=url_path; self.path=path; self.cache_headers=cache_headers


class Flow:
    def __init_subclass__(cls,domain=None): cls.domain=domain
    def __init__(self): self.configured=False; self.existing=[]
    def _async_current_entries(self): return self.existing
    def async_abort(self,**kwargs): return {"type":"abort",**kwargs}
    async def async_set_unique_id(self,uid): self.uid=uid
    def _abort_if_unique_id_configured(self):
        if self.configured: raise UserWarning("already configured")
    def async_create_entry(self,**kwargs): return {"type":"create_entry",**kwargs}
    def async_show_form(self,**kwargs): return {"type":"form",**kwargs}


class Connection:
    def __init__(self,admin=True): self.user=SimpleNamespace(is_admin=admin); self.results=[]; self.errors=[]
    def send_result(self,id,data): self.results.append((id,deepcopy(data)))
    def send_error(self,id,code,message): self.errors.append((id,code,message))


def stubs():
    ws=module("homeassistant.components.websocket_api",websocket_command=ws_command,require_admin=admin,async_response=response,
              async_register_command=lambda hass,fn:hass.commands.update({fn.command_type:fn}))
    front=module("homeassistant.components.frontend",async_remove_panel=lambda hass,path:hass.panels.pop(path,None))
    panel=module("homeassistant.components.panel_custom",async_register_panel=register_panel)
    cv=module("homeassistant.helpers.config_validation",config_entry_only_config_schema=lambda domain:lambda x:x)
    modules={
        "probatio":module("probatio",Required=lambda x:x,Optional=lambda x:x,In=lambda x:lambda y:y),
        "homeassistant":module("homeassistant"),
        "homeassistant.components":module("homeassistant.components",websocket_api=ws,frontend=front,panel_custom=panel),
        "homeassistant.components.websocket_api":ws,"homeassistant.components.frontend":front,"homeassistant.components.panel_custom":panel,
        "homeassistant.components.http":module("homeassistant.components.http",StaticPathConfig=StaticPath),
        "homeassistant.core":module("homeassistant.core",HomeAssistant=Hass,Context=Context,callback=callback),
        "homeassistant.const":module("homeassistant.const",EVENT_HOMEASSISTANT_STOP="homeassistant_stop"),
        "homeassistant.config_entries":module("homeassistant.config_entries",ConfigFlow=Flow),
        "homeassistant.exceptions":module("homeassistant.exceptions",ConfigEntryError=RuntimeError),
        "homeassistant.helpers":module("homeassistant.helpers",config_validation=cv),
        "homeassistant.helpers.config_validation":cv,
        "homeassistant.helpers.storage":module("homeassistant.helpers.storage",Store=Store),
        "homeassistant.helpers.event":module("homeassistant.helpers.event",async_track_state_change_event=lambda h,ids,fn:watch(h,ids,fn,"change"),async_track_state_report_event=lambda h,ids,fn:watch(h,ids,fn,"report"),async_track_time_interval=interval),
        "homeassistant.util":module("homeassistant.util",dt=SimpleNamespace(utcnow=lambda:datetime.now(timezone.utc))),
    }
    return patch.dict(sys.modules,modules)
