# Lire Signal Matin sur une liseuse

Signal Matin peut produire une édition numérique conçue pour les écrans e-ink.
Cela évite l'impression tout en conservant une lecture calme, hors des réseaux
sociaux et des notifications du téléphone.

## Quel format choisir ?

### EPUB — recommandé

L'EPUB est reformatable : la liseuse adapte les lignes à son écran et permet de
changer la police, la taille du texte, les marges et l'interligne. Le sommaire
donne un accès direct à la une, la journée, l'actualité, la tech, la veille et
les jeux.

```powershell
signal-matin ereader --demo
```

Le fichier est créé dans :

```text
output/ereader/AAAA-MM-JJ-signal-matin.epub
```

### PDF e-ink — mise en page stable

Le PDF e-ink utilise un ratio 3:4, une seule colonne, une police plus grande et
un contraste élevé. Il est utile lorsqu'une liseuse gère mal l'EPUB ou lorsqu'on
souhaite conserver exactement la même composition.

```powershell
signal-matin ereader --demo --format pdf
```

Trois tailles sont disponibles :

```powershell
signal-matin ereader --demo --format pdf --screen small
signal-matin ereader --demo --format pdf --screen medium
signal-matin ereader --demo --format pdf --screen large
```

Le profil `medium` est le choix générique. L'EPUB n'a pas besoin de profil : il
s'adapte directement à la liseuse.

Pour comparer les deux sorties :

```powershell
signal-matin ereader --demo --format both
```

## Recevoir le journal sans câble

Deux méthodes sont possibles. Elles ne demandent aucune modification du
firmware de la liseuse.

### Option A — Send-to-PocketBook, s'il est intégré

`Send-to-PocketBook` n'est pas une application à télécharger : c'est un service
présent dans certains firmwares PocketBook. Ouvre **Paramètres > Comptes et
synchronisation** sur la liseuse. Si le service apparaît :

1. active-le et confirme l'adresse proposée par PocketBook ;
2. autorise l'adresse d'expédition souhaitée ;
3. envoie l'EPUB du jour en pièce jointe depuis cette adresse ;
4. synchronise la bibliothèque de la liseuse.

Certains appareils vendus sous une autre marque utilisent le matériel
PocketBook mais un firmware qui ne contient pas ce service. S'il n'apparaît pas
dans les réglages, il ne peut pas être ajouté comme une application ordinaire.
Il est déconseillé de remplacer le firmware uniquement pour cette fonction :
cela peut supprimer les services du revendeur, compromettre la garantie ou
rendre la liseuse inutilisable.

Références utiles :

- [manuel et assistance PocketBook](https://support.pocketbook-int.com/) ;
- [transfert de livres externes chez Vivlio](https://shop.vivlio.com/content/liseuse-transfert).

### Option B — page privée sur le Wi-Fi local

Cette option fonctionne sans compte externe. L'ordinateur qui fait tourner
Signal Matin publie uniquement les EPUB/PDF générés dans une page très légère.
`config.yaml`, les clés et les sources ne sont jamais servis.

Test manuel :

```powershell
signal-matin serve --live --host 0.0.0.0 --port 8844 --refresh-at 08:00
```

La commande affiche une adresse locale courte et un code temporaire à six
chiffres. Depuis la liseuse connectée au **même Wi-Fi** :

1. ouvre le navigateur ;
2. recopie seulement l'adresse courte affichée par Signal Matin ;
3. saisis une fois le code à six chiffres ;
4. après l'association, enregistre cette page dans les favoris ;
5. touche **Télécharger l'EPUB** chaque matin.

Le code expire après une heure et disparaît dès sa première utilisation. La
liseuse conserve ensuite localement un cookie d'accès pendant un an. Il n'est
donc plus nécessaire de recopier le long jeton privé. Pour associer un nouvel
appareil, relance `--show-url-only` afin de créer un nouveau code temporaire.

L'édition est créée au démarrage si celle du jour manque, puis actualisée à
l'heure choisie. La liseuse n'a pas besoin d'être branchée en USB. En revanche,
la plupart des liseuses ne permettent pas à une page web de télécharger un
fichier toute seule en arrière-plan : il reste normalement un toucher sur le
favori, puis sur le bouton de téléchargement.

Si un autre outil produit déjà une édition normalisée Signal Matin, la page peut
la reprendre sans dupliquer ses connecteurs ni ses secrets :

```powershell
signal-matin serve --host 0.0.0.0 --input-dir "D:\journaux\data"
```

Le serveur attend dans ce dossier un fichier nommé
`AAAA-MM-JJ-signal-matin.json`. Tant qu'il n'est pas disponible, il conserve
l'édition précédente et réessaie automatiquement. Cette passerelle reste
facultative : l'installation autonome normale utilise directement `--live`.

Pour publier aussi un PDF e-ink :

```powershell
signal-matin serve --live --host 0.0.0.0 --format both
```

Pour afficher à nouveau le favori sans démarrer un second serveur :

```powershell
signal-matin serve --host 0.0.0.0 --show-url-only
```

#### Démarrage automatique sous Windows

Après un premier test manuel réussi :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_ereader_server_task.ps1 `
  -Time "08:00"
```

Le serveur démarre à l'ouverture de session Windows et renouvelle l'édition
chaque jour à 8 h. Il conserve le même favori privé après les redémarrages.

Si Windows bloque l'accès depuis la liseuse, ouvre PowerShell **en tant
qu'administrateur** et relance explicitement avec :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_ereader_server_task.ps1 `
  -Time "08:00" -OpenFirewall
```

La règle créée accepte uniquement le port choisi sur les réseaux Windows de
profil **Privé**.

### Règles de sécurité

- ne publie jamais le jeton historique, le code d'association ou les fichiers
  personnels sur un forum ou dans le dépôt Git ;
- utilise cette fonction uniquement sur un Wi-Fi de confiance ;
- n'ouvre jamais ce port sur la box et ne crée pas de redirection Internet ;
- les fichiers de sortie, le jeton `.access-token` et le code temporaire sont
  ignorés par Git ;
- pour révoquer le favori, arrête le serveur, supprime localement
  `output/ereader/.access-token`, puis redémarre-le.

## Transférer le journal par USB

La méthode universelle reste disponible :

1. générer d'abord l'EPUB et le PDF e-ink ;
2. connecter la liseuse en USB ;
3. placer le fichier dans le dossier de livres ou de documents indiqué par le
   fabricant ;
4. éjecter proprement l'appareil ;
5. vérifier le sommaire, la taille des caractères et les changements de page.

Ne pas automatiser la copie vers un appareil avant d'avoir validé manuellement
le bon dossier et le bon format sur ce modèle précis.

## Utiliser ses vraies données

Retire `--demo` lorsque `config.yaml` est prêt :

```powershell
signal-matin ereader --live --format epub
```

Les règles de confidentialité restent identiques : l'édition générée est un
fichier personnel et ne doit pas être ajoutée au dépôt Git.
