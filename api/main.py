from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import time
import openai
from openai import OpenAI
from typing import Dict, Any, List
import logging

app = FastAPI(title="Outils Citoyens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for structured output
class Lettre(BaseModel):
    destinataire_bloc: str
    objet: str
    corps: str
    pj: List[str]
    signature: str

class Output(BaseModel):
    resume: List[str]
    lettre: Lettre
    checklist: List[str]
    mentions: str

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
    """Enhanced fallback mock response when OpenAI is unavailable"""
    
    # Tool-specific mock responses that follow the new standards
    mock_responses = {
        "amendes": {
            "resume": [
                "Rassembler les preuves de l'erreur de verbalisation",
                "Rédiger une contestation argumentée en LRAR",
                "Envoyer dans les 45 jours à l'OMP",
                "Conserver une copie et l'accusé de réception",
                "Attendre la réponse sous 3 mois maximum"
            ],
            "lettre": {
                "destinataire_bloc": "Monsieur l'Officier du Ministère Public\nTribunal de Police\n[Code postal] [Ville]",
                "objet": "Contestation PV - Stationnement",
                "corps": "Monsieur l'Officier,\n\nJe conteste formellement le procès-verbal dressé.\n\nMotifs de contestation :\n[Détailler les arguments selon les éléments fournis]\n\nJe vous prie d'annuler cette contravention et vous adresse mes salutations respectueuses.",
                "pj": ["Copie du PV", "Photos du lieu", "Justificatif d'identité"],
                "signature": "[Nom Prénom]\n[Adresse complète]\nLe [Date]"
            },
            "checklist": [
                "Envoyer en LRAR dans les 45 jours",
                "Conserver l'original du PV",
                "Prendre des photos du lieu si pertinent",
                "Vérifier l'exactitude des mentions du PV"
            ],
            "mentions": "Aide automatisée – ne remplace pas un conseil d'avocat. Respecter impérativement le délai de 45 jours."
        },
        "travail": {
            "resume": [
                "Rassembler les preuves des heures supplémentaires",
                "Calculer le montant exact des sommes dues",
                "Adresser une mise en demeure à l'employeur",
                "Saisir le conseil de prud'hommes si échec",
                "Conserver toutes les pièces justificatives"
            ],
            "lettre": {
                "destinataire_bloc": "Service Ressources Humaines\n[Adresse de l'entreprise]",
                "objet": "Demande de paiement - Heures supplémentaires",
                "corps": "Monsieur le Directeur,\n\nJe vous informe que des heures supplémentaires effectuées n'ont pas été rémunérées conformément au Code du travail.\n\n[Détail des heures et calcul]\n\nJe vous demande le règlement sous 30 jours.",
                "pj": ["Planning de travail", "Relevés d'heures", "Contrat de travail", "Convention collective"],
                "signature": "[Nom Prénom]\n[Adresse]\nLe [Date]"
            },
            "checklist": [
                "Rassembler tous les justificatifs d'heures",
                "Vérifier les taux majorés applicables",
                "Envoyer la demande en LRAR",
                "Respecter le délai de prescription de 3 ans"
            ],
            "mentions": "Aide automatisée – ne remplace pas un conseil d'avocat. Respecter les délais de prescription et de saisine prud'homale."
        },
        "loyers": {
            "resume": [
                "Vérifier l'encadrement des loyers dans la zone",
                "Calculer l'éventuel dépassement du loyer de référence",
                "Adresser une mise en demeure au bailleur",
                "Saisir la commission de conciliation si échec",
                "Engager une action devant le tribunal si nécessaire"
            ],
            "lettre": {
                "destinataire_bloc": "Monsieur/Madame [Nom du bailleur]\n[Adresse du bailleur]",
                "objet": "Contestation du montant du loyer - Logement",
                "corps": "Monsieur/Madame,\n\nJe vous informe que le loyer pratiqué semble dépasser les plafonds légaux.\n\n[Détail du calcul et de la contestation]\n\nJe vous demande de bien vouloir régulariser cette situation.",
                "pj": ["Bail de location", "Quittances de loyer", "Données loyers de référence"],
                "signature": "[Nom Prénom]\n[Adresse]\nLe [Date]"
            },
            "checklist": [
                "Consulter les loyers de référence en mairie",
                "Calculer précisément le dépassement",
                "Envoyer en LRAR la contestation",
                "Conserver tous les justificatifs"
            ],
            "mentions": "Aide automatisée – ne remplace pas un conseil d'avocat. Vérifier l'applicabilité de l'encadrement dans votre commune."
        }
    }
    
    # Return tool-specific mock or generic fallback
    if tool_id in mock_responses:
        return mock_responses[tool_id]
    
    # Generic fallback for other tools
    return {
        "resume": [
            "Analyser votre situation juridique",
            "Rassembler les documents nécessaires", 
            "Rédiger un courrier approprié",
            "Envoyer en recommandé avec AR",
            "Suivre les délais de réponse"
        ],
        "lettre": {
            "destinataire_bloc": "Service compétent\nAdresse\nCP Ville",
            "objet": f"{tool_id.upper()} — demande/contestation",
            "corps": "Madame, Monsieur,\n\nJe vous adresse ce courrier concernant la situation décrite dans vos services.\n\n[Exposé des faits et demande]\n\nJe vous prie d'agréer mes salutations respectueuses.",
            "pj": ["Copie du document", "Justificatif d'identité"],
            "signature": "[Nom Prénom]\n[Adresse complète]\nLe [Date]"
        },
        "checklist": [
            "Conserver une copie signée de tous documents",
            "Respecter les délais légaux indiqués", 
            "Joindre toutes les pièces justificatives",
            "Suivre l'accusé de réception"
        ],
        "mentions": "Aide automatisée – ne remplace pas un conseil d'avocat. Vérifier les délais légaux applicables à votre situation."
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

def call_openai_with_retry(system_prompt: str, user_prompt: str, max_retries: int = 3, is_repair: bool = False) -> Dict[str, Any]:
    """Call OpenAI with exponential backoff retry logic"""
    if not openai_client:
        raise Exception("OpenAI client not available")
    
    # Use gpt-4o for main generation, gpt-4o-mini for repair
    model = "gpt-4o-mini" if is_repair else "gpt-4o"
    max_tokens = 1200
    timeout = 20  # 15-20s per pass as specified
    
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=max_tokens,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            logger.info(f"OpenAI call successful - model: {model}, duration: {duration:.2f}s, attempt: {attempt + 1}")
            
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                if is_repair:
                    # If repair also fails, raise exception
                    raise Exception("Repair attempt failed - invalid JSON")
                
                # Try repair with explicit prompt
                logger.warning(f"JSON decode error, attempting repair")
                repair_prompt = f"Réparez ce JSON en format valide avec les clés resume[], lettre{{}}, checklist[], mentions: {content}"
                return call_openai_with_retry(
                    "Vous êtes un réparateur de JSON. Retournez uniquement du JSON valide.",
                    repair_prompt,
                    max_retries=2,
                    is_repair=True
                )
                
        except openai.RateLimitError:
            # 429 - Rate limit
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + (attempt * 0.1)  # Exponential backoff
                logger.warning(f"Rate limit hit, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                continue
            logger.error("Max retries exceeded due to rate limiting")
            raise
        except (openai.APITimeoutError, openai.InternalServerError, openai.APIError) as e:
            # Timeout, 5xx errors
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + (attempt * 0.1)  # Exponential backoff
                logger.warning(f"API error: {type(e).__name__}, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                continue
            logger.error(f"Max retries exceeded due to API errors: {e}")
            raise
        except Exception as e:
            # Any other error
            logger.error(f"Unexpected error in OpenAI call: {e}")
            raise
    
    raise Exception("Max retries exceeded")

def generate_with_two_passes(system_prompt: str, user_prompt: str, tool_id: str) -> Dict[str, Any]:
    """Generate response with two-pass auto-critique system"""
    start_time = time.time()
    
    try:
        # Pass 1: Initial generation
        logger.info(f"Pass 1 - Initial generation for tool: {tool_id}")
        pass1_response = call_openai_with_retry(system_prompt, user_prompt)
        
        # Validate Pass 1 response structure
        validated_pass1 = validate_and_fix_response(pass1_response, tool_id)
        
        # Pass 2: Auto-critique and improvement
        logger.info(f"Pass 2 - Auto-critique for tool: {tool_id}")
        critique_prompt = f"""Voici le JSON généré en première passe :

{json.dumps(validated_pass1, ensure_ascii=False, indent=2)}

Vérifie la structure, le ton et la clarté. Si des champs sont trop vagues, remplace par des formulations neutres et ajoute dans checklist l'action pour compléter. 

Assure-toi que :
- resume contient 4-8 puces concrètes et utiles
- checklist utilise des verbes à l'infinitif et des actions claires  
- mentions contient 2-4 rappels prudents
- lettre a un ton administratif approprié et des informations précises

Réponds en JSON strict identique avec ces améliorations."""

        pass2_response = call_openai_with_retry(system_prompt, critique_prompt)
        
        # Final validation
        final_response = validate_and_fix_response(pass2_response, tool_id)
        
        duration = time.time() - start_time
        logger.info(f"Two-pass generation completed - tool: {tool_id}, total duration: {duration:.2f}s")
        
        return final_response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Two-pass generation failed - tool: {tool_id}, duration: {duration:.2f}s, error: {e}")
        # Fallback to mock response after max attempts
        return get_mock_response(tool_id)

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
    
    # Try OpenAI integration with two-pass system, fallback to mock on any error
    if openai_client and in_.tool_id in TEMPLATES:
        try:
            # Build user prompt from template
            template = TEMPLATES[in_.tool_id]
            user_prompt = template.format(fields=json.dumps(in_.fields, ensure_ascii=False))
            
            # Enhanced system prompt with strict JSON requirements
            enhanced_system_prompt = f"""{SYSTEM_PROMPT}

Tu dois OBLIGATOIREMENT répondre avec un JSON valide contenant exactement ces 4 clés:
- "resume": array de 4-8 strings concrètes (étapes à suivre)
- "lettre": objet avec les clés "destinataire_bloc", "objet", "corps", "pj" (array), "signature"
- "checklist": array de strings (actions claires, verbes à l'infinitif)
- "mentions": string (2-4 rappels prudents)

Exemple de structure attendue:
{{
  "resume": ["Étape 1...", "Étape 2...", "Étape 3...", "Étape 4..."],
  "lettre": {{
    "destinataire_bloc": "Service\\nAdresse\\nVille",
    "objet": "Objet du courrier",
    "corps": "Corps de la lettre en français administratif...",
    "pj": ["Pièce 1", "Pièce 2"],
    "signature": "Signature avec nom, adresse, date"
  }},
  "checklist": ["Vérifier...", "Conserver...", "Respecter le délai de..."],
  "mentions": "Aide automatisée – ne remplace pas un conseil d'avocat. Délais légaux à respecter."
}}"""
            
            # Use two-pass generation system
            return generate_with_two_passes(enhanced_system_prompt, user_prompt, in_.tool_id)
            
        except Exception as e:
            logger.error(f"Generation failed for tool {in_.tool_id}: {e}")
    
    # Fallback to mock response
    logger.info(f"Using mock response for tool: {in_.tool_id}")
    return get_mock_response(in_.tool_id)