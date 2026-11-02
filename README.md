# Blog de La Pépinière des Élites

Publié sur https://blog.pepinieredeselites.org (GitHub Pages).

## Publier un article

1. Ajoute un fichier dans `articles/`, nommé `AAAA-MM-JJ-titre-court.md` (copie un article existant comme modèle).
2. Remplis l'en-tête : titre, date, format, rubrique, chantier, auteur, chapo.
3. `statut: brouillon` cache l'article ; retire la ligne pour le publier.
4. Enregistre (commit) sur la branche `main` : le site se met à jour tout seul en 1 à 2 minutes.

On peut tout faire depuis github.com : bouton **Add file > Create new file** dans le dossier `articles/`.

## En local

```
pip install markdown pyyaml
python3 build.py --subdomain --drafts   # aperçu dans dist/blog/
```
