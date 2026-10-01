# Signal Matin

[![Tests](https://github.com/sosoj92/signal-matin/actions/workflows/tests.yml/badge.svg)](https://github.com/sosoj92/signal-matin/actions/workflows/tests.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-2f3437)](https://www.python.org/downloads/)
[![Licence MIT](https://img.shields.io/badge/licence-MIT-66705f)](LICENSE)

Un petit quotidien personnel A4, généré le matin pour remplacer le premier
scroll du téléphone. Il assemble uniquement les sources choisies, compose un
vrai journal monochrome et peut produire un PDF ou l'envoyer à l'imprimante.

![Aperçu de la une](docs/images/demo-page-1.png)

> **Pour essayer, aucune API, aucun compte et aucune imprimante ne sont
> nécessaires.** Le mode démo fonctionne avec des données fictives.

## Ce que Signal Matin peut contenir

- météo, agenda, priorités, tâches et rappels ;
- actualités générales avec brèves, articles développés et pages focus ;
- actualités IA / tech, flux RSS, veille et recommandations ;
- mot français, vocabulaire tech, quiz, calcul mental et mots croisés ;
- trois densités : `compact`, `standard` et `extended` ;
- pagination adaptative : si une rubrique est plus longue, une vraie page de
  suite est créée au lieu de couper le texte ou de tout rapetisser ;
- aperçu navigateur, PDF A4, impression facultative et recto verso ;
- édition liseuse EPUB reformatable et PDF e-ink à fort contraste ;
- lancement quotidien sous Windows, macOS ou Linux.

## Installation ultra simple — débutants

### 1. Récupérer le projet

La méthode sans Git :

1. clique sur le bouton vert **Code** en haut de cette page ;
2. choisis **Download ZIP** ;
3. décompresse le ZIP ;
4. ouvre le dossier `signal-matin` obtenu.

Ou, si Git est déjà installé :

```bash
git clone https://github.com/sosoj92/signal-matin.git
cd signal-matin
```

### 2. Installer Python

Installe [Python 3.11 ou plus récent](https://www.python.org/downloads/).

Sous Windows, coche **Add Python to PATH** dans la première fenêtre de
l'installateur. Pour vérifier :

```bash
python --version
```

Le résultat doit commencer par `Python 3.11`, `3.12`, `3.13` ou une version
plus récente. Sous Windows, si `python` n'est pas reconnu, essaie `py`.

### 3. Lancer l'installation guidée

Ouvre un terminal dans le dossier `signal-matin` :

- **Windows 11** : clique dans la barre d'adresse de l'Explorateur, écris
  `powershell`, puis appuie sur Entrée ;
- **macOS / Linux** : ouvre Terminal, écris `cd ` avec un espace, glisse le
  dossier dans la fenêtre, puis appuie sur Entrée.

Lance ensuite :

```bash
python scripts/setup.py
```

Sous Windows, tu peux utiliser ceci si nécessaire :

```powershell
py scripts/setup.py
```

Le programme :

1. crée un environnement Python isolé dans `.venv` ;
2. installe les dépendances ;
3. installe Chromium pour fabriquer les PDF ;
4. crée un `config.yaml` local de démonstration ;
5. vérifie l'installation ;
6. ouvre un vrai journal fictif dans le navigateur.

Il ne lance jamais d'impression pendant l'installation.

### 4. Vérifier ou réparer

```bash
# Windows
.\.venv\Scripts\python.exe scripts\doctor.py

# macOS / Linux
./.venv/bin/python scripts/doctor.py
```

Chaque ligne indique `OK`, `INFO` ou l'action exacte à effectuer.

## 🤝 Se faire aider par une IA (gratuitement)

**Pour INSTALLER, aucune connaissance technique n'est requise.** Ouvre la
version gratuite de [ChatGPT](https://chatgpt.com/),
[Claude](https://claude.ai/) ou [Gemini](https://gemini.google.com/), colle le
contenu de [INSTALL_WITH_AI.md](INSTALL_WITH_AI.md), puis laisse l'assistant te
guider une étape à la fois. Les offres gratuites ont des limites variables,
mais l'installation de démonstration est suffisamment courte pour ce type
d'accompagnement.

**Pour MODIFIER ou bidouiller le code**, plusieurs choix existent :

- **[Cline](https://docs.cline.bot/) + [Ollama](https://ollama.com/)** —
  assistant de code avec un modèle local, sans facturation d'API cloud ; il faut
  toutefois un ordinateur assez puissant pour le modèle choisi ;
- **[GitHub Copilot Free](https://docs.github.com/en/copilot/get-started/plans)**
  — palier gratuit et limité, disponible notamment dans VS Code ;
- **[Cursor Hobby](https://www.cursor.com/pricing)** — offre gratuite avec un
  volume d'utilisation limité ;
- **Codex ou Claude Code** — si tu y as déjà accès avec ton abonnement ou ton
  organisation.

Aucun outil n'est imposé : prends celui qui te convient. Ne colle jamais dans
un chatbot le contenu de `.env`, `config.yaml`, `credentials.json`, `token.json`
ou une URL de calendrier privée. Le guide explique où placer ces informations
localement sans les exposer dans la conversation.

## Installation manuelle — pour les personnes à l'aise avec un terminal

```bash
git clone https://github.com/sosoj92/signal-matin.git
cd signal-matin
python -m venv .venv
```

Active l'environnement avec `.\.venv\Scripts\Activate.ps1` sous Windows ou
`source .venv/bin/activate` sous macOS/Linux, puis lance :

```bash
pip install -e .
playwright install chromium
```

Enfin, copie la configuration d'exemple et ouvre la démo :

```powershell
# Windows PowerShell
Copy-Item config.example.yaml config.yaml
python main.py --preview --demo
```

```bash
# macOS / Linux
cp config.example.yaml config.yaml
python main.py --preview --demo
```

## Utilisation quotidienne

Les commandes ci-dessous supposent que l'environnement est activé. Pour
l'activer :

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Puis :

```bash
python main.py --preview   # ouvre l'aperçu HTML
python main.py --generate  # crée JSON + HTML + PDF
python main.py --print     # prépare l'impression, sans l'envoyer
```

La CLI installée propose les mêmes opérations :

```bash
signal-matin preview --demo
signal-matin generate --demo --mode standard
signal-matin ereader --demo --format both
signal-matin print --live --printer "Nom exact" --duplex --confirm
```

`print` n'envoie rien sans `--confirm`.

Les fichiers sont rangés par date :

```text
output/data/2026-09-26-signal-matin.json
output/preview/2026-09-26-signal-matin.html
output/pdf/2026-09-26-signal-matin.pdf
output/ereader/2026-09-26-signal-matin.epub
output/ereader/2026-09-26-signal-matin-eink.pdf
```

## Lire sur une liseuse sans imprimer

Le format recommandé est l'**EPUB** : le texte se réorganise selon l'écran et
la taille de police choisie sur la liseuse. Un **PDF e-ink** en ratio 3:4 est
également disponible pour les appareils qui préfèrent une mise en page fixe.

```bash
signal-matin ereader --demo                 # EPUB reformatable
signal-matin ereader --demo --format pdf    # PDF e-ink
signal-matin ereader --demo --format both   # génère les deux pour comparer
```

Le guide [Lire Signal Matin sur une liseuse](docs/liseuse.md) explique les
profils d'écran et trois modes de livraison : USB, **Send-to-PocketBook** lorsque
le firmware l'intègre, ou une **page privée sur le Wi-Fi local** lorsqu'il ne
l'intègre pas. Cette page peut renouveler l'EPUB chaque matin sur un ordinateur
allumé en permanence, sans exposer la configuration ni les clés API.

## ⚙️ Configuration

Toute la configuration tient dans un seul fichier local `config.yaml`, créée à
partir de [config.example.yaml](config.example.yaml). Ce fichier n'est jamais
versionné : chacun peut donc brancher ses propres sources sans les publier sur
GitHub.

| Intégration | Ce qu'il faut | Guide |
|---|---|---|
| Édition de démonstration | Rien | [Installation ultra simple](#installation-ultra-simple--débutants) |
| Météo Open-Meteo | Ville et coordonnées, aucune clé | [Météo](#météo-sans-clé-api) |
| Actualités et veille RSS | URLs de flux publics | [RSS et actualités](#flux-rss-et-actualités) |
| Agenda ICS | Fichier local ou URL privée | [Agenda ICS](#agenda-ics) |
| Google Calendar | Client OAuth local en lecture seule | [Google Calendar](#google-calendar) |
| Priorités et rappels | Quelques lignes YAML locales | [Priorités](#priorités-et-rappels) |
| Impression | Une imprimante configurée, facultative | [Impression](#impression) |
| Lancement quotidien | Planificateur Windows ou cron | [Automatisation](#automatiser-chaque-matin) |

### Activer ses vraies données

Ouvre `config.yaml` dans un éditeur de texte, remplace `demo: true` par
`demo: false`, puis active uniquement les modules souhaités :

```yaml
modules:
  weather: true
  calendar: true
  tasks: true
  news: true
  tech: true
  rss: true
  games: true
  tech_vocabulary: true
  recommendations: true
```

Tout est facultatif. Une source absente ou en panne ne bloque pas le reste du
journal. Signal Matin n'invente pas une actualité pour remplir un trou.

### Météo sans clé API

Open-Meteo fonctionne gratuitement et sans compte :

```yaml
weather:
  location: "Lyon"
  latitude: 45.7640
  longitude: 4.8357
```

### Flux RSS et actualités

```yaml
news:
  limit: 12
  max_age_hours: 72
  feeds:
    - name: "Nom du média"
      category: "Monde"
      url: "https://media.example/rss.xml"

tech:
  limit: 6
  feeds:
    - name: "Veille tech"
      category: "Tech"
      url: "https://tech.example/rss.xml"
```

Les titres, résumés, dates, URLs et médias restent associés à chaque article,
mais le journal imprimé ne montre pas les détails techniques du connecteur.

### Agenda ICS

Un fichier `.ics` local ou une URL ICS fonctionne :

```yaml
calendar:
  ics:
    - name: "Agenda personnel"
      source: "calendars/agenda.ics"
```

Les événements récurrents (réunion chaque mardi, anniversaires…) sont dépliés
pour le jour de l'édition, exceptions comprises.

Une URL ICS peut donner accès à ton agenda : ne la publie jamais.

### Google Calendar

Installe d'abord l'option Google :

```bash
pip install -e ".[google]"
```

Dans Google Cloud Console, crée un client OAuth de type **application de
bureau**, télécharge-le sous `credentials.json`, puis configure :

```yaml
calendar:
  google:
    enabled: true
    calendar_id: "primary"
    credentials_file: "credentials.json"
    token_file: "token.json"
```

Connecte ensuite le compte une seule fois :

```bash
signal-matin auth-google
```

L'accès est en lecture seule. Les fichiers OAuth sont ignorés par Git.

### Priorités et rappels

```yaml
tasks:
  priorities:
    - title: "Finaliser le dossier principal"
      importance: "high"
    - "Faire le point avant midi"
  reminders:
    - title: "Envoyer le compte rendu"
      due: "2026-09-26T16:00:00+02:00"
      context: "Travail"
```

Le fichier [config.example.yaml](config.example.yaml) documente toutes les
options avec des exemples génériques.

## ✏️ Personnaliser facilement

La plupart des personnalisations se font dans `config.yaml`, sans modifier le
code. Commence par dupliquer [config.example.yaml](config.example.yaml), puis
change seulement les valeurs dont tu as besoin.

| Je veux... | Je modifie... |
|---|---|
| Renommer le journal | `paper.title`, `paper.subtitle` et `paper.motto` |
| Afficher ou masquer une rubrique | les interrupteurs `true` / `false` de `modules` |
| Changer la ville de la météo | `weather.location`, `latitude` et `longitude` |
| Ajouter mes priorités | `tasks.priorities` et `tasks.reminders` |
| Ajouter une phrase personnelle | `personal.greeting`, `note`, `free_window` ou `quote` |
| Choisir mes médias | `news.feeds` et `tech.feeds` |
| Ajouter mes recommandations | `recommendations` |
| Faire une édition plus courte ou plus riche | l'option `--mode` de la commande |

### Changer le nom et la devise

```yaml
paper:
  title: "Le Petit Matin"
  subtitle: "Mon quotidien personnel"
  motto: "Commencer informé, continuer léger."
```

Le titre peut contenir un ou plusieurs mots. Le moteur adapte automatiquement
le masthead, les en-têtes et les pieds de page.

### Choisir ses rubriques

Passe une option à `false` pour retirer complètement la rubrique correspondante :

```yaml
modules:
  weather: true
  calendar: true
  tasks: true
  news: true
  tech: true
  rss: false
  games: true
  tech_vocabulary: true
  recommendations: false
```

Toutes les sources restent facultatives. Une rubrique vide ou désactivée ne
laisse pas un grand encadré blanc : la composition se rééquilibre et la
pagination s'adapte au contenu restant.

### Ajouter sa touche personnelle

```yaml
personal:
  greeting: "Bonjour, voici l'essentiel pour commencer la journée."
  note: "Garder une heure sans notifications ce matin."
  free_window: "14 h - 15 h 30"
  quote:
    text: "La clarté précède l'action."
    author: "Note personnelle"

recommendations:
  - title: "Relire le chapitre commencé hier"
    kind: "Lecture"
    reason: "Dix minutes suffisent pour reprendre le fil."
```

Ces textes restent dans le `config.yaml` local et ne sont jamais inclus dans le
dépôt Git.

### Choisir le format de l'édition

```bash
signal-matin preview --mode compact   # bref et rapide
signal-matin preview --mode standard  # équilibre
signal-matin preview --mode extended  # davantage de développements
signal-matin preview --mode auto      # Signal Matin choisit selon le contenu
```

Utilise toujours `preview` avant d'imprimer : tu peux modifier `config.yaml`,
relancer la commande et comparer immédiatement le résultat.

### Modifier les couleurs et les polices

Pour une personnalisation visuelle simple, les réglages principaux sont réunis
au début de [`web/signal_matin.css`](web/signal_matin.css) :

```css
:root {
  --ink: #151515;
  --paper: #fbfaf6;
  --display: Georgia, Cambria, "Times New Roman", serif;
  --serif: Cambria, Georgia, "Times New Roman", serif;
  --sans: Arial, "Helvetica Neue", sans-serif;
}
```

Garde un contraste fort pour l'impression et ne change pas les dimensions A4
si tu souhaites conserver la pagination automatique.

### Demander à une IA de le personnaliser

Tu peux aussi donner ce prompt à l'assistant de ton choix :

```text
Lis le README et config.example.yaml du projet Signal Matin. Aide-moi à
personnaliser uniquement mon fichier local config.yaml, une étape à la fois.
Commence par me demander le nom du journal, les rubriques souhaitées et mes
sources. Ne me demande jamais de coller une clé API, un token OAuth, une URL ICS
privée ou le contenu complet de config.yaml dans la conversation.
```

## Choisir le nombre et la densité des pages

```bash
signal-matin generate --demo --mode compact
signal-matin generate --demo --mode standard
signal-matin generate --demo --mode extended
```

| Mode | Pour quoi faire |
|---|---|
| `compact` | Brief rapide, peu de contenu, environ quatre pages. |
| `standard` | Édition quotidienne équilibrée. |
| `extended` | Plus de développements et de cahiers. |
| `auto` | Choix d'après la quantité de contenu. |

Le nombre final n'est pas rigide. Le moteur mesure les vraies pages dans
Chromium. Si un article, une liste ou une rubrique déborde, il crée une page de
suite, renumérote le journal et conserve un A4 lisible.

## Impression

Teste d'abord sans envoyer de papier :

```bash
signal-matin print --demo --printer "Nom exact"
```

Puis confirme explicitement :

```bash
signal-matin print --live --printer "Nom exact" --duplex --confirm
```

- Windows utilise le pilote sélectionné et un rendu plein A4 ;
- macOS et Linux utilisent CUPS (`lp`) ;
- aucune impression n'est lancée pendant l'installation ou les tests.

## Automatiser chaque matin

### Windows — Planificateur de tâches

Génération seule à 8 h :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_windows_task.ps1 -Time "08:00"
```

Impression recto verso :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_windows_task.ps1 `
  -Time "08:00" -Print -Duplex -Printer "Nom exact de l'imprimante"
```

Le script mémorise le Python de `.venv`, le dossier du projet et l'imprimante.
L'heure choisie est l'heure de **démarrage de la collecte** : avec beaucoup de
sources, le papier peut sortir quelques minutes plus tard.

Pour faire un essai dans une minute sans laisser Codex ou un terminal ouvert :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\programmer_impression_signal_matin.ps1 -DansMinutes 1
```

Ou pour la prochaine occurrence d'une heure précise :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\programmer_impression_signal_matin.ps1 -Heure "18:30"
```

Le test réutilise exactement l'action de la tâche quotidienne `Signal Matin`.
Il refuse de continuer si cette tâche a été installée sans l'option `-Print`.

### macOS / Linux — cron

Le script affiche la ligne à ajouter, sans modifier la crontab tout seul :

```bash
sh scripts/install_cron.sh 08:00 generate
sh scripts/install_cron.sh 08:00 print
```

## Architecture

```text
Sources facultatives
  RSS / Open-Meteo / ICS / Google Calendar / YAML
                    |
                    v
          Connectors / Adapters
                    |
                    v
       Normalisation Pydantic stricte
                    |
                    v
          MorningEdition JSON
                    |
                    v
          Règles éditoriales
                    |
                    v
       Renderer HTML/CSS autonome
                    |
                    v
      Playwright / Chromium -> PDF A4
                    |
                    v
          Impression facultative
```

Les données et le design restent séparés :

- `src/signal_matin/connectors/` lit les sources ;
- `models.py` définit le contrat JSON ;
- `pipeline.py` orchestre et hiérarchise ;
- `renderer.py` ne connaît aucune clé ni API ;
- `web/signal_matin.css` porte la direction artistique ;
- `signal_matin_pagination.js` crée les pages de suite si nécessaire ;
- `pdf.py` mesure chaque A4 avant l'export ;
- `printer.py` exige une confirmation explicite.

## Ajouter un connecteur

1. Ajoute un module dans `src/signal_matin/connectors/`.
2. Retourne des modèles normalisés et un `DataSourceStatus`.
3. Branche-le dans `pipeline.py`, jamais dans le renderer.
4. Ajoute un exemple générique dans `config.example.yaml`.
5. Écris un test avec des données fictives, sans appel réseau réel.

Un connecteur ne doit jamais écrire de secret dans le JSON ou les logs. Une
erreur ne doit dégrader que sa propre section.

## Personnaliser le design

La feuille `web/signal_matin.css` est conçue pour `@page { size: A4 }`. Conserve
les marges physiques et lance les tests de débordement après chaque changement :

```bash
signal-matin preview --demo --mode standard
pytest tests/test_renderer.py
```

## Tests et contribution

```bash
pip install -e ".[dev]"
playwright install chromium
pytest
```

La CI vérifie les modèles, les sections absentes, le HTML, les trois densités,
la pagination dynamique, les débordements et le format A4. Voir aussi
[CONTRIBUTING.md](CONTRIBUTING.md).

## Confidentialité

- `.env`, `config.yaml`, OAuth, calendriers et sorties sont ignorés par Git ;
- les URLs privées restent uniquement sur la machine de l'utilisateur ;
- aucune donnée personnelle n'est nécessaire pour le mode démo ;
- l'impression demande toujours une action volontaire ;
- ce dépôt est autonome et ne dépend d'aucun assistant personnel.

## Dépannage

**`python` n'est pas reconnu sous Windows**

Réinstalle Python en cochant **Add Python to PATH**, ou essaie
`py scripts/setup.py`.

**PowerShell refuse `Activate.ps1`**

Tu n'as pas besoin d'activer l'environnement : utilise directement
`.\.venv\Scripts\python.exe main.py --preview --demo`.

**Chromium est introuvable**

Lance `.\.venv\Scripts\python.exe -m playwright install chromium` sous Windows,
ou `./.venv/bin/python -m playwright install chromium` sous macOS/Linux.

**Une source ne s'affiche pas**

Vérifie qu'elle est activée dans `modules`, puis lance `python scripts/doctor.py`.
Les autres rubriques continueront de fonctionner.

**L'impression quotidienne ne part pas**

Ouvre le Planificateur de tâches et consulte l'historique de `Signal Matin`.
Réinstalle la tâche avec `-Print`, puis fais un essai avec `-DansMinutes 1`.

**Une page est plus longue que d'habitude**

C'est normal : le moteur ajoute une page de suite lorsque la quantité de texte
l'exige, au lieu de tronquer l'information.

## Licence

MIT. Voir [LICENSE](LICENSE).
