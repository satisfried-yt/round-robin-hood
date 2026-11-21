# Capteurs Home Assistant

Le **capteur réseau** mesure la puissance instantanée W/kW ; un compteur cumulatif en kWh est inadapté à la régulation. Vérifiez le signe de l’injection dans les outils de Home Assistant.

Les **capteurs de prix** doivent fournir une valeur numérique et une unité de devise par kWh compatible (ex. `EUR/kWh`, `ct/kWh`). Les sources PV utilisent des unités de puissance W/kW ; les compteurs d’énergie Wh/kWh/MWh. Une valeur `unknown`, `unavailable` ou non numérique n’est pas valide. Une mesure restaurée sans nouvelle mise à jour n’autorise pas de nouveau démarrage.

---

[Accueil](index.md) | [Sécurité](safety.md)
