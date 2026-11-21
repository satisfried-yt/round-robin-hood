# Appareils

Créez un appareil avec un **nom**, une **icône**, l’**entité HA de commande** et sa **puissance nominale (W)**. L’entité doit être autorisée et ne peut pas appartenir à deux appareils RRH. Les cartes montrent l’état confirmé, la participation et les raisons d’attente.

Modes : **interrupteur on/off**, **plusieurs niveaux** ou **régulation continue**. Configurez pour chaque niveau son action et ses watts. Vérifiez qu’une valeur `number` de 0 éteint vraiment le matériel. Les protections de durée minimale et de redémarrage réduisent les commutations rapides.

Supprimer un appareil RRH ne supprime jamais l’entité Home Assistant.

---

[Accueil](index.md) | [Sécurité](safety.md)
