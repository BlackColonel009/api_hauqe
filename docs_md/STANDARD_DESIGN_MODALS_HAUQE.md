# Standard de design des modals HAUQE

À compter du 30 juillet 2026, les nouveaux modals métier de HAUQE Certif
reprennent la fiche opérationnelle validée sur les pages Échéances et Alertes.

## Structure obligatoire

1. Bandeau institutionnel vert HAUQE avec icône, contexte, titre et fermeture.
2. Carte de synthèse chevauchant légèrement le bandeau : date, ressource et statut.
3. Zone centrale en deux parties lorsque les données le permettent :
   contenu principal à gauche et panneau « Repères » à droite.
4. Défilement vertical interne au contenu pour conserver l’entête et les actions.
5. Pied blanc fixe avec note de traçabilité et actions clairement hiérarchisées.

## Principes visuels

- Vert profond et vert institutionnel comme couleurs principales.
- Doré discret pour l’identité institutionnelle.
- Cartes blanches, bordures vert-gris légères et ombres modérées.
- Couleurs métier réservées aux statuts et niveaux de criticité.
- Coins compris entre 11 et 26 pixels selon le niveau de conteneur.
- Responsive mobile obligatoire et compatibilité avec le thème sombre.

## Interaction

- Une seule action principale verte par modal.
- Fermeture accessible par un bouton avec libellé ARIA.
- Aucun contenu ne doit disparaître au zoom : overflow interne obligatoire.
- Toute action métier sensible doit rappeler sa journalisation.
