# Installation et mises à jour

Avant toute mise à jour, utilisez **Tout arrêter** et vérifiez physiquement que les appareils sont éteints. La pause ne coupe pas l’alimentation. Créez une sauvegarde Home Assistant complète, y compris `.storage`.

Pour une installation initiale, copiez `custom_components/round_robin_hood` dans `/config/custom_components/`, redémarrez Home Assistant Core, puis ajoutez l’intégration dans **Paramètres > Appareils et services**. L’assistant de configuration vous guide ensuite.

Lors d’une mise à jour depuis **0.9.4**, suivez `docs/UPDATE_0.9.5.md`. Pour revenir en arrière, restaurez **ensemble** le code et le fichier RRH `.storage` correspondant, uniquement avec HA Core arrêté. Une sauvegarde complète reste l’option la plus sûre.

---

[Accueil](index.md) | [Sécurité](safety.md)


## Mise à jour de 0.9.4 vers 0.9.5

- Utilisez Tout arrêter dans RRH et vérifiez chaque actionneur. La pause ne coupe pas les appareils.
- Effectuez une sauvegarde complète de Home Assistant, y compris /config/.storage. Désactivez le démarrage automatique pendant la mise à jour si nécessaire.
- Installez v0.9.5 depuis HACS/Marketplace ou le paquet officiel GitHub. En installation manuelle, remplacez uniquement custom_components/round_robin_hood. Détails et retour arrière : docs/UPDATE_0.9.5.md.
- Redémarrez HA Core et vérifiez appareils, profils, conditions, statistiques, sélecteurs d'entités et nouveaux plannings.
- Les plannings sont désactivés initialement. Pour revenir en arrière, restaurez ensemble le code et le fichier .storage avec HA Core arrêté.
