# Outils Citoyens — Scaffold final (12 outils)

Ce dépôt est minimal mais **contractuel** : Copilot peut développer le reste en suivant ces règles.

## Architecture
- `web/` : Next.js 14 (App Router). Pages : `/` (grille) et `/outil/[id]` (formulaire dynamique).
- `api/` : FastAPI, endpoints `GET /health` et `POST /generate`.
- `schemas/` : **12 JSON Schema** (source de vérité des formulaires).
- `api/system_lumiere.txt` : prompt système de l’assistant.
- `api/templates.json` : prompts par outil (Copilot doit enrichir).
- `tests/` : checklists d’acceptation.
- `.github/` : rappel des tâches.

## Contrat API
`POST /generate` reçoit : 
```json
{ "tool_id": "amendes", "fields": { "...": "..." } }
```
et retourne **obligatoirement** :
```json
{
  "resume": ["Étape 1 …"],
  "lettre": {
    "destinataire_bloc": "…",
    "objet": "…",
    "corps": "…",
    "pj": ["…"],
    "signature": "…"
  },
  "checklist": ["…"],
  "mentions": "Aide automatisée – ne remplace pas un conseil d’avocat."
}
```

## Tâches Copilot
1. Implémenter l’API d’après `api/openapi.yaml`. Utiliser OpenAI (clé `OPENAI_API_KEY`) avec fallback **mock** si absente.
2. Générer les formulaires Next.js **depuis les JSON Schema** (sans coder 12 pages à la main).
3. Afficher la réponse (`resume`, `lettre`, `checklist`, `mentions`) et proposer un export `.txt` (PDF ensuite).
4. Déploiement : web (Netlify/Vercel), api (Render/Fly). Variables : `NEXT_PUBLIC_API_BASE`, `OPENAI_API_KEY`.
5. Sécurité : pas de stockage de données, CORS restreint au domaine du front.

## Critères d’acceptation
- `GET /health` → `{ "ok": true }`
- `/outil/amendes` → formulaire auto, envoi à `/generate`, rendu des 4 blocs.
- Les 12 outils sont accessibles via `/outil/[id]` avec leurs schémas.
