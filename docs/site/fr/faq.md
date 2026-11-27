# FAQ

**RRH a-t-il besoin de sa propre simulation ?** Non. En usage normal, il lit un vrai capteur de puissance réseau. La démo est facultative et isolée.

**Pourquoi l’appareil reste-t-il actif lorsque l’injection devient nulle ?** La puissance consommée par RRH est déjà reflétée dans le compteur : elle ne doit pas être soustraite deux fois.

**Pause éteint-elle les appareils ?** Non. Utilisez Tout arrêter, puis vérifiez physiquement.

**Les statistiques représentent-elles une facture ?** Non, elles reposent sur des valeurs nominales et les tarifs configurés.

---

[Accueil](index.md) | [Sécurité](safety.md)


## FAQ de la version 0.9.5

- Pourquoi un appareil ne démarre-t-il pas malgré le surplus ? Vérifiez le profil, les deux plannings, les capteurs, le délai de redémarrage et le capteur réseau. Le statut indique la raison du blocage.
- Comment autoriser lundi 22:00 jusqu'à mardi 02:00 ? Choisissez lundi et 22:00–02:00. Le jour indique le début et la fin est exclue.
- Plusieurs plages sont-elles possibles ? Oui. Une plage suffit dans un même planning, mais plannings du profil et de l'appareil doivent tous deux autoriser.
- RRH arrête-t-il à la fin ? Oui, les appareils actifs qu'il commande, même pendant la durée minimale. Il n'adopte pas les appareils allumés de l'extérieur.
- Les notifications téléphone/haut-parleur sont-elles incluses ? Non, elles sont prévues pour une version ultérieure.
