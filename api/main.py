from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import time
import openai
from openai import OpenAI
from typing import Dict, Any, List, Optional
import logging
from jinja2 import Template
import re
import prompting
from collections import defaultdict
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple rate limiting
rate_limit_store = defaultdict(list)

app = FastAPI(title="Outils Citoyens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://outils-citoyens-three.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

# Pydantic models
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

class GenerateRequest(BaseModel):
    tool_id: str
    fields: Dict[str, Any]
    
    class Config:
        # Add validation
        max_anystr_length = 10000  # Limit string length
        validate_assignment = True
        
    def __init__(self, **data):
        # Sanitize inputs
        if 'fields' in data:
            data['fields'] = self._sanitize_fields(data['fields'])
        super().__init__(**data)
    
    def _sanitize_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input fields to prevent injection attacks"""
        sanitized = {}
        for key, value in fields.items():
            if isinstance(value, str):
                # Remove dangerous characters and limit length
                value = value.strip()[:5000]  # Limit to 5000 chars
                # Remove script tags and other dangerous content
                value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
                value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
                sanitized[key] = value
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_fields(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    item.strip()[:1000] if isinstance(item, str) else item 
                    for item in value[:50]  # Limit array size
                ]
            else:
                sanitized[key] = value
        return sanitized

# Utility functions
def check_rate_limit(client_ip: str, max_requests: int = 60, window_minutes: int = 5) -> bool:
    """Simple rate limiting: max_requests per window_minutes per IP"""
    now = datetime.now()
    window_start = now - timedelta(minutes=window_minutes)
    
    # Clean old entries
    rate_limit_store[client_ip] = [
        timestamp for timestamp in rate_limit_store[client_ip]
        if timestamp > window_start
    ]
    
    # Check if under limit
    if len(rate_limit_store[client_ip]) >= max_requests:
        return False
    
    # Add current request
    rate_limit_store[client_ip].append(now)
    return True
def remove_emojis(text: str) -> str:
    """Remove emojis from text"""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def format_work_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    """Format work fields to ensure no raw objects, convert to strings"""
    formatted_fields = fields.copy()
    
    # Format employer information as strings
    if 'employeur' in formatted_fields:
        if isinstance(formatted_fields['employeur'], dict):
            emp = formatted_fields['employeur']
            formatted_fields['employeur_nom'] = str(emp.get('nom', ''))
            formatted_fields['employeur_adresse'] = str(emp.get('adresse', ''))
            del formatted_fields['employeur']
        elif isinstance(formatted_fields['employeur'], str):
            formatted_fields['employeur_nom'] = formatted_fields['employeur']
            formatted_fields['employeur_adresse'] = ''
    
    # Ensure all fields are strings or basic types
    for key, value in formatted_fields.items():
        if isinstance(value, dict) or isinstance(value, list):
            formatted_fields[key] = str(value)
    
    return formatted_fields

def calculate_price_per_sqm(fields: Dict[str, Any]) -> Optional[str]:
    """Calculate price per square meter for rent tools"""
    try:
        surface = fields.get('surface')
        loyer = fields.get('loyer')
        
        if surface and loyer:
            # Extract numeric values
            surface_num = float(re.sub(r'[^0-9.]', '', str(surface)))
            loyer_num = float(re.sub(r'[^0-9.]', '', str(loyer)))
            
            if surface_num > 0:
                price_per_sqm = loyer_num / surface_num
                return f"Le prix au mètre carré s'élève à {price_per_sqm:.2f}€/m², ce qui permet d'évaluer la pertinence du montant demandé."
    except (ValueError, TypeError):
        pass
    
    return None

def ensure_four_paragraphs(corps: str) -> str:
    """Ensure letter body has exactly 4 paragraphs"""
    paragraphs = [p.strip() for p in corps.split('\n\n') if p.strip()]
    
    if len(paragraphs) < 4:
        # Add generic paragraphs to reach 4
        while len(paragraphs) < 4:
            if len(paragraphs) == 1:
                paragraphs.append("Je vous expose ci-dessous les faits et les démarches entreprises à ce jour.")
            elif len(paragraphs) == 2:
                paragraphs.append("Cette situation nécessite une intervention de votre part afin de résoudre cette problématique.")
            elif len(paragraphs) == 3:
                paragraphs.append("Je vous remercie par avance de l'attention que vous porterez à ma demande et reste à votre disposition pour tout complément d'information.")
    
    elif len(paragraphs) > 4:
        # Merge excess paragraphs into the last one
        merged_last = ' '.join(paragraphs[3:])
        paragraphs = paragraphs[:3] + [merged_last]
    
    return '\n\n'.join(paragraphs)

def make_subject_sober(objet: str) -> str:
    """Make subject line more sober and professional"""
    # Remove emojis and excessive punctuation
    objet = remove_emojis(objet)
    objet = re.sub(r'[!]{2,}', '!', objet)
    objet = re.sub(r'[?]{2,}', '?', objet)
    
    # Ensure it starts with appropriate formal terms
    formal_starts = ['Objet :', 'Demande de', 'Réclamation concernant', 'Contestation de', 'Demande d\'intervention']
    
    has_formal_start = any(objet.strip().startswith(start) for start in formal_starts)
    
    if not has_formal_start and not objet.strip().startswith('Objet :'):
        objet = f"Objet : {objet.strip()}"
    
    return objet.strip()

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/generate", response_model=Output)
async def generate_document(request: GenerateRequest, req: Request):
    """Generate document based on tool_id and fields"""
    # Rate limiting
    client_ip = req.client.host if req.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    
    try:
        tool_id = request.tool_id
        fields = request.fields
        
        # Validate tool_id
        valid_tools = ["amendes", "caf", "loyers", "travail", "sante", "energie", "expulsions", "css", "ecole", "decodeur", "usure", "aides"]
        if tool_id not in valid_tools:
            logger.warning(f"Invalid tool_id requested: {tool_id}")
            raise HTTPException(status_code=400, detail=f"Invalid tool_id. Must be one of: {', '.join(valid_tools)}")
        
        # Special handling for work tool
        if tool_id == "travail":
            fields = format_work_fields(fields)
        
        logger.info(f"Generating document for tool: {tool_id}")
        
        # Generate base content using OpenAI
        if client:
            result = await generate_with_openai(tool_id, fields)
        else:
            result = generate_mock_response(tool_id, fields)
        
        # Post-process the result
        result = post_process_output(result, tool_id, fields)
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise  
    except Exception as e:
        logger.error(f"Unexpected error generating document: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

async def generate_with_openai(tool_id: str, fields: Dict[str, Any]) -> Output:
    """Generate content using OpenAI"""
    # Load system prompt and templates
    system_prompt = load_system_prompt()
    tool_template = load_tool_template(tool_id)
    
    # Create user prompt
    user_prompt = create_user_prompt(tool_id, fields, tool_template)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=1200
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON response
        try:
            result_data = json.loads(content)
            return Output(**result_data)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return generate_mock_response(tool_id, fields)
            
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return generate_mock_response(tool_id, fields)

def generate_mock_response(tool_id: str, fields: Dict[str, Any]) -> Output:
    """Generate mock response when OpenAI is not available"""
    return Output(
        resume=[
            "Étape 1 : Rédaction de votre courrier officiel",
            "Étape 2 : Rassemblement des pièces justificatives",
            "Étape 3 : Envoi recommandé avec accusé de réception",
            "Étape 4 : Suivi de votre demande dans les délais légaux"
        ],
        lettre=Lettre(
            destinataire_bloc="[Destinataire à compléter]\n[Adresse à compléter]",
            objet=f"Objet : Demande concernant {tool_id}",
            corps="Madame, Monsieur,\n\nJe me permets de vous contacter concernant ma situation.\n\nJe vous expose ci-dessous les faits et les démarches entreprises à ce jour.\n\nJe vous remercie par avance de l'attention que vous porterez à ma demande.\n\nJe vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.",
            pj=["Copie de pièce d'identité", "Justificatifs pertinents"],
            signature="[Votre nom]\n[Votre adresse]\n[Date]"
        ),
        checklist=[
            "Vérifier l'exactitude des informations",
            "Rassembler les pièces justificatives",
            "Envoyer en recommandé avec AR",
            "Conserver une copie du courrier"
        ],
        mentions="Aide automatisée - ne remplace pas un conseil d'avocat. En cas de situation complexe, consultez un professionnel du droit."
    )

def post_process_output(output: Output, tool_id: str, fields: Dict[str, Any]) -> Output:
    """Post-process the output to apply normalization rules"""
    # Remove emojis from resume and mentions
    output.resume = [remove_emojis(item) for item in output.resume]
    output.mentions = remove_emojis(output.mentions)
    
    # Ensure 4 paragraphs in letter body
    output.lettre.corps = ensure_four_paragraphs(output.lettre.corps)
    
    # Make subject sober
    output.lettre.objet = make_subject_sober(output.lettre.objet)
    
    # Special handling for loyers tool
    if tool_id == "loyers":
        price_calc = calculate_price_per_sqm(fields)
        if price_calc:
            # Insert calculation in the second paragraph
            paragraphs = output.lettre.corps.split('\n\n')
            if len(paragraphs) >= 2:
                paragraphs[1] += f" {price_calc}"
                output.lettre.corps = '\n\n'.join(paragraphs)
    
    return output

def load_system_prompt() -> str:
    """Load system prompt from file"""
    try:
        with open('system_lumiere.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Vous êtes un assistant spécialisé dans la rédaction de courriers administratifs français."

def load_tool_template(tool_id: str) -> str:
    """Load tool-specific template"""
    try:
        with open('templates.json', 'r', encoding='utf-8') as f:
            templates = json.load(f)
            return templates.get(tool_id, "")
    except FileNotFoundError:
        return ""

def create_user_prompt(tool_id: str, fields: Dict[str, Any], template: str) -> str:
    """Create user prompt for OpenAI"""
    return f"""Outil: {tool_id}
Données: {json.dumps(fields, ensure_ascii=False)}
Template: {template}

Générez un document administratif complet au format JSON avec les champs: resume, lettre (destinataire_bloc, objet, corps, pj, signature), checklist, mentions."""

# Include chat router
try:
    from chat import router as chat_router
    app.include_router(chat_router)
except ImportError:
    logger.warning("Chat router not available")

# Include legal router  
try:
    from legal.router import router as legal_router
    app.include_router(legal_router)
except ImportError:
    logger.warning("Legal router not available")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
