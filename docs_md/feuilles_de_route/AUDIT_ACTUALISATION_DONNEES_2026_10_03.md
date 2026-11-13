# Audit de l'actualisation des données — 3 octobre 2026

## Suivi de réalisation après cet audit — version 20261003-3

Les sections suivantes sont le constat initial, conservé pour traçabilité.
Depuis, les 7 registres métier manquants (Organismes, Campagnes, FUCCS, Veille,
Scoring, INFC, SNCC) sont raccordés. Chaque écran raccordé a un horodatage
HH:mm:ss. La suspension liée aux saisies de modals, l'objet selected d'Alertes
et Veille et la registration tardive d'une page quittée sont corrigés.
Douze tests Node réussis. Les fiches détail/Parcours et les autres modules hors
de ce lot restent à traiter ; recette navigateur multi-session encore à faire.

Audit du code uniquement, sans modification applicative pendant cet audit.
Les changements Git existants sont préservés. Aucune validation navigateur
multi-session n'est revendiquée. Base PostgreSQL modifiée : non.

## Périmètre effectivement raccordé

Les scripts Dashboard, Entreprises, Certifications, Collectes, Vérifications,
Validations, Intégrations, Alertes/notifications et Échéances enregistrent un
chargeur via `HAUQE_REGISTER_DATA_REFRESH`. Le minuteur ne renavigue pas.
Le correctif commun de détection des dialogues natifs fermés s'applique à tous.

Les registres Organismes, Gestion des campagnes, Contrôle FUCCS, Cellule de
veille, Scoring, INFC et Classement SNCC ne sont pas raccordés. Les rubriques
Rapports, Administration, Référentiels, Zones et Règles ne le sont pas non plus.
Les formulaires et les fiches détail ne sont pas rechargés automatiquement.

## Constats à traiter

1. **Élevée — Suspension après modification d'un formulaire.** Dans app-shell,
   `pageFormDirty` est positionné par input/change puis remis à zéro seulement
   après une navigation/page-ready ou un rafraîchissement manuel. Fermer ou
   enregistrer un modal ne le réinitialise pas. Après une saisie, le polling
   peut donc rester suspendu jusqu'à la prochaine navigation. Prévoir un suivi
   par formulaire et une remise à zéro explicite après succès, sans effacer
   les brouillons conservés après fermeture.
2. **Élevée — Couverture partielle.** Le réglage de profil semble général,
   mais seules les rubriques raccordées l'appliquent. Ajouter des chargeurs
   spécifiques, pas des navigations périodiques ni une réinitialisation globale.
3. **Moyenne — Détail d'une alerte potentiellement ancien.** loadAlerts remplace
   la liste mais conserve l'objet `selected` s'il existe toujours. Il devrait
   le remplacer par la version récente de la réponse, avant renderDetail.
4. **Moyenne — Parcours de dossier.** Les panneaux suivent l'événement
   `hauqe:dossier-parcours-changed`, notamment après des écritures locales.
   Ils ne disposent pas d'un chargeur périodique enregistré sur les pages
   détail ; ne pas promettre la réception automatique des changements d'une
   autre session sur ces écrans.
5. **Moyenne — Courses de chargement.** La validation d'une réponse tardive
   doit conserver une référence à la page d'origine. Le contrat actuel de
   registration capture le hash et la racine au moment de l'enregistrement,
   après l'initialisation asynchrone ; tester la navigation rapide A → B pendant
   le chargement initial, avant d'étendre le mécanisme.

## Protections déjà présentes

- Pause sur modal réellement ouvert, champ actif, onglet caché, action en cours
  et formulaire modifié. Nouvelle vérification après réponse API.
- Filtres/tri/pagination gardés dans l'état des registres raccordés.
- Entreprises conserve sa sélection dans un Set ; Collectes conserve les
  campagnes dépliées dans `expandedCampaigns`.
- Échéances préserve les sélections des filtres du registre consolidé.
- Les boutons statiques ne sont pas réinitialisés par le minuteur ; les actions
  des lignes redessinées sont réinstallées par les renderers existants. Leur
  réactivité réelle après plusieurs cycles reste à tester au navigateur.
- L'heure Entreprises ne montre que les minutes : plusieurs rafraîchissements
  de 15 secondes dans une même minute ont la même heure affichée.

## Vérifications effectuées

- Six tests Node du mécanisme commun réussis.
- Syntaxe des neuf scripts de pages raccordées vérifiée avec `node --check`.
- Aucun test navigateur réel, aucun test SMTP, aucune écriture en base.

## Ordre recommandé des correctifs

1. Corriger le suivi des formulaires modifiés et la sélection d'alerte.
2. Tester deux sessions, navigation rapide, modal rempli puis enregistré,
   fermeture avec brouillon, filtres et clics répétés pendant plusieurs cycles.
3. Étendre aux registres manquants, bloc par bloc, puis aux panneaux de lecture
   des fiches détail ; laisser les inputs des formulaires intacts.
