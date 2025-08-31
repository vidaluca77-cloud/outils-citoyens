# Test API Contract

## Démarrage
- Démarrer l'API: `uvicorn api.main:app --reload --port 8000`

## Tests manuels

### Test 1: Health check
```bash
curl -X GET http://127.0.0.1:8000/health
# Attendu: {"ok": true}
```

### Test 2: Documentation OpenAPI
- Naviguer vers: http://127.0.0.1:8000/docs
- Attendu: Interface Swagger UI accessible

### Test 3: Generate - tool_id "amendes"
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "amendes",
    "fields": {
      "montant": "90",
      "date": "2024-01-15",
      "numero": "12345",
      "motif": "Excès de vitesse",
      "nom": "Dupont",
      "prenom": "Jean"
    }
  }'
```
**Attendu**: Réponse JSON avec les 4 clés (resume, lettre, checklist, mentions)

### Test 4: Generate - tool_id "caf"
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "caf",
    "fields": {
      "type_courrier": "Réclamation RSA",
      "numero_allocataire": "123456",
      "nom": "Martin",
      "prenom": "Marie",
      "adresse": "123 rue Example, 75001 Paris"
    }
  }'
```
**Attendu**: Réponse JSON avec les 4 clés (resume, lettre, checklist, mentions)

### Test 5: Error handling - tool_id invalide
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"tool_id": "invalid", "fields": {}}'
```
**Attendu**: HTTP 400 avec `{"detail": "tool_id inconnu"}`

## Notes
- Sans OPENAI_API_KEY, l'API utilise automatiquement le fallback mock
- Avec OPENAI_API_KEY configurée, l'API appelle OpenAI avec retry et fallback en cas d'erreur
- La structure de réponse est toujours identique et conforme au contrat