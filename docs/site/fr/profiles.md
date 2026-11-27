# Profils et stratégies

Les profils partagent une seule puissance disponible. Leur **priorité** fixe l’ordre d’allocation. Chaque profil possède ses propres participants, sa stratégie et ses paramètres. Les conditions peuvent suspendre un profil.

Les huit stratégies sont décrites ci-dessous. Selon le mode, configurez l’autorisation de sauter une charge trop grande, la période de comparaison, l’intervalle de rotation, le gain minimal et la marge de démarrage. Les valeurs de watts sont des estimations.

## Profils et stratégies

- Tour à tour : rotation entre les appareils éligibles.
- Durée équitable : priorité au temps confirmé le plus faible.
- Énergie équitable : priorité aux Wh estimés les plus faibles.
- Priorité fixe : l’ordre défini reste prioritaire.
- Efficacité maximale : recherche une combinaison consommant davantage de surplus.
- Puissance croissante : petits appareils en premier.
- Puissance décroissante : grands appareils en premier.
- Fonctionnement stable : évite les changements non nécessaires.

---

[Accueil](index.md) | [Sécurité](safety.md)


## Plannings hebdomadaires des profils (depuis 0.9.5)

Dans Profils → Modifier, activez un planning propre au profil. Chaque plage accepte plusieurs jours, une heure de début et de fin, ainsi que plusieurs plages par jour.

Les plannings du profil et des appareils sont indépendants. Pour autoriser un démarrage, il faut un profil actif, les deux plannings autorisés et toutes les conditions de capteurs requises. La stratégie choisit ensuite parmi les appareils admissibles.

À la fermeture du planning, RRH demande l'arrêt confirmé des appareils actifs gérés du profil ; un arrêt groupé est possible. Les appareils allumés de manière externe ne sont pas adoptés.

Les plages passant minuit relèvent du jour de départ. Le fuseau horaire de Home Assistant et les changements d'heure sont respectés. Le panneau montre le prochain début.
