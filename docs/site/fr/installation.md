# Installation et mises à jour

Avant toute mise à jour, utilisez **Tout arrêter** et vérifiez physiquement que les appareils sont éteints. La pause ne coupe pas l’alimentation. Créez une sauvegarde Home Assistant complète, y compris `.storage`.

Pour une installation initiale, copiez `custom_components/round_robin_hood` dans `/config/custom_components/`, redémarrez Home Assistant Core, puis ajoutez l’intégration dans **Paramètres > Appareils et services**. L’assistant de configuration vous guide ensuite.

Lors d’une mise à jour depuis **0.9.2**, suivez `docs/UPDATE_0.9.3.md`. Pour revenir en arrière, restaurez **ensemble** le code et le fichier RRH `.storage` correspondant, uniquement avec HA Core arrêté. Une sauvegarde complète reste l’option la plus sûre.

---

[Accueil](index.md) | [Sécurité](safety.md)
