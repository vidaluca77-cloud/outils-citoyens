"""
Schema-driven prompt building module for Outils Citoyens
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def load_schema(tool_id: str) -> Dict[str, Any]:
    """Load JSON schema for a tool"""
    # Try public/schemas first (Next.js structure), then schemas folder
    schema_paths = [
        Path("../public/schemas") / f"{tool_id}.json",
        Path("../schemas") / f"{tool_id}.json",
        Path("schemas") / f"{tool_id}.json"
    ]
    
    for schema_path in schema_paths:
        try:
            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load schema from {schema_path}: {e}")
            continue
    
    # Fallback generic schema
    logger.warning(f"No schema found for {tool_id}, using generic schema")
    return {
        "title": f"Outil {tool_id}",
        "properties": {
            "identite": {
                "type": "object",
                "properties": {
                    "nom": {"type": "string"},
                    "prenom": {"type": "string"},
                    "adresse": {"type": "string"}
                }
            }
        }
    }

def build_context(payload: Dict[str, Any], schema: Dict[str, Any]) -> str:
    """Build organized context from form fields"""
    context_lines = []
    
    # Extract user identity if present
    identite = payload.get('identite', {})
    if identite:
        context_lines.append("=== IDENTITÉ ===")
        if identite.get('nom'):
            context_lines.append(f"Nom: {identite['nom']}")
        if identite.get('prenom'):
            context_lines.append(f"Prénom: {identite['prenom']}")
        if identite.get('adresse'):
            context_lines.append(f"Adresse: {identite['adresse']}")
        context_lines.append("")
    
    # Extract other fields based on schema properties
    context_lines.append("=== DONNÉES DU FORMULAIRE ===")
    properties = schema.get('properties', {})
    
    for field_name, field_value in payload.items():
        if field_name == 'identite':
            continue  # Already processed
            
        # Get field schema info
        field_schema = properties.get(field_name, {})
        field_title = field_schema.get('title', field_name.replace('_', ' ').title())
        
        if isinstance(field_value, dict):
            context_lines.append(f"{field_title}:")
            for k, v in field_value.items():
                context_lines.append(f"  - {k}: {v}")
        elif isinstance(field_value, list):
            context_lines.append(f"{field_title}:")
            for item in field_value:
                context_lines.append(f"  - {item}")
        else:
            context_lines.append(f"{field_title}: {field_value}")
    
    return "\n".join(context_lines)

def load_template(tool_id: str) -> str:
    """Load Jinja template for a tool, fallback to generic"""
    template_paths = [
        Path("templates") / f"{tool_id}.j2",
        Path("templates") / "_generic.j2"
    ]
    
    for template_path in template_paths:
        try:
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.warning(f"Failed to load template from {template_path}: {e}")
            continue
    
    # Hardcoded fallback if no template files found
    return """DESTINATAIRE: {{ destinataire or "Service compétent" }}
OBJET: {{ objet or ("Courrier – " + tool_id|upper) }}

CORPS:
{{ corps }}

PIÈCES JOINTES:
{% for pj in pieces_jointes -%}
- {{ pj }}
{% endfor %}

SIGNATURE:
{{ identite.nom }} {{ identite.prenom }}
{{ identite.adresse }}
"""

def load_fewshots(tool_id: str) -> str:
    """Load few-shot examples for a tool"""
    fewshot_path = Path("fewshots") / f"{tool_id}.md"
    
    try:
        if fewshot_path.exists():
            with open(fewshot_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        logger.warning(f"Failed to load fewshots from {fewshot_path}: {e}")
    
    return ""

def get_checklist_blueprint(tool_id: str) -> List[str]:
    """Get checklist blueprint for a tool"""
    blueprints = {
        "amendes": [
            "Respecter le délai de 45 jours pour la contestation",
            "Envoyer en lettre recommandée avec accusé de réception",
            "Rassembler toutes les preuves (photos, témoignages)",
            "Conserver l'original de l'avis de contravention",
            "Vérifier l'exactitude des mentions du procès-verbal"
        ],
        "caf": [
            "Respecter le délai de recours de 2 mois",
            "Rassembler tous les justificatifs de situation",
            "Envoyer en LRAR avec numéro allocataire",
            "Conserver copies et accusés de réception"
        ],
        "loyers": [
            "Vérifier l'applicabilité de l'encadrement des loyers",
            "Consulter les données officielles de référence",
            "Calculer précisément le dépassement",
            "Envoyer en LRAR au bailleur"
        ]
    }
    
    return blueprints.get(tool_id, [
        "Rassembler tous les documents nécessaires",
        "Respecter les délais légaux",
        "Envoyer en lettre recommandée",
        "Conserver toutes les preuves"
    ])

def get_mentions_blueprint(tool_id: str) -> List[str]:
    """Get mentions blueprint for a tool"""
    blueprints = {
        "amendes": [
            "Délai de contestation : 45 jours maximum",
            "Envoi obligatoire en lettre recommandée",
            "Recours possible devant le tribunal en cas de rejet",
            "Ne pas payer l'amende pendant la contestation"
        ],
        "caf": [
            "Délai de recours : 2 mois après notification",
            "Possibilité de saisir la CRA en cas d'échec",
            "Maintien des droits pendant l'instruction",
            "Aide juridictionnelle possible"
        ],
        "loyers": [
            "Prescription triennale pour les actions en restitution",
            "Recours devant la commission de conciliation",
            "Possibilité de saisir le tribunal judiciaire",
            "Conservation obligatoire des preuves"
        ]
    }
    
    return blueprints.get(tool_id, [
        "Respecter les délais légaux",
        "Conserver tous les documents",
        "Recours possibles en cas de refus",
        "Aide juridique disponible si nécessaire"
    ])

def build_prompt(tool_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to build schema-driven prompt
    
    Args:
        tool_id: Tool identifier (e.g., 'amendes', 'caf')
        payload: Form data from user
        
    Returns:
        Dict with prompt components
    """
    try:
        # Load schema and build context
        schema = load_schema(tool_id)
        context = build_context(payload, schema)
        
        # Load template and few-shot examples
        template = load_template(tool_id)
        fewshots = load_fewshots(tool_id)
        
        # Get blueprints
        checklist_blueprint = get_checklist_blueprint(tool_id)
        mentions_blueprint = get_mentions_blueprint(tool_id)
        
        # Build system prompt
        system_prompt = """Tu es un assistant juridique français expert et bienveillant, spécialisé en démarches administratives. 
Tu maintiens un ton administratif français, factuel, sans donner de conseils juridiques personnalisés.

Ta mission : générer une réponse JSON complète avec 4 clés pour des lettres officielles."""

        # Build instructions
        instructions = f"""Contraintes de style et structure :
- Ton administratif français professionnel mais accessible
- Structure argumentative claire et logique
- Intégration naturelle des données utilisateur
- Aucun conseil juridique personnalisé, seulement des faits et procédures
- Formules de politesse appropriées mais chaleureuses"""

        # Add few-shot examples if available
        if fewshots:
            context = f"{context}\n\n=== EXEMPLES ===\n{fewshots}"
        
        return {
            "system": system_prompt,
            "instructions": instructions,
            "context": context,
            "template": template,
            "checklist_blueprint": checklist_blueprint,
            "mentions_blueprint": mentions_blueprint
        }
        
    except Exception as e:
        logger.error(f"Error building prompt for {tool_id}: {e}")
        # Return minimal fallback
        return {
            "system": "Assistant juridique français pour courriers administratifs",
            "instructions": "Répondre en français administratif, ton factuel",
            "context": f"Outil: {tool_id}\nDonnées: {json.dumps(payload, ensure_ascii=False)}",
            "template": load_template("_generic"),
            "checklist_blueprint": get_checklist_blueprint(tool_id),
            "mentions_blueprint": get_mentions_blueprint(tool_id)
        }