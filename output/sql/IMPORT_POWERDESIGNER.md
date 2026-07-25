# Import du schéma HAUQE Certif dans PowerDesigner

Fichier à importer : `HAUQE_CERTIF_POWERDESIGNER.sql`

## Méthode recommandée

1. Ouvrir PowerDesigner.
2. Créer un nouveau **Physical Data Model / Modèle physique de données**.
3. Choisir PostgreSQL comme SGBD.
4. Ouvrir la fonction **Database > Reverse Engineer Database**.
5. Choisir la rétroconception à partir d'un fichier script.
6. Sélectionner `HAUQE_CERTIF_POWERDESIGNER.sql`.
7. Sélectionner le schéma `hauqe_certif`.
8. Lancer la rétroconception.
9. Utiliser **Layout > Auto Layout** pour organiser les tables.
10. Enregistrer le modèle au format `.pdm`.

## Résultat attendu

- 66 tables ;
- 105 clés étrangères ;
- 9 contraintes d'unicité ;
- index sur les clés étrangères ;
- types PostgreSQL ;
- relations automatiquement dessinées.

## Compatibilité PowerDesigner

La version corrigée limite à 31 caractères les codes des contraintes, index et triggers afin de respecter la règle de validation du SGBD configuré dans PowerDesigner. Les colonnes portant une contrainte d'unicité sont également déclarées `NOT NULL`.

Si une première version du modèle a déjà été importée, créer de préférence un nouveau MPD puis relancer la rétroconception avec le fichier corrigé. Cela évite de conserver les anciens noms de contraintes et d'index dans le modèle.

La génération d'un modèle conceptuel depuis le MPD pourra ensuite être lancée dans PowerDesigner. Les noms métier des associations et les cardinalités minimales devront être relus après génération.
