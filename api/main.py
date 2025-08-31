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

def integrate_css_data(response: Dict[str, Any], user_fields: dict) -> Dict[str, Any]:
    """Integrate user data into CSS mock response for personalization"""
    import copy
    
    # Deep copy to avoid modifying the original
    personalized = copy.deepcopy(response)
    
    # Extract user data with fallbacks
    revenu = user_fields.get("revenu_mensuel_net", "[Revenus mensuels]")
    foyer = user_fields.get("foyer", "[Nombre de personnes]")
    age = user_fields.get("age", "[Age]")
    statut = user_fields.get("statut", "[Statut]")
    couverture = user_fields.get("couverture_actuelle", "[Couverture actuelle]")
    
    # Calculate eligibility (simplified 2024 thresholds)
    eligibility_text = "[Éligibilité à calculer]"
    css_type = "CSS sans participation"
    
    if isinstance(revenu, (int, float)) and isinstance(foyer, int):
        annual_income = float(revenu) * 12
        # Simplified thresholds for 2024 (approximate)
        thresholds = {1: 9203, 2: 13804, 3: 16565, 4: 19326, 5: 22087}
        threshold = thresholds.get(int(foyer), 22087 + (int(foyer) - 5) * 2761)
        
        if annual_income <= threshold:
            eligibility_text = f"ÉLIGIBLE à la CSS gratuite (revenus: {annual_income:.0f}€/an, plafond: {threshold}€)"
            css_type = "CSS sans participation financière"
        elif annual_income <= threshold * 1.35:  # Participation bracket
            participation = round((annual_income - threshold) * 0.08 / 12)
            eligibility_text = f"ÉLIGIBLE à la CSS avec participation de {participation}€/mois"
            css_type = "CSS avec participation forfaitaire"
        else:
            eligibility_text = f"NON ÉLIGIBLE (revenus: {annual_income:.0f}€/an dépassent le plafond de {threshold}€)"
            css_type = "Alternative : mutuelle privée ou d'entreprise"
    
    # Personalize resume
    personalized["resume"][0] = f"Évaluer l'éligibilité CSS pour un foyer de {foyer} personne(s) avec {revenu}€/mois de revenus"
    personalized["resume"][2] = f"Déposer la demande CSS auprès de la CPAM avec le formulaire S3715 pour {css_type}"
    
    # Personalize letter
    lettre = personalized["lettre"]
    lettre["destinataire_bloc"] = "Caisse Primaire d'Assurance Maladie\nService Complémentaire Santé Solidaire\n[Adresse CPAM de votre département]\n[Code postal] [Ville]"
    lettre["objet"] = f"Demande de Complémentaire Santé Solidaire - Foyer {foyer} personne(s) - Revenus {revenu}€/mois"
    
    statut_text = ""
    if statut in ["chomeur", "demandeur_emploi"]:
        statut_text = " en situation de recherche d'emploi"
    elif statut == "retraite":
        statut_text = " retraité(e)"
    elif statut == "etudiant":
        statut_text = " étudiant(e)"
    
    lettre["corps"] = f"""Madame, Monsieur,

J'ai l'honneur de solliciter l'attribution de la Complémentaire Santé Solidaire pour mon foyer composé de {foyer} personne(s){statut_text}, avec des revenus mensuels nets de {revenu}€.

Situation actuelle : {couverture if couverture != "aucune" else "aucune couverture complémentaire santé"}.

{eligibility_text}

Veuillez trouver ci-joint l'ensemble des pièces justificatives requises par la réglementation en vigueur.

Dans l'attente de votre réponse dans un délai de 2 mois, je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations respectueuses."""
    
    # Personalize pieces jointes based on status
    pj_list = ["Formulaire S3715 dûment complété et signé", "Justificatifs de revenus des 3 derniers mois complets"]
    
    if statut in ["chomeur", "demandeur_emploi"]:
        pj_list.append("Attestation de situation Pôle emploi actualisée")
    elif statut == "retraite":
        pj_list.append("Notification de pension de retraite")
    elif statut == "etudiant":
        pj_list.append("Certificat de scolarité en cours de validité")
    
    pj_list.extend(["Justificatif de domicile de moins de 3 mois", "Copie recto-verso de la pièce d'identité"])
    lettre["pj"] = pj_list
    
    # Personalize checklist
    if isinstance(revenu, (int, float)) and isinstance(foyer, int):
        annual = float(revenu) * 12
        personalized["checklist"][0] = f"Vérifier l'éligibilité : {revenu}€ × 12 = {annual:.0f}€/an pour {foyer} personne(s)"
    
    return personalized

def integrate_loyers_data(response: Dict[str, Any], user_fields: dict) -> Dict[str, Any]:
    """Integrate user data into loyers mock response for personalization"""
    import copy
    
    # Deep copy to avoid modifying the original
    personalized = copy.deepcopy(response)
    
    # Extract user data with fallbacks
    loyer = user_fields.get("loyer_actuel", "[Montant du loyer]")
    surface = user_fields.get("surface", "[Surface]")
    ville = user_fields.get("ville", "[Ville]")
    adresse = user_fields.get("adresse", "[Adresse du logement]")
    type_logement = user_fields.get("type", "logement")
    
    # Calculate potential excess (simplified estimate for demonstration)
    excess_text = "[Calcul du dépassement]"
    if isinstance(loyer, (int, float, str)) and isinstance(surface, (int, float, str)):
        try:
            loyer_val = float(loyer)
            surface_val = float(surface)
            prix_m2 = loyer_val / surface_val
            if prix_m2 > 25:  # Simplified threshold for Paris
                excess = loyer_val - (25 * surface_val)
                excess_text = f"Dépassement estimé de {excess:.0f}€/mois ({prix_m2:.2f}€/m² vs référence ~25€/m²)"
        except:
            pass
    
    # Personalize resume
    personalized["resume"][0] = f"Vérifier l'encadrement des loyers applicable à {ville} pour un {type_logement} de {surface}m²"
    personalized["resume"][1] = f"Calculer le dépassement du loyer de référence pour le logement sis {adresse} (loyer actuel: {loyer}€)"
    
    # Personalize letter
    lettre = personalized["lettre"]
    lettre["objet"] = f"Contestation du montant du loyer - Logement sis {adresse}, {ville}"
    
    lettre["corps"] = f"""Monsieur/Madame le Bailleur,

J'ai l'honneur de porter à votre connaissance ma contestation formelle concernant le montant du loyer pratiqué pour le logement que j'occupe sis {adresse}, {ville}.

Après vérification auprès des services compétents, il apparaît que le loyer mensuel de {loyer}€ pour un {type_logement} de {surface}m² dépasse manifestement les plafonds légaux en vigueur dans cette zone.

{excess_text}

Conformément aux dispositions de la loi ELAN et du décret d'application relatif à l'encadrement des loyers, je vous demande de bien vouloir procéder à la régularisation de cette situation en ramenant le loyer au montant légalement autorisé.

Je vous prie d'agréer, Monsieur/Madame le Bailleur, l'expression de ma considération distinguée."""
    
    # Update pieces jointes
    lettre["pj"] = [
        f"Bail de location du logement sis {adresse}",
        "Quittances de loyer des 12 derniers mois",
        f"Données de référence des loyers à {ville}",
        "Justificatif d'identité en cours de validité"
    ]
    
    # Personalize checklist
    personalized["checklist"][0] = f"Consulter les loyers de référence en mairie de {ville} ou sur le site officiel"
    personalized["checklist"][1] = f"Calculer précisément le dépassement pour un {type_logement} de {surface}m² à {loyer}€/mois"
    
    return personalized

def integrate_amendes_data(response: Dict[str, Any], user_fields: dict) -> Dict[str, Any]:
    """Integrate user data into amendes mock response for personalization"""
    import copy
    from datetime import datetime, timedelta
    
    # Deep copy to avoid modifying the original
    personalized = copy.deepcopy(response)
    
    # Extract user data with fallbacks
    numero = user_fields.get("numero_amende", "[Numéro PV]")
    motif = user_fields.get("motif", "[Motif de la contravention]")
    lieu = user_fields.get("lieu", "[Lieu de l'infraction]")
    date_pv = user_fields.get("date", "[Date]")
    heure = user_fields.get("heure", "[Heure]")
    
    # Calculate 45-day deadline if date is provided
    deadline_text = "[45 jours après réception]"
    if date_pv and "/" in str(date_pv):
        try:
            # Assume format DD/MM/YYYY and calculate 45 days later
            day, month, year = map(int, str(date_pv).split("/"))
            pv_date = datetime(year, month, day)
            deadline = pv_date + timedelta(days=45)
            deadline_text = deadline.strftime("%d/%m/%Y")
        except:
            pass  # Keep fallback if parsing fails
    
    # Personalize resume
    if "numéro" in str(personalized["resume"][0]).lower():
        personalized["resume"][0] = f"Analyser minutieusement les mentions du procès-verbal n° {numero} dans un délai de 5 jours"
    
    if len(personalized["resume"]) > 3:
        personalized["resume"][3] = f"Expédier le courrier en LRAR avant l'échéance du {deadline_text} (45e jour après réception)"
    
    # Personalize letter
    lettre = personalized["lettre"]
    
    # Update object with specific data
    lettre["objet"] = f"Contestation formelle du procès-verbal n° {numero} - {motif.title()} du {date_pv} - Art. L121-3 du Code de la route"
    
    # Update letter body with personalized data
    lettre["corps"] = f"""Monsieur l'Officier du Ministère Public,

J'ai l'honneur de porter à votre connaissance ma contestation formelle du procès-verbal n° {numero} dressé le {date_pv} à {heure} pour {motif} sur la voie publique sise {lieu}.

Après examen attentif des circonstances de fait et de droit, je conteste cette verbalisation pour les motifs juridiques suivants :

[Exposé détaillé et argumenté des moyens de contestation selon les preuves disponibles]

En conséquence, et conformément aux dispositions de l'article 530 du Code de procédure pénale, je sollicite respectueusement l'annulation pure et simple de cette contravention.

Dans l'attente de votre décision motivée, je vous prie d'agréer, Monsieur l'Officier du Ministère Public, l'expression de ma haute considération."""
    
    # Update pieces jointes with specific PV number
    lettre["pj"][0] = f"Copie intégrale du procès-verbal n° {numero}"
    if lieu != "[Lieu de l'infraction]":
        lettre["pj"][1] = f"Photographies horodatées du lieu {lieu}"
    
    # Personalize checklist
    if deadline_text != "[45 jours après réception]":
        personalized["checklist"][0] = f"Respecter impérativement le délai légal de 45 jours (échéance : {deadline_text})"
    
    if lieu != "[Lieu de l'infraction]":
        personalized["checklist"][1] = f"Photographier le lieu {lieu} avec horodatage pour constitution de preuves"
    
    if numero != "[Numéro PV]":
        personalized["checklist"][3] = f"Vérifier l'exactitude des mentions du PV n° {numero} (heure, lieu, motif)"
    
    return personalized

def get_mock_response(tool_id: str, user_fields: dict = None) -> Dict[str, Any]:
    """Enhanced fallback mock response with user data integration when OpenAI is unavailable"""
    
    # Tool-specific mock responses that follow the new standards
    mock_responses = {
        "amendes": {
            "resume": [
                "Analyser minutieusement les mentions du procès-verbal dans un délai de 5 jours (art. L121-3 Code de la route)",
                "Rassembler méthodiquement les preuves matérielles et testimoniales de l'erreur de verbalisation",
                "Rédiger une contestation juridiquement argumentée selon les dispositions du Code de procédure pénale",
                "Expédier le courrier en lettre recommandée avec accusé de réception avant l'expiration du délai de 45 jours",
                "Constituer un dossier de suivi avec copies intégrales et accusés de réception pour traçabilité",
                "Surveiller activement la réponse de l'Officier du Ministère Public dans un délai maximal de 3 mois",
                "Préparer les éventuels recours complémentaires en cas de rejet non motivé de la contestation"
            ],
            "lettre": {
                "destinataire_bloc": "Monsieur l'Officier du Ministère Public\nTribunal de Police de [Ville]\nService des Contraventions\n[Code postal] [Ville]",
                "objet": "Contestation formelle du procès-verbal n° [Numéro] - Art. L121-3 du Code de la route",
                "corps": "Monsieur l'Officier du Ministère Public,\n\nJ'ai l'honneur de porter à votre connaissance ma contestation formelle du procès-verbal n° [Numéro] dressé le [Date] à [Heure] pour [Motif] sur la voie publique sise [Lieu exact].\n\nAprès examen attentif des circonstances de fait et de droit, je conteste cette verbalisation pour les motifs juridiques suivants :\n\n[Exposé détaillé et argumenté des moyens de contestation]\n\nEn conséquence, et conformément aux dispositions légales en vigueur, je sollicite respectueusement l'annulation pure et simple de cette contravention.\n\nDans l'attente de votre décision motivée, je vous prie d'agréer, Monsieur l'Officier du Ministère Public, l'expression de ma haute considération.",
                "pj": ["Copie intégrale du procès-verbal contesté", "Photographies horodatées des lieux", "Attestations circonstanciées de témoins", "Justificatif d'identité en cours de validité"],
                "signature": "[Prénom NOM]\n[Adresse complète avec code postal]\nTél. : [Numéro de téléphone]\nFait à [Ville], le [Date]"
            },
            "checklist": [
                "Respecter impérativement le délai légal de 45 jours à compter de la réception de l'avis (art. L121-3 Code de la route)",
                "Photographier exhaustivement les lieux avec horodatage pour constitution de preuves",
                "Recueillir des témoignages écrits et signés de personnes présentes lors des faits allégués",
                "Vérifier scrupuleusement l'exactitude des mentions obligatoires du procès-verbal",
                "Conserver précieusement l'original de l'avis de contravention et tous les accusés de réception",
                "Calculer précisément les délais de prescription et de recours pour anticiper les échéances"
            ],
            "mentions": "Aide juridique automatisée – ne se substitue aucunement aux conseils personnalisés d'un avocat spécialisé. Respecter impérativement le délai de contestation de 45 jours. En cas de complexité particulière, solliciter l'assistance d'un professionnel du droit. Possibilité de recours devant le tribunal compétent en cas de rejet non motivé."
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
                "Analyser l'applicabilité de l'encadrement des loyers dans la zone géographique concernée",
                "Consulter les données officielles de loyers de référence auprès des services municipaux compétents",
                "Calculer méthodiquement l'éventuel dépassement par rapport au loyer de référence légal",
                "Constituer un dossier documentaire exhaustif avec toutes les pièces justificatives",
                "Adresser une mise en demeure formelle au bailleur en lettre recommandée avec AR",
                "Saisir la commission départementale de conciliation en cas d'échec de la négociation amiable",
                "Engager une action devant le tribunal judiciaire si la situation n'est pas régularisée"
            ],
            "lettre": {
                "destinataire_bloc": "Monsieur/Madame [Nom du bailleur]\n[Qualité : Propriétaire bailleur]\n[Adresse complète du bailleur]\n[Code postal] [Ville]",
                "objet": "Contestation formelle du montant du loyer - Logement sis [Adresse] - Encadrement des loyers",
                "corps": "Monsieur/Madame le Bailleur,\n\nJ'ai l'honneur de porter à votre connaissance ma contestation formelle concernant le montant du loyer pratiqué pour le logement que j'occupe.\n\nAprès vérification auprès des services compétents, il apparaît que le loyer mensuel dépasse manifestement les plafonds légaux en vigueur.\n\n[Exposé détaillé du calcul et du dépassement constaté]\n\nConformément aux dispositions légales en vigueur, je vous demande de procéder à la régularisation de cette situation.\n\nJe vous prie d'agréer, Monsieur/Madame le Bailleur, l'expression de ma considération distinguée.",
                "pj": ["Bail de location original", "Quittances de loyer des 12 derniers mois", "Données officielles des loyers de référence", "Justificatif d'identité en cours de validité"],
                "signature": "[Prénom NOM]\nLocataire\n[Adresse complète]\nTéléphone : [Numéro]\nFait à [Ville], le [Date]"
            },
            "checklist": [
                "Vérifier l'applicabilité de l'encadrement des loyers dans votre commune et arrondissement",
                "Consulter les données officielles des loyers de référence sur le site de la préfecture",
                "Calculer précisément le dépassement en fonction de la surface et des caractéristiques du logement",
                "Rassembler toutes les pièces justificatives nécessaires à la constitution du dossier",
                "Envoyer la mise en demeure en lettre recommandée avec accusé de réception",
                "Respecter les délais de prescription triennale pour les actions en récupération de loyers",
                "Conserver précieusement tous les documents et accusés de réception"
            ],
            "mentions": "Aide juridique automatisée – ne se substitue pas aux conseils d'un avocat spécialisé en droit immobilier. Vérifier impérativement l'applicabilité de l'encadrement des loyers dans votre commune. Possibilité de recours devant la commission de conciliation puis devant le tribunal judiciaire. Délai de prescription : 3 ans pour les actions en restitution de loyers indûment perçus."
        },
        "css": {
            "resume": [
                "Évaluer précisément l'éligibilité selon les plafonds de ressources CSS en vigueur",
                "Rassembler méthodiquement tous les justificatifs de ressources et de composition familiale",
                "Compléter rigoureusement le formulaire S3715 de demande de CSS",
                "Déposer le dossier complet auprès de la CPAM dans les délais réglementaires",
                "Assurer le suivi du traitement dans un délai maximal de 2 mois",
                "Activer la prise en charge dès notification d'acceptation pour optimiser les remboursements",
                "Programmer le renouvellement annuel avant échéance pour éviter toute interruption de droits"
            ],
            "lettre": {
                "destinataire_bloc": "Caisse Primaire d'Assurance Maladie\nService Complémentaire Santé Solidaire\n[Adresse CPAM de votre département]\n[Code postal] [Ville]",
                "objet": "Demande de Complémentaire Santé Solidaire - Art. L861-1 CSS",
                "corps": "Madame, Monsieur,\n\nJ'ai l'honneur de solliciter l'attribution de la Complémentaire Santé Solidaire pour mon foyer.\n\nSelon l'analyse de ma situation, mes ressources devraient me permettre de bénéficier de cette aide.\n\n[Détails de la situation et éligibilité]\n\nVeuillez trouver ci-joint l'ensemble des pièces justificatives requises.\n\nJe vous prie d'agréer mes salutations respectueuses.",
                "pj": ["Formulaire S3715 complété", "Justificatifs de revenus", "Justificatif de domicile", "Pièce d'identité"],
                "signature": "[Prénom NOM]\n[Adresse complète]\nN° Sécurité Sociale : [Numéro]\nLe [Date]"
            },
            "checklist": [
                "Vérifier l'éligibilité selon les plafonds de ressources annuels actualisés",
                "Télécharger le formulaire S3715 sur ameli.fr ou le retirer en agence CPAM",
                "Rassembler les justificatifs de revenus des 3 derniers mois complets",
                "Joindre les documents de composition familiale et de situation",
                "Déposer le dossier dans les 2 mois suivant un changement de situation",
                "Conserver une copie complète du dossier et l'accusé de réception",
                "Prévoir le renouvellement avant l'échéance annuelle"
            ],
            "mentions": "Aide automatisée – calculs indicatifs basés sur les plafonds en vigueur. Vérifier les montants exacts sur ameli.fr. Possibilité de recours auprès de la Commission de Recours Amiable en cas de refus. Alternative : dispositifs d'aide des collectivités locales ou mutuelles solidaires."
        }
    }
    
    # Return tool-specific mock with user data integration or generic fallback
    if tool_id in mock_responses:
        response = mock_responses[tool_id].copy()
        
        # Integrate user data for specific tools
        if tool_id == "amendes" and user_fields:
            response = integrate_amendes_data(response, user_fields)
        elif tool_id == "loyers" and user_fields:
            response = integrate_loyers_data(response, user_fields)
        elif tool_id == "css" and user_fields:
            response = integrate_css_data(response, user_fields)
        
        return response
    
    # Generic enhanced fallback for other tools
    return {
        "resume": [
            "Analyser méthodiquement votre situation juridique au regard de la réglementation applicable",
            "Constituer un dossier documentaire exhaustif avec l'ensemble des pièces justificatives pertinentes", 
            "Rédiger un courrier administratif structuré et juridiquement fondé selon les règles de l'art",
            "Expédier le courrier en lettre recommandée avec accusé de réception pour opposabilité légale",
            "Effectuer un suivi rigoureux des délais de réponse et préparer les recours éventuels",
            "Documenter chaque étape de la procédure pour assurer une traçabilité complète du dossier"
        ],
        "lettre": {
            "destinataire_bloc": "Service compétent\n[Dénomination précise du service]\n[Adresse complète]\n[Code postal] [Ville]",
            "objet": f"Demande relative à {tool_id.upper()} - Dossier n° [Référence]",
            "corps": "Madame la Directrice, Monsieur le Directeur,\n\nJ'ai l'honneur de porter à votre connaissance ma demande relative à la situation administrative exposée ci-après.\n\n[Exposé circonstancié des faits et du fondement juridique de la demande]\n\nEn conséquence, je sollicite respectueusement votre intervention pour [objet précis de la demande].\n\nDans l'attente de votre réponse dans les délais réglementaires, je vous prie d'agréer, Madame la Directrice, Monsieur le Directeur, l'expression de ma considération distinguée.",
            "pj": ["Copie certifiée conforme du document de référence", "Justificatif d'identité en cours de validité", "Pièces complémentaires selon la réglementation applicable"],
            "signature": "[Prénom NOM en majuscules]\n[Qualité/Statut si pertinent]\n[Adresse complète]\nTéléphone : [Numéro]\nCourriel : [Email]\nFait à [Ville], le [Date complète]"
        },
        "checklist": [
            "Conserver rigoureusement une copie intégrale signée de tous les documents transmis",
            "Respecter scrupuleusement les délais légaux et réglementaires applicables à votre situation", 
            "Joindre systématiquement toutes les pièces justificatives exigées par la procédure",
            "Assurer un suivi méthodique des accusés de réception et des délais de traitement",
            "Préparer les voies de recours appropriées en cas de décision défavorable",
            "Solliciter l'assistance d'un professionnel du droit en cas de complexité particulière"
        ],
        "mentions": "Aide juridique automatisée – ne se substitue aucunement aux conseils personnalisés d'un avocat spécialisé. Vérifier impérativement les délais légaux et conditions d'éligibilité applicables à votre situation particulière. Possibilité de recours gracieux puis contentieux selon la nature du litige. Documentation juridique disponible sur les sites officiels des administrations compétentes."
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

CRITIQUE PROFESSIONNELLE REQUISE - Améliore la qualité et le professionnalisme :

1. PERSONNALISATION : Intègre mieux les données utilisateur dans tous les champs (dates, noms, montants, références). Évite les formulations génériques.

2. TONALITÉ PROFESSIONNELLE : Vérifie que le langage administratif est soutenu, précis et élégant. Améliore les formules de politesse et la structure argumentative.

3. PRÉCISION JURIDIQUE : Ajoute des références légales spécifiques, calcule les délais exacts, mentionne les procédures détaillées.

4. EXHAUSTIVITÉ : Assure-toi que :
   - resume contient 5-8 étapes détaillées avec estimations temporelles
   - lettre intègre parfaitement les données fournies et utilise un vocabulaire juridique approprié
   - checklist inclut des actions expertes avec délais précis
   - mentions contient 3-5 rappels juridiques prudents avec références aux recours

5. ÉLÉGANCE RÉDACTIONNELLE : Évite les répétitions, utilise des synonymes, structure les paragraphes logiquement.

Réponds en JSON strict identique mais considérablement amélioré selon ces critères professionnels."""

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
    return get_mock_response(in_.tool_id, in_.fields)