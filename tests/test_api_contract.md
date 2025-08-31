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
      "type_amende": "vitesse",
      "date_infraction": "15/01/2024",
      "lieu": "Avenue de la République, Caen",
      "numero_process_verbal": "14RD001234",
      "plaque": "AB-123-CD",
      "motif_contestation": "Feu rouge défaillant",
      "elements_preuve": "Photos du feu, témoins présents",
      "identite": {
        "nom": "Dupont",
        "prenom": "Jean",
        "adresse": "123 rue des Lilas, 14000 Caen"
      }
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
      "type_courrier_caf": "Réclamation RSA",
      "resume_courrier": "Suspension allocation suite courrier du 10/12/2024",
      "situation": "Demandeur RSA depuis 2 ans, situation inchangée"
    }
  }'
```
**Attendu**: Réponse JSON avec les 4 clés (resume, lettre, checklist, mentions)

### Test 5: Generate - tool_id "loyers"
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "loyers",
    "fields": {
      "adresse_complete": "15 rue des Martyrs, 75009 Paris",
      "surface_m2": 25,
      "nb_pieces": 1,
      "annee_construction": 1960,
      "meuble": false,
      "loyer_hc": 850,
      "charges": 120
    }
  }'
```
**Attendu**: Réponse JSON avec les 4 clés (resume, lettre, checklist, mentions)

### Test 6: Generate - tool_id "travail"
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "travail",
    "fields": {
      "situation": "licenciement abusif",
      "contrat": "CDI",
      "anciennete_mois": 24,
      "elements_preuve": "Emails de harcèlement, témoignages collègues",
      "identite": {
        "nom": "Martin",
        "prenom": "Sophie",
        "adresse": "45 avenue des Champs, 69000 Lyon"
      },
      "employeur": {
        "raison_sociale": "ENTREPRISE SAS",
        "adresse": "Zone industrielle, 69100 Villeurbanne"
      }
    }
  }'
```
**Attendu**: Réponse JSON avec les 4 clés (resume, lettre, checklist, mentions)

### Test 7: Generate - tool_id "sante"
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "sante",
    "fields": {
      "code_postal": "13001",
      "couverture": "ameli",
      "besoin": "medecin_traitant"
    }
  }'
```
**Attendu**: Réponse JSON avec les 4 clés (resume, lettre, checklist, mentions)

### Test 8: Generate - tool_id "energie"
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "energie",
    "fields": {
      "fournisseur": "EDF",
      "offre": "reglemente",
      "conso_kwh": 150,
      "montant_facture": 250,
      "date": "12/2024"
    }
  }'
```
**Attendu**: Réponse JSON avec les 4 clés (resume, lettre, checklist, mentions)

### Test 9: Generate - tool_id "aides"
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "aides",
    "fields": {
      "composition_foyer": "2 adultes, 1 enfant",
      "situation_pro": "chomage",
      "revenu_mensuel_net": 800,
      "logement": "locataire",
      "code_postal": "59000",
      "sante_couverture": "aucune"
    }
  }'
```
**Attendu**: Réponse JSON avec les 4 clés (resume, lettre, checklist, mentions)

### Test 10: Generate - tool_id "css"
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "css",
    "fields": {
      "revenu_mensuel_net": 950,
      "foyer": 2,
      "age": 45,
      "statut": "chomeur",
      "couverture_actuelle": "aucune"
    }
  }'
```
**Attendu**: Réponse JSON avec les 4 clés (resume, lettre, checklist, mentions)

### Test 11: Generate - tool_id "expulsions"
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "expulsions",
    "fields": {
      "situation": "menace expulsion pour impayés",
      "statut": "locataire",
      "dates": "Commandement du 15/11/2024",
      "preuves": "Difficultés financières temporaires, recherche emploi"
    }
  }'
```
**Attendu**: Réponse JSON avec les 4 clés (resume, lettre, checklist, mentions)

### Test 12: Generate - tool_id "ecole"
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "ecole",
    "fields": {
      "niveau": "college",
      "type": "harcelement",
      "faits": "Insultes répétées, isolation par groupe d élèves",
      "etablissement": "Collège Jean Moulin, Marseille",
      "parents_contacts": "Rendez-vous demandé, pas de réponse"
    }
  }'
```
**Attendu**: Réponse JSON avec les 4 clés (resume, lettre, checklist, mentions)

### Test 13: Generate - tool_id "usure"
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "usure",
    "fields": {
      "type_credit": "conso",
      "taux_annuel": 15.5,
      "assurance_emprunteur": 2.1,
      "frais": 150,
      "date_offre": "10/12/2024"
    }
  }'
```
**Attendu**: Réponse JSON avec les 4 clés (resume, lettre, checklist, mentions)

### Test 14: Generate - tool_id "decodeur"
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "decodeur",
    "fields": {
      "courrier_texte": "Suite à votre déclaration, un contrôle sera effectué. Vous devez fournir les justificatifs dans les 30 jours sous peine de redressement.",
      "expediteur": "Impots",
      "deadline_si_indiquee": "30 jours"
    }
  }'
```
**Attendu**: Réponse JSON avec les 4 clés (resume, lettre, checklist, mentions)

### Test 15: Error handling - tool_id invalide
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"tool_id": "invalid", "fields": {}}'
```
**Attendu**: HTTP 400 avec `{"detail": "tool_id inconnu"}`

## Structure de réponse attendue
Chaque appel à `/generate` doit retourner un JSON avec exactement ces 4 clés :
```json
{
  "resume": ["Étape 1...", "Étape 2..."],
  "lettre": {
    "destinataire_bloc": "Service\nAdresse\nVille",
    "objet": "Objet du courrier",
    "corps": "Corps de la lettre...",
    "pj": ["Pièce 1", "Pièce 2"],
    "signature": "Signature"
  },
  "checklist": ["Point 1", "Point 2"],
  "mentions": "Aide automatisée – ne remplace pas un conseil d'avocat."
}
```

## Notes
- Sans OPENAI_API_KEY, l'API utilise automatiquement le fallback mock
- Avec OPENAI_API_KEY configurée, l'API appelle OpenAI (gpt-4o-mini, temperature 0.2) avec retry et fallback en cas d'erreur
- La structure de réponse est toujours identique et conforme au contrat
- Tous les 12 outils sont supportés et testés ci-dessus