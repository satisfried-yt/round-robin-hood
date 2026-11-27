# Dépannage

Si RRH reste arrêté après un redémarrage, vérifiez la politique de démarrage, le capteur réseau (signe, unité, fraîcheur), les états des appareils et les **journaux de Home Assistant**. Un appareil indisponible peut bloquer un redémarrage automatique.

Si aucun appareil ne démarre, vérifiez la réserve, les profils, les conditions, les temporisations et le surplus mesuré. Si un capteur de prix n’apparaît pas, contrôlez son unité. Après un échec de mise à jour, n’exécutez pas la même commande en boucle ; utilisez la sauvegarde et le guide de restauration.

---

[Accueil](index.md) | [Sécurité](safety.md)


## Dépannage : plannings et recherche (0.9.5)

Pas de démarrage malgré le surplus : consultez le statut de l'appareil et du profil. Les deux plannings et les capteurs doivent autoriser. Vérifiez aussi le compteur réseau, la réserve, les watts et le délai de redémarrage.

Heure ou jour inattendu : contrôlez le fuseau horaire Home Assistant. Les plages de nuit appartiennent au jour de début. Les changements d'heure peuvent supprimer ou répéter une heure locale.

Entité introuvable : vérifiez l'entité, son domaine et son unité. Les anciennes références sont conservées autant que possible. Si l'ancienne interface apparaît, actualisez le cache du navigateur et redémarrez HA.

Si l'arrêt n'est pas confirmé, vérifiez l'actionneur réel et les journaux HA. RRH n'est pas un arrêt d'urgence électrique.
