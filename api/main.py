from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import time
import openai
from openai import OpenAI
from typing import Dict, Any

app = FastAPI(title="Outils Citoyens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
)

# OpenAI setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Load system prompt and templates
def load_system_prompt():
    try:
        with open("system_lumiere.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "SYSTEM PROMPT – Lumière citoyenne : assistant civique FR, clair, bienveillant, non avocat. Sortie JSON {resume[], lettre{}, checklist[], mentions}."

def load_templates():
    try:
        with open("templates.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "amendes": "Contexte: contestation d'amende. Données: {fields}",
            "caf": "Contexte: réponse à un courrier CAF. Données: {fields}"
        }

SYSTEM_PROMPT = load_system_prompt()
TEMPLATES = load_templates()

def get_mock_response(tool_id: str) -> Dict[str, Any]:
    """Fallback mock response when OpenAI is unavailable"""
    return {
        "resume": ["Étape 1 : Préparez vos pièces.", "Étape 2 : Envoyez en recommandé AR.", "Étape 3 : Suivez la réponse."],
        "lettre": {
            "destinataire_bloc": "Service compétent\nAdresse\nCP Ville",
            "objet": f"{tool_id.upper()} — demande/contestation",
            "corps": "Madame, Monsieur,\n\nJe vous adresse ce courrier concernant la situation décrite...",
            "pj": ["Copie du document", "Justificatif d'identité"],
            "signature": "Nom Prénom\nAdresse\nDate"
        },
        "checklist": ["Délai indicatif 30–45 jours", "Conserver une copie signée", "Joindre toutes les pièces"],
        "mentions": "Aide automatisée – ne remplace pas un conseil d'avocat."
    }

def validate_and_fix_response(response_data: Dict[str, Any], tool_id: str) -> Dict[str, Any]:
    """Validate response has required keys and fix if needed"""
    required_keys = ["resume", "lettre", "checklist", "mentions"]
    
    # Check if all required keys exist
    for key in required_keys:
        if key not in response_data:
            return get_mock_response(tool_id)
    
    # Check lettre structure
    if not isinstance(response_data.get("lettre"), dict):
        return get_mock_response(tool_id)
    
    lettre_keys = ["destinataire_bloc", "objet", "corps", "pj", "signature"]
    for key in lettre_keys:
        if key not in response_data["lettre"]:
            return get_mock_response(tool_id)
    
    # Ensure arrays are arrays
    if not isinstance(response_data.get("resume"), list):
        response_data["resume"] = ["Étape 1 : Préparez vos pièces."]
    if not isinstance(response_data.get("checklist"), list):
        response_data["checklist"] = ["Délai indicatif 30–45 jours"]
    if not isinstance(response_data["lettre"].get("pj"), list):
        response_data["lettre"]["pj"] = ["Copie du document"]
    
    return response_data

def call_openai_with_retry(system_prompt: str, user_prompt: str, max_retries: int = 3) -> Dict[str, Any]:
    """Call OpenAI with exponential backoff retry logic"""
    if not openai_client:
        raise Exception("OpenAI client not available")
    
    for attempt in range(max_retries):
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo-1106",  # Model that supports JSON mode
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000,
                timeout=30
            )
            
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try repair with explicit prompt
                repair_prompt = f"Réparez ce JSON en format valide avec les clés resume[], lettre{{}}, checklist[], mentions: {content}"
                repair_response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo-1106",
                    messages=[
                        {"role": "system", "content": "Vous êtes un réparateur de JSON. Retournez uniquement du JSON valide."},
                        {"role": "user", "content": repair_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=2000,
                    timeout=30
                )
                return json.loads(repair_response.choices[0].message.content)
                
        except openai.RateLimitError:
            # 429 - Rate limit
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + (attempt * 0.1)  # Exponential backoff
                time.sleep(wait_time)
                continue
            raise
        except (openai.APITimeoutError, openai.InternalServerError, openai.APIError) as e:
            # Timeout, 5xx errors
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + (attempt * 0.1)  # Exponential backoff
                time.sleep(wait_time)
                continue
            raise
        except Exception as e:
            # Any other error
            raise
    
    raise Exception("Max retries exceeded")

class GenIn(BaseModel):
    tool_id: str
    fields: dict

@app.get("/health")
def health(): return {"ok": True}

@app.post("/generate")
def generate(in_: GenIn):
    # Validate tool_id
    allowed = ["amendes","aides","loyers","travail","sante","caf","usure","energie","expulsions","css","ecole","decodeur"]
    if in_.tool_id not in allowed:
        raise HTTPException(400, "tool_id inconnu")
    
    # Try OpenAI integration first, fallback to mock on any error
    if openai_client and in_.tool_id in TEMPLATES:
        try:
            # Build user prompt from template
            template = TEMPLATES[in_.tool_id]
            user_prompt = template.format(fields=json.dumps(in_.fields, ensure_ascii=False))
            
            # Add explicit JSON structure requirements to system prompt
            enhanced_system_prompt = f"""{SYSTEM_PROMPT}

Tu dois OBLIGATOIREMENT répondre avec un JSON valide contenant exactement ces 4 clés:
- "resume": array de strings (étapes à suivre)
- "lettre": objet avec les clés "destinataire_bloc", "objet", "corps", "pj" (array), "signature"
- "checklist": array de strings (conseils pratiques)
- "mentions": string (avertissement légal)

Exemple de structure attendue:
{{
  "resume": ["Étape 1...", "Étape 2..."],
  "lettre": {{
    "destinataire_bloc": "Service\\nAdresse\\nVille",
    "objet": "Objet du courrier",
    "corps": "Corps de la lettre...",
    "pj": ["Pièce 1", "Pièce 2"],
    "signature": "Signature"
  }},
  "checklist": ["Point 1", "Point 2"],
  "mentions": "Aide automatisée – ne remplace pas un conseil d'avocat."
}}"""
            
            # Call OpenAI with retry logic
            response_data = call_openai_with_retry(enhanced_system_prompt, user_prompt)
            
            # Validate and fix response
            validated_response = validate_and_fix_response(response_data, in_.tool_id)
            return validated_response
            
        except Exception as e:
            # Log error in production you might want to log this
            pass
    
    # Fallback to mock response
    return get_mock_response(in_.tool_id)