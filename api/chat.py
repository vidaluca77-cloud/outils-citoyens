from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import os
import logging
from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)

# OpenAI setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

router = APIRouter()

# Pydantic models
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    tool_id: Optional[str] = None
    messages: List[ChatMessage]
    current_form_values: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    answer: str
    suggested_fields: Optional[Dict[str, Any]] = None

# System prompt for chat assistant
CHAT_SYSTEM_PROMPT = """Tu es un assistant juridique français expert et bienveillant, spécialisé en démarches administratives citoyennes. Tu aides les citoyens français à comprendre leurs droits et à réaliser leurs démarches.

Tes rôles principaux :
1. Écouter et comprendre la situation de l'utilisateur
2. Poser des questions de précision pour bien cerner ses besoins
3. Donner des conseils juridiques accessibles et bienveillants
4. Orienter vers les bons outils et démarches
5. Aider à remplir les formulaires en expliquant chaque champ

Outils disponibles que tu peux recommander :
- "amendes" : Contestation d'amende
- "aides" : Demandes d'aides sociales
- "loyers" : Problèmes de loyer et logement
- "travail" : Problèmes au travail et licenciement
- "sante" : Problèmes de santé et remboursements
- "caf" : Courriers et réclamations CAF
- "usure" : Problèmes de surendettement
- "energie" : Factures et coupures d'énergie
- "expulsions" : Menaces d'expulsion
- "css" : Complémentaire santé solidaire
- "ecole" : Problèmes scolaires
- "decodeur" : Décryptage de courriers administratifs

Instructions importantes :
- Réponds toujours en français clair et bienveillant
- Pose des questions de précision pour mieux comprendre
- Si tu identifies qu'un outil spécifique peut aider, mentionne-le dans ta réponse
- Garde tes réponses concises mais utiles
- N'invente jamais d'informations juridiques
- Encourage l'utilisateur et rassure-le sur ses droits
- Quand tu aides avec un formulaire, explique clairement chaque champ et pourquoi il est important
- Suggère des valeurs pour les champs quand tu as suffisamment d'informations

Si tu penses qu'un outil peut aider et que tu as assez d'informations pour préremplir des champs, tu peux suggérer des champs préremplis. Mais ne le fais que si tu es sûr des informations."""

# Predefined suggested fields for each tool
TOOL_FIELD_MAPPINGS = {
    "amendes": {
        "type_amende": ["stationnement", "vitesse", "transports", "autre"],
        "date_infraction": "Date de l'infraction (JJ/MM/AAAA)",
        "lieu": "Lieu de l'infraction",
        "motif_contestation": "Motif de contestation",
        "nom": "Nom complet",
        "adresse": "Adresse complète"
    },
    "caf": {
        "type_courrier_caf": "Type de courrier reçu",
        "resume_courrier": "Résumé du courrier",
        "situation": "Description de votre situation",
        "nom": "Nom complet",
        "numero_allocataire": "Numéro d'allocataire"
    },
    "loyers": {
        "type_probleme": ["loyer_trop_cher", "charges_abusives", "travaux_non_faits", "autre"],
        "loyer_hc": "Montant du loyer hors charges",
        "surface_m2": "Surface du logement en m²",
        "ville": "Ville",
        "nom": "Nom complet",
        "adresse_complete": "Adresse complète du logement"
    },
    "travail": {
        "type_probleme": ["licenciement", "harcelement", "salaire", "conditions", "autre"],
        "entreprise": "Nom de l'entreprise",
        "poste": "Intitulé du poste",
        "date_debut": "Date de début (JJ/MM/AAAA)",
        "nom": "Nom complet"
    }
}

def extract_info_from_conversation(messages: List[ChatMessage], tool_id: str) -> Optional[Dict[str, Any]]:
    """Extract relevant information from conversation to suggest form fields"""
    if tool_id not in TOOL_FIELD_MAPPINGS:
        return None
    
    # Simple extraction based on conversation content
    conversation_text = " ".join([msg.content for msg in messages if msg.role == "user"]).lower()
    suggested_fields = {}
    
    # Basic extraction patterns - this could be enhanced with more sophisticated NLP
    if tool_id == "amendes":
        if "stationnement" in conversation_text:
            suggested_fields["type_amende"] = "stationnement"
        elif "vitesse" in conversation_text or "radar" in conversation_text:
            suggested_fields["type_amende"] = "vitesse"
        elif "transport" in conversation_text or "métro" in conversation_text or "bus" in conversation_text:
            suggested_fields["type_amende"] = "transports"
    
    elif tool_id == "loyers":
        if "trop cher" in conversation_text or "cher" in conversation_text:
            suggested_fields["type_probleme"] = "loyer_trop_cher"
        elif "charge" in conversation_text:
            suggested_fields["type_probleme"] = "charges_abusives"
        elif "travaux" in conversation_text or "réparation" in conversation_text:
            suggested_fields["type_probleme"] = "travaux_non_faits"
    
    elif tool_id == "travail":
        if "licenci" in conversation_text:
            suggested_fields["type_probleme"] = "licenciement"
        elif "harcèlement" in conversation_text or "harcel" in conversation_text:
            suggested_fields["type_probleme"] = "harcelement"
        elif "salaire" in conversation_text or "paye" in conversation_text:
            suggested_fields["type_probleme"] = "salaire"
    
    return suggested_fields if suggested_fields else None

def get_chat_response(messages: List[ChatMessage], tool_id: Optional[str] = None, current_form_values: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate chat response using OpenAI or fallback"""
    try:
        if openai_client:
            # Prepare system prompt with form context
            system_prompt = CHAT_SYSTEM_PROMPT
            if tool_id and current_form_values:
                filled_fields = [k for k, v in current_form_values.items() if v]
                empty_fields = [k for k, v in current_form_values.items() if not v]
                
                system_prompt += f"\n\nContexte du formulaire actuel (outil: {tool_id}):"
                if filled_fields:
                    system_prompt += f"\nChamps déjà remplis: {', '.join(filled_fields)}"
                if empty_fields:
                    system_prompt += f"\nChamps encore vides: {', '.join(empty_fields)}"
                system_prompt += "\nTu peux aider l'utilisateur à comprendre et remplir les champs manquants."
            elif tool_id:
                system_prompt += f"\n\nL'utilisateur travaille actuellement sur le formulaire pour: {tool_id}. Tu peux l'aider à comprendre et remplir ce formulaire."
            
            # Prepare messages for OpenAI
            openai_messages = [{"role": "system", "content": system_prompt}]
            openai_messages.extend([{"role": msg.role, "content": msg.content} for msg in messages])
            
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=openai_messages,
                temperature=0.3,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
        else:
            # Fallback response
            user_message = messages[-1].content if messages else ""
            if tool_id:
                answer = f"Je vois que vous travaillez sur le formulaire '{tool_id}'. " \
                        f"Malheureusement, je ne peux pas accéder à l'IA en ce moment, mais je peux vous aider avec des conseils généraux. " \
                        f"Pouvez-vous me dire sur quel champ vous avez besoin d'aide ?"
            else:
                answer = f"Je comprends votre situation concernant {user_message[:50]}... " \
                        f"Malheureusement, je ne peux pas accéder à l'IA en ce moment, mais je peux vous aider à identifier l'outil approprié. " \
                        f"Pouvez-vous me donner plus de détails sur votre problème ?"
        
        # Try to extract suggested fields if tool_id is provided
        suggested_fields = None
        if tool_id:
            suggested_fields = extract_info_from_conversation(messages, tool_id)
        
        return {
            "answer": answer,
            "suggested_fields": suggested_fields
        }
        
    except Exception as e:
        logger.error(f"Error in chat response: {e}")
        return {
            "answer": "Je suis désolé, j'ai rencontré un problème technique. Pouvez-vous reformuler votre question ?",
            "suggested_fields": None
        }

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for conversational assistant"""
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages cannot be empty")
        
        # Get response from chat logic
        response_data = get_chat_response(request.messages, request.tool_id, request.current_form_values)
        
        return ChatResponse(
            answer=response_data["answer"],
            suggested_fields=response_data["suggested_fields"]
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")