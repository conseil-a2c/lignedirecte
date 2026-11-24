# Ligne Directe

Site personnel de recherche d'emploi : offres récentes (06, Monaco, télétravail, direction, CFA), missions en indépendante, organismes de formation et certificateurs, CV réécrit pour chaque offre, suivi des candidatures et relances.

Les offres se mettent à jour chaque matin grâce au robot GitHub (onglet **Actions**). Aucune donnée personnelle n'est stockée ici : votre CV et vos candidatures restent dans votre navigateur.

## Mise en ligne (une seule fois, 10 minutes)

1. Sur github.com, cliquez sur **+** en haut à droite, puis **New repository**.
   - Nom : `lignedirecte`
   - Cochez **Public** (obligatoire pour l'hébergement gratuit ; aucune donnée personnelle n'est dans les fichiers).
   - Cliquez sur **Create repository**.
2. Sur la page du dépôt, cliquez sur **uploading an existing file**, puis glissez **tout le contenu** du dossier décompressé (fichiers *et* dossiers, y compris `.github`). Cliquez sur **Commit changes**.
   - Sur Mac, le dossier `.github` est caché : dans le Finder, appuyez sur **Cmd + Maj + .** pour l'afficher avant de glisser.
3. Allez dans **Settings → Pages**. Sous « Branch », choisissez **main** et **/ (root)**, puis **Save**.
   Au bout d'une minute, l'adresse du site s'affiche : `https://VOTRE-NOM.github.io/lignedirecte/`
4. Allez dans **Settings → Actions → General**. Sous « Workflow permissions », cochez **Read and write permissions**, puis **Save**.
5. Allez dans l'onglet **Actions**, cliquez sur **Collecte quotidienne des offres**, puis **Run workflow** pour faire un premier essai. Il dure entre 30 et 90 minutes ; une coche verte indique que c'est réussi.

## Première ouverture

1. Ouvrez votre adresse dans Safari ou Chrome.
2. Onglet **Mon CV** → **Importer une sauvegarde** → choisissez `sauvegarde-ligne-directe.json` (fourni à part, à ne pas mettre sur GitHub).
3. Facultatif : collez votre clé d'IA dans **Rédaction automatique** pour activer la réécriture du CV et les messages.
4. Sur iPhone : Safari → Partager → **Sur l'écran d'accueil**.

## Modifier les recherches

Le fichier `scripts/recherches.json` liste les recherches collectées chaque jour. Sur GitHub, ouvrez-le, cliquez sur le crayon, modifiez, puis **Commit changes**. Chaque ligne :
`{"mots": "directeur de site", "dept": "06", "jours": 14, "max": 30, "salaire": true, "piste": "dg"}`
- `dept` : numéro de département, `MC` pour Monaco, vide pour toute la France
- `jours` : ancienneté maximale des offres (1, 3, 7, 14 ou 31)
- `contrats` : `LIB` pour les missions en indépendante (par défaut CDI, CDD, intérim)
- `salaire` : `true` pour lire le salaire de chaque offre (plus lent)
- `piste` : `dg` (direction), `cfa` ou absent

## Bon à savoir

- Source des offres : pages publiques de candidat.francetravail.fr et de ses partenaires.
- Organismes de formation : liste publique du Ministère du Travail. Certificateurs : répertoire de France Compétences (RNCP et RS).
- GitHub met en pause les robots d'un dépôt sans activité pendant 60 jours ; ici, la collecte quotidienne crée cette activité.
