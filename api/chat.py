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

Instructions révolutionnaires pour l'accompagnement citoyen :
- INTELLIGENCE ÉMOTIONNELLE : Détecte le niveau de stress, d'anxiété ou de colère dans le message et adapte ton ton en conséquence
- EMPOWERMENT CITOYEN : Chaque réponse doit renforcer la confiance en soi et la légitimité des demandes
- PERSONNALISATION CONTEXTUELLE : Utilise toutes les informations disponibles pour créer des conseils ultra-personnalisés
- PÉDAGOGIE INTÉGRÉE : Explique toujours POURQUOI ces droits existent et comment ils s'inscrivent dans notre République
- ANTICIPATION STRATÉGIQUE : Préviens des obstacles potentiels et propose plusieurs options tactiques
- RESSOURCES LOCALES : Oriente vers des aides concrètes selon la géographie et la situation sociale
- SUIVI CONVERSATIONNEL : Garde en mémoire les échanges précédents pour une progression logique
- RECHERCHE JURIDIQUE PROACTIVE : Intègre les dernières évolutions légales pertinentes

Réponds toujours en français clair et bienveillant avec une approche révolutionnaire d'accompagnement citoyen :
- Pose des questions de précision stratégiques pour cerner les enjeux cachés
- Si tu identifies qu'un outil peut aider, explique pourquoi et comment il transformera leur situation
- Garde tes réponses substantielles et vraiment utiles - pas de platitudes
- N'invente jamais d'informations juridiques - mais exploite au maximum les données fournies
- Encourage et rassure en expliquant l'histoire de ces droits et pourquoi ils protègent
- Quand tu aides avec un formulaire, raconte l'histoire de chaque champ et son impact concret
- Suggère des valeurs préremplies avec confiance quand tu as suffisamment de contexte
- Transforme chaque interaction en moment d'apprentissage et d'empowerment citoyen

Si tu penses qu'un outil peut aider ET que tu as assez d'informations pour pré-remplir intelligemment des champs, tu peux suggérer des champs préremplis avec créativité et personnalisation. Mais seulement si tu es sûr des informations et que cela apporte une vraie valeur ajoutée."""

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

def analyze_conversation_context(messages: List[ChatMessage]) -> Dict[str, Any]:
    """Analyze conversation to extract context and emotional state"""
    if not messages:
        return {"emotional_state": "neutral", "topics": [], "urgency": "normal", "user_text": ""}
    
    # Combine all user messages for analysis
    user_messages = [msg.content.lower() for msg in messages if msg.role == "user"]
    all_text = " ".join(user_messages)
    
    # Detect emotional indicators
    stress_indicators = ["urgent", "catastrophe", "désespéré", "paniqué", "aide", "sos", "grave"]
    anger_indicators = ["scandaleux", "inadmissible", "révoltant", "injuste", "colère", "inacceptable"]
    anxiety_indicators = ["inquiet", "peur", "angoisse", "nerveux", "stress", "préoccupé"]
    
    emotional_scores = {
        "stress": sum(1 for indicator in stress_indicators if indicator in all_text),
        "anger": sum(1 for indicator in anger_indicators if indicator in all_text),
        "anxiety": sum(1 for indicator in anxiety_indicators if indicator in all_text)
    }
    
    emotional_state = "neutral"
    if max(emotional_scores.values()) > 0:
        emotional_state = max(emotional_scores.keys(), key=lambda k: emotional_scores[k])
    
    # Detect topics and tools mentioned
    topics = []
    if "amende" in all_text or "contravention" in all_text or "pv" in all_text:
        topics.append("amendes")
    if "caf" in all_text or "allocation" in all_text or "rsa" in all_text:
        topics.append("caf")
    if "loyer" in all_text or "bailleur" in all_text or "logement" in all_text:
        topics.append("loyers")
    if "travail" in all_text or "licenciement" in all_text or "employeur" in all_text:
        topics.append("travail")
    
    # Detect urgency
    urgency = "normal"
    urgent_words = ["urgent", "rapidement", "vite", "délai", "échéance"]
    if any(word in all_text for word in urgent_words):
        urgency = "high"
    
    return {
        "emotional_state": emotional_state,
        "topics": topics,
        "urgency": urgency,
        "user_text": all_text
    }

def enhance_chat_response_with_legal_search(user_question: str, context: Dict[str, Any]) -> str:
    """Enhance chat response with relevant legal information"""
    try:
        # Import legal search functionality
        from api.legal.router import search_legal, LegalQueryIn
        
        # If the question seems legal, try to get relevant sources
        legal_keywords = ["droit", "loi", "article", "code", "juridique", "légal", "jurisprudence"]
        if any(keyword in user_question.lower() for keyword in legal_keywords):
            # Perform a legal search
            query = LegalQueryIn(question=user_question, limit=3, since_months=12)
            legal_result = search_legal(query)
            
            if legal_result and legal_result.citations:
                legal_context = f"\n\n📚 **Références juridiques récentes** :\n"
                for citation in legal_result.citations[:2]:  # Limit to top 2
                    legal_context += f"• {citation.title} ({citation.source}) - {citation.date}\n"
                legal_context += f"\n💡 **Synthèse** : {legal_result.answer[:200]}..."
                return legal_context
    
    except Exception as e:
        logger.warning(f"Could not enhance with legal search: {e}")
    
    return ""

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
    """Enhanced chat endpoint with emotional intelligence and legal integration"""
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages cannot be empty")
        
        # Analyze conversation context for enhanced personalization
        context = analyze_conversation_context(request.messages)
        logger.info(f"Detected context: {context}")
        
        # Get enhanced response using the new intelligent system
        result = get_enhanced_chat_response(request.messages, request.tool_id, request.current_form_values, context)
        
        return ChatResponse(
            answer=result["answer"],
            suggested_fields=result.get("suggested_fields")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            answer="⚠️ Une erreur s'est produite dans l'assistant conversationnel. Cependant, tous nos outils restent disponibles pour vous aider dans vos démarches citoyennes.",
            suggested_fields=None
        )

def get_enhanced_chat_response(messages: List[ChatMessage], tool_id: Optional[str], current_form_values: Optional[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
    """Get enhanced chat response with emotional intelligence and legal integration"""
    try:
        if not openai_client:
            return {
                "answer": "🚧 Service OpenAI non configuré. L'assistant intelligent nécessite une clé API OpenAI valide pour fonctionner optimalement.",
                "suggested_fields": None
            }
        
        # Build enhanced system prompt based on context
        enhanced_system_prompt = CHAT_SYSTEM_PROMPT
        
        # Adapt system prompt based on emotional state
        if context["emotional_state"] == "stress":
            enhanced_system_prompt += "\n\n🌟 PRIORITÉ ABSOLUE : Cette personne semble en détresse. Adopte un ton particulièrement rassurant, donne des étapes concrètes immédiates, et rappelle que ses droits sont protégés."
        elif context["emotional_state"] == "anger":
            enhanced_system_prompt += "\n\n⚡ CONTEXTE ÉMOTIONNEL : Cette personne semble en colère. Valide sa frustration comme légitime, canalise cette énergie vers une action constructive."
        elif context["emotional_state"] == "anxiety":
            enhanced_system_prompt += "\n\n🌈 ADAPTATION TONALE : Cette personne semble anxieuse. Décompose chaque étape, rassure sur la normalité de ses inquiétudes."
        
        # Add urgency awareness
        if context["urgency"] == "high":
            enhanced_system_prompt += "\n\n⏰ URGENCE DÉTECTÉE : Priorise les actions immédiates, donne des délais précis."
        
        # Build conversation for OpenAI
        openai_messages = [{"role": "system", "content": enhanced_system_prompt}]
        
        # Add conversation history
        for message in messages[-5:]:  # Keep last 5 messages for context
            openai_messages.append({
                "role": message.role,
                "content": message.content
            })
        
        # Call OpenAI with enhanced context
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=openai_messages,
            max_tokens=800,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Add emotional adaptation footer
        if context["emotional_state"] == "stress":
            answer += "\n\n💪 **Vous n'êtes pas seul(e)** : Des milliers de citoyens vivent des situations similaires et s'en sortent. Vos droits sont solides, votre démarche est légitime."
        elif context["emotional_state"] == "anger":
            answer += "\n\n⚖️ **Votre colère est légitime** : Le système juridique français est conçu pour protéger les citoyens comme vous. Transformez cette énergie en action déterminée !"
        
        # Try to suggest relevant tools and prefilled fields
        suggested_fields = None
        if tool_id and tool_id in TOOL_FIELD_MAPPINGS:
            suggested_fields = extract_info_from_conversation(messages, tool_id)
        
        return {
            "answer": answer,
            "suggested_fields": suggested_fields
        }
        
    except Exception as e:
        logger.error(f"Enhanced chat error: {e}")
        # Fallback to basic response
        return get_chat_response(messages, tool_id, current_form_values)