# Installer Signal Matin avec l'aide d'une IA

Ce guide s'adresse aux personnes qui ne sont pas à l'aise avec un terminal. Il
ne remplace pas le programme d'installation guidée : il donne à une IA le bon
contexte pour vous accompagner sans lui transmettre de secret.

## La voie la plus simple

Après avoir téléchargé ou cloné le dépôt, ouvrez un terminal dans son dossier et
lancez :

```bash
python scripts/setup.py
```

Le script crée un environnement isolé, installe les dépendances et ouvre une
édition fictive. Aucune clé API et aucune imprimante ne sont nécessaires.

Sous Windows, extrayez d'abord le ZIP et placez le dossier hors de OneDrive (par
exemple `C:\Users\<votre nom>\signal-matin`). En cas de `[WinError 5] Accès
refusé`, suivez la section dédiée du README : le script affiche aussi les
causes probables et il suffit ensuite de le relancer.

## Prompt à copier dans votre IA

Copiez le texte ci-dessous dans l'assistant de votre choix :

```text
Je veux installer le projet open source Signal Matin depuis
https://github.com/sosoj92/signal-matin.

Accompagne-moi comme une personne débutante, une seule étape à la fois. Commence
par identifier mon système (Windows, macOS ou Linux), vérifier Python 3.11+, puis
faire cloner ou télécharger le dépôt. Utilise d'abord le programme officiel
`python scripts/setup.py`. Si une commande échoue, explique le message en mots
simples et donne seulement la prochaine commande nécessaire. Sous Windows, en
cas de « [WinError 5] Accès refusé », suis la section dédiée du README (pas de
terminal administrateur, dossier hors OneDrive, autres fenêtres fermées).

Objectif initial : ouvrir l'édition de démonstration, sans aucune API et sans
impression. Ensuite, fais exécuter `python scripts/doctor.py`, puis aide-moi à
activer uniquement les sources que je choisis dans config.yaml.

Règles importantes :
- ne me demande jamais de coller une clé API, un token OAuth ou une URL de
  calendrier privée dans le chat ; indique-moi seulement dans quel fichier local
  la placer ;
- ne publie et ne committe jamais config.yaml, .env, credentials.json,
  token.json, un calendrier ICS ou le dossier output ;
- ne lance jamais une impression sans me demander une confirmation explicite ;
- ne modifie pas le code tant que l'installation normale n'a pas été testée.
```

## Ce que l'IA peut vous demander

- la version affichée par `python --version` ;
- votre système d'exploitation ;
- le message d'erreur exact, sans vos clés ni tokens ;
- les rubriques que vous voulez activer ;
- le nom de votre imprimante, uniquement si vous souhaitez imprimer.

## Ce que vous ne devez jamais envoyer

Ne partagez pas le contenu de `.env`, `config.yaml`, `credentials.json`,
`token.json`, une URL ICS privée ou une clé d'API. Ces fichiers sont ignorés par
Git, mais ils restent vos données personnelles.
