# Conditions de capteurs

Les conditions évaluent une entité numérique HA, un opérateur (`<`, `<=`, `>`, `>=`), un seuil et une **hystérésis**. Les groupes **TOUTES** et **UNE AU MOINS** permettent de combiner des conditions. Elles peuvent s’appliquer à un appareil ou à un profil.

Un capteur inconnu ou indisponible ne donne pas l’autorisation de démarrer. Une condition logicielle de température **ne remplace pas** un limiteur thermique indépendant.

---

[Accueil](index.md) | [Sécurité](safety.md)


## Combiner conditions de capteurs et horaires (0.9.5)

Les conditions numériques et les plannings hebdomadaires peuvent être activés indépendamment. Les règles du capteur conservent leur ET/OU ; le planning est toujours un ET supplémentaire.

Un appareil démarre uniquement si le profil est actif, le planning du profil autorisé, son propre planning autorisé et toutes les conditions numériques applicables remplies.

Un capteur invalide empêche le démarrage. À la fin d'une plage, RRH arrête les appareils qu'il gère sans attendre la durée minimale. Les conditions logicielles ne remplacent pas les protections indépendantes.

Le sélecteur Home Assistant permet la recherche d'entités numériques. Réglez les plages dans les éditeurs de profil et d'appareil.
