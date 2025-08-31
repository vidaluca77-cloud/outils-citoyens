from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(title="Outils Citoyens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
)

class GenIn(BaseModel):
    tool_id: str
    fields: dict

@app.get("/health")
def health(): return {"ok": True}

@app.post("/generate")
def generate(in_: GenIn):
    # Stub de sortie conforme (Copilot branchera OpenAI ensuite)
    allowed = ["amendes","aides","loyers","travail","sante","caf","usure","energie","expulsions","css","ecole","decodeur"]
    if in_.tool_id not in allowed:
        raise HTTPException(400, "tool_id inconnu")
    return {
        "resume": ["Étape 1 : Préparez vos pièces.", "Étape 2 : Envoyez en recommandé AR.", "Étape 3 : Suivez la réponse."],
        "lettre": {
            "destinataire_bloc": "Service compétent\nAdresse\nCP Ville",
            "objet": f"{in_.tool_id.upper()} — demande/contestation",
            "corps": "Madame, Monsieur,\n\nJe vous adresse ce courrier concernant la situation décrite...",
            "pj": ["Copie du document", "Justificatif d'identité"],
            "signature": "Nom Prénom\nAdresse\nDate"
        },
        "checklist": ["Délai indicatif 30–45 jours", "Conserver une copie signée", "Joindre toutes les pièces"],
        "mentions": "Aide automatisée – ne remplace pas un conseil d’avocat."
    }
