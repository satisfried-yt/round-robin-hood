# Appareils

Créez un appareil avec un **nom**, une **icône**, l’**entité HA de commande** et sa **puissance nominale (W)**. L’entité doit être autorisée et ne peut pas appartenir à deux appareils RRH. Les cartes montrent l’état confirmé, la participation et les raisons d’attente.

Modes : **interrupteur on/off**, **plusieurs niveaux** ou **régulation continue**. Configurez pour chaque niveau son action et ses watts. Vérifiez qu’une valeur `number` de 0 éteint vraiment le matériel. Les protections de durée minimale et de redémarrage réduisent les commutations rapides.

Supprimer un appareil RRH ne supprime jamais l’entité Home Assistant.

---

[Accueil](index.md) | [Sécurité](safety.md)


## Nouveau en 0.9.5 : recherche et planning des appareils

Dans Appareils → Modifier, choisissez les entités de commande et de niveau grâce au sélecteur Home Assistant avec recherche par nom ou identifiant. Les valeurs existantes sont conservées.

Activez le planning uniquement si nécessaire. Ajoutez plusieurs plages, choisissez les jours lun–dim et saisissez le début et la fin (HH:MM). Un planning désactivé ne limite pas le fonctionnement.

Pour lundi 22:00–mardi 02:00, choisissez lundi : le jour désigne le début. La fin est exclue. Plusieurs plages sont liées par OU ; planning du profil et conditions des capteurs restent requis par ET.

À la fermeture de la plage, RRH arrête ses appareils actifs même durant la durée minimale. Cela ne remplace pas une protection thermique ou électrique indépendante. Le prochain début s'affiche dans le fuseau HA.
