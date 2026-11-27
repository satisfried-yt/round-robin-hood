# Round Robin Hood - Accueil

**Version 0.9.5** | [Deutsch](../) | [English](../en/)

Round Robin Hood (RRH) répartit le surplus solaire mesuré entre les appareils admissibles selon leur puissance nominale et la stratégie choisie. La mesure de réseau est une puissance instantanée en W ou kW, pas un compteur de kWh.

**Sécurité:** RRH peut commander des appareils réels. Ce logiciel ne remplace jamais une protection électrique ou thermique indépendante ni un arrêt d’urgence physique. Une mauvaise commande peut causer des frais, une surchauffe ou un incendie.

## Accueil

- [Installation et mises à jour](installation.md)
- [Configuration](setup.md)
- [Tableau de bord](dashboard.md)
- [Appareils](consumers.md)
- [Profils et stratégies](profiles.md)
- [Conditions de capteurs](conditions.md)
- [Énergie et coûts](energy.md)
- [Paramètres](settings.md)
- [Capteurs Home Assistant](sensors.md)
- [Comportement au redémarrage](startup.md)
- [Dépannage](troubleshooting.md)
- [Sécurité](safety.md)
- [FAQ](faq.md)
- [Glossaire](glossary.md)
- [À propos](about.md)


## Nouveautés de la version 0.9.5

- Sélection recherchable des entités Home Assistant dans les paramètres, l'assistant, les appareils, les conditions et les données d'énergie, aussi sur mobile.
- Plannings hebdomadaires facultatifs pour profils et appareils, avec jours choisis, plusieurs plages et passage à minuit.
- Les capteurs et les deux plannings doivent autoriser l'action. À la fin d'une plage, RRH arrête les appareils actifs qu'il commande, même avant la durée minimale.
- La configuration existante est conservée et les plannings sont désactivés par défaut. Sauvegardez HA, y compris .storage, avant toute mise à jour.
