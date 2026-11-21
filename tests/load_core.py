"""Import real HA-independent production modules without importing HA bootstrap.

This is NOT a replacement of controller/model; only the package __init__ (the HA
integration loader) is bypassed for unit tests. No installed HA is required.
"""
from pathlib import Path
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "round_robin_hood"
if "rrh_tested" not in sys.modules:
    pkg = ModuleType("rrh_tested")
    pkg.__path__ = [str(COMPONENT)]
    sys.modules["rrh_tested"] = pkg
