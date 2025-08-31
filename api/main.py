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
from jinja2 import Template
import prompting

app = FastAPI(title="Outils Citoyens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
)

# Include chat router
from chat import router as chat_router
app.include_router(chat_router)

# Include legal router
from legal.router import router as legal_router
app.include_router(legal_router)

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

def enhance_response_quality(response: Dict[str, Any], user_fields: dict, tool_id: str) -> Dict[str, Any]:
    """Enhance response quality with user-centric improvements"""
    import copy
    enhanced = copy.deepcopy(response)
    
    # Ensure resume is comprehensive and reassuring
    if len(enhanced.get("resume", [])) < 6:
        # Add more helpful steps if too short
        enhanced["resume"].extend([
            "Garder confiance : vous suivez la bonne procédure et vos droits sont protégés",
            "En cas de question, ne pas hésiter à contacter les services compétents - ils sont là pour vous aider"
        ])
    
    # Enhance mentions to be more encouraging
    if "mentions" in enhanced:
        base_mentions = enhanced["mentions"]
        if "🤖" not in base_mentions:  # If not already enhanced
            enhanced["mentions"] = f"🤖 {base_mentions} 💪 Vous avez des droits légitimes, n'hésitez pas à les faire valoir avec confiance."
    
    # Personalize signature if user data available
    if "lettre" in enhanced and user_fields:
        # Try to personalize the signature block
        signature = enhanced["lettre"].get("signature", "")
        if "[" in signature and "]" in signature:
            # Replace placeholders with more helpful text
            enhanced["lettre"]["signature"] = signature.replace(
                "[Votre prénom et NOM]", "[Indiquer vos prénom et nom]"
            ).replace(
                "[Votre adresse complète]", "[Votre adresse complète]"
            )
    
    return enhanced

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

def integrate_travail_data(response: Dict[str, Any], user_fields: dict) -> Dict[str, Any]:
    """Integrate user data into travail mock response for personalization"""
    import copy
    
    personalized = copy.deepcopy(response)
    
    # Extract user data with fallbacks
    type_litige = user_fields.get("type_litige", "conflit professionnel")
    employeur = user_fields.get("employeur", "[Nom de l'employeur]")
    periode = user_fields.get("periode", "[Période concernée]")
    montant_estime = user_fields.get("montant_estime", "[Montant estimé]")
    date_licenciement = user_fields.get("date_licenciement", "[Date]")
    
    # Personalize resume based on litigation type
    if "heures" in str(type_litige).lower():
        personalized["resume"][0] = f"Rassembler les preuves des heures supplémentaires non payées chez {employeur} pour la période {periode}"
        personalized["resume"][1] = f"Calculer le montant exact des sommes dues (estimation : {montant_estime}€) selon les taux légaux"
    elif "licenciement" in str(type_litige).lower():
        personalized["resume"][0] = f"Analyser la procédure de licenciement effectuée par {employeur} le {date_licenciement}"
        personalized["resume"][1] = f"Identifier les irrégularités et violations du Code du travail dans cette procédure"
    else:
        personalized["resume"][0] = f"Analyser votre situation de {type_litige} avec l'employeur {employeur}"
        personalized["resume"][1] = f"Rassembler tous les éléments de preuve relatifs à la période {periode}"
    
    # Personalize letter
    lettre = personalized["lettre"]
    lettre["destinataire_bloc"] = f"{employeur}\nService Ressources Humaines\n[Adresse de l'entreprise]\n[Code postal et ville]"
    
    if "heures" in str(type_litige).lower():
        lettre["objet"] = f"Demande de paiement - Heures supplémentaires période {periode} - Montant estimé {montant_estime}€"
    elif "licenciement" in str(type_litige).lower():
        lettre["objet"] = f"Contestation de la procédure de licenciement du {date_licenciement} - Demande de régularisation"
    else:
        lettre["objet"] = f"Réclamation {type_litige.title()} - Période {periode}"
    
    # Customize letter body based on litigation type
    if "heures" in str(type_litige).lower():
        lettre["corps"] = f"""Monsieur le Directeur des Ressources Humaines,

J'ai l'honneur de porter à votre connaissance que des heures supplémentaires effectuées au sein de votre entreprise {employeur} n'ont pas été rémunérées conformément aux dispositions du Code du travail.

Pour la période allant de {periode}, j'ai effectué des heures supplémentaires qui n'ont pas fait l'objet d'une rémunération selon les taux majorés légalement prévus. Le montant total des sommes dues s'élève approximativement à {montant_estime}€.

Conformément aux articles L3121-33 et suivants du Code du travail, je vous demande de procéder au règlement de ces heures supplémentaires sous un délai de 30 jours.

Je vous prie d'agréer, Monsieur le Directeur, l'expression de ma considération distinguée."""
    elif "licenciement" in str(type_litige).lower():
        lettre["corps"] = f"""Monsieur le Directeur des Ressources Humaines,

Par la présente, je conteste formellement la procédure de licenciement qui m'a été notifiée le {date_licenciement} par votre entreprise {employeur}.

Cette procédure présente des irrégularités au regard des dispositions du Code du travail, notamment en matière de forme et de délais. Ces violations constituent un motif de nullité de la procédure.

Je vous demande de bien vouloir procéder à ma réintégration et à la régularisation de ma situation sous 15 jours.

Je vous prie d'agréer, Monsieur le Directeur, l'expression de ma considération distinguée."""
    else:
        lettre["corps"] = f"""Monsieur le Directeur,

Je vous informe d'un {type_litige} survenu dans le cadre de mon activité professionnelle au sein de votre entreprise {employeur}.

Pour la période {periode}, ma situation nécessite une intervention de votre part pour une résolution conforme au droit du travail et aux conventions collectives applicables.

Je sollicite un entretien dans les meilleurs délais pour examiner cette situation et trouver une solution satisfaisante.

Je vous prie d'agréer, Monsieur le Directeur, l'expression de ma considération distinguée."""
    
    # Customize pieces jointes
    if "heures" in str(type_litige).lower():
        lettre["pj"] = [f"Planning de travail détaillé pour la période {periode}", "Relevés d'heures supplémentaires", "Contrat de travail", "Convention collective applicable", "Calcul détaillé des sommes dues"]
    elif "licenciement" in str(type_litige).lower():
        lettre["pj"] = [f"Lettre de licenciement du {date_licenciement}", "Contrat de travail", "Derniers bulletins de paie", "Éléments prouvant l'irrégularité de la procédure"]
    else:
        lettre["pj"] = ["Documents relatifs au litige", "Contrat de travail", "Convention collective", "Toute correspondance pertinente"]
    
    # Personalize checklist
    if "heures" in str(type_litige).lower():
        personalized["checklist"][0] = f"Rassembler tous les justificatifs d'heures pour la période {periode} chez {employeur}"
        personalized["checklist"][1] = f"Calculer précisément les {montant_estime}€ selon les taux majorés (25% ou 50%)"
    elif "licenciement" in str(type_litige).lower():
        personalized["checklist"][0] = f"Analyser la lettre de licenciement du {date_licenciement} pour identifier les vices de procédure"
        personalized["checklist"][1] = f"Vérifier le respect des délais et formes de la procédure par {employeur}"
    
    return personalized

def integrate_caf_data(response: Dict[str, Any], user_fields: dict) -> Dict[str, Any]:
    """Integrate user data into CAF mock response for personalization"""
    import copy
    
    personalized = copy.deepcopy(response)
    
    # Extract user data with fallbacks
    numero_allocataire = user_fields.get("numero_allocataire", "[Numéro allocataire]")
    type_courrier = user_fields.get("type_courrier", "réclamation")
    montant = user_fields.get("montant", "[Montant]")
    periode = user_fields.get("periode", "[Période]")
    motif = user_fields.get("motif", "[Motif du litige]")
    
    # Personalize resume
    personalized["resume"][0] = f"Analyser le courrier CAF concernant votre dossier allocataire n° {numero_allocataire}"
    personalized["resume"][1] = f"Contester la décision relative au {type_courrier} de {montant}€ pour la période {periode}"
    
    # Personalize letter
    lettre = personalized["lettre"]
    lettre["destinataire_bloc"] = "Caisse d'Allocations Familiales\nService Contentieux et Recours\n[Adresse CAF de votre département]\n[Code postal] [Ville]"
    
    if "indu" in str(type_courrier).lower():
        lettre["objet"] = f"Recours gracieux - Indû n° allocataire {numero_allocataire} - Montant {montant}€ - Période {periode}"
    elif "suspension" in str(type_courrier).lower():
        lettre["objet"] = f"Contestation suspension allocations - N° {numero_allocataire} - Période {periode}"
    else:
        lettre["objet"] = f"Recours gracieux - {type_courrier.title()} - N° allocataire {numero_allocataire}"
    
    # Customize letter body
    lettre["corps"] = f"""Madame, Monsieur,

Allocataire sous le numéro {numero_allocataire}, je vous adresse la présente afin de contester formellement votre décision concernant un {type_courrier} d'un montant de {montant}€ pour la période {periode}.

Après examen attentif de votre courrier, je conteste cette décision pour les motifs suivants :

[Exposé détaillé de votre situation et des arguments juridiques]

Cette décision me semble erronée au regard de ma situation réelle et des droits qui me sont reconnus par le Code de la sécurité sociale.

Conformément à l'article R142-1 du Code de la sécurité sociale, je sollicite un recours gracieux et vous demande de bien vouloir réexaminer mon dossier.

Dans l'attente de votre réponse dans un délai de 2 mois, je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations respectueuses."""
    
    # Customize pieces jointes
    lettre["pj"] = [f"Courrier CAF contesté concernant le {type_courrier}", f"Justificatifs de situation pour la période {periode}", "Relevés de compte bancaire", "Tout document prouvant la régularité de ma situation", "Copie pièce d'identité"]
    
    # Personalize checklist
    personalized["checklist"][0] = f"Respecter le délai de recours de 2 mois après réception du courrier CAF"
    personalized["checklist"][1] = f"Rassembler tous justificatifs prouvant l'erreur de la CAF sur le {type_courrier} de {montant}€"
    personalized["checklist"][2] = f"Envoyer le recours en LRAR à la CAF avec numéro allocataire {numero_allocataire}"
    
    return personalized

def integrate_energie_data(response: Dict[str, Any], user_fields: dict) -> Dict[str, Any]:
    """Integrate user data into energie mock response for personalization"""
    import copy
    
    personalized = copy.deepcopy(response)
    
    # Extract user data with fallbacks
    fournisseur = user_fields.get("fournisseur", "[Fournisseur d'énergie]")
    facture_numero = user_fields.get("facture_numero", "[Numéro de facture]")
    montant_conteste = user_fields.get("montant_conteste", "[Montant contesté]")
    periode = user_fields.get("periode", "[Période de facturation]")
    motif_contestation = user_fields.get("motif_contestation", "facture anormalement élevée")
    
    # Personalize resume
    personalized["resume"][0] = f"Analyser la facture {fournisseur} n° {facture_numero} d'un montant de {montant_conteste}€"
    personalized["resume"][1] = f"Identifier les éléments anormaux ou erronés dans cette facturation {fournisseur}"
    personalized["resume"][2] = f"Contester formellement auprès de {fournisseur} le montant de {montant_conteste}€"
    
    # Personalize letter
    lettre = personalized["lettre"]
    lettre["destinataire_bloc"] = f"{fournisseur}\nService Clientèle - Réclamations\n[Adresse du fournisseur]\n[Code postal] [Ville]"
    lettre["objet"] = f"Contestation facture n° {facture_numero} - Montant {montant_conteste}€ - {motif_contestation}"
    
    lettre["corps"] = f"""Madame, Monsieur,

Client de votre société {fournisseur}, je vous adresse la présente pour contester formellement la facture n° {facture_numero} d'un montant de {montant_conteste}€ pour la période {periode}.

Cette facturation me semble erronée pour les motifs suivants : {motif_contestation}.

Après vérification de mes relevés de consommation et comparaison avec les périodes précédentes, je constate une anomalie manifeste qui nécessite une révision de cette facture.

Conformément au Code de l'énergie et aux conditions générales de vente, je vous demande de procéder à une vérification de votre comptage et à une rectification de cette facture.

Je vous prie d'agréer, Madame, Monsieur, l'expression de ma considération distinguée."""
    
    # Customize pieces jointes
    lettre["pj"] = [f"Copie de la facture contestée n° {facture_numero}", "Relevés de consommation antérieurs pour comparaison", "Photos des index de compteurs", f"Historique des factures {fournisseur}", "Justificatif d'identité"]
    
    # Personalize checklist
    personalized["checklist"][0] = f"Conserver la facture originale {fournisseur} n° {facture_numero} et tous les documents"
    personalized["checklist"][1] = f"Relever les index de compteurs et photographier pour preuve"
    personalized["checklist"][2] = f"Envoyer la contestation en LRAR à {fournisseur} dans les 2 mois"
    
    return personalized

def integrate_aides_data(response: Dict[str, Any], user_fields: dict) -> Dict[str, Any]:
    """Integrate user data into aides mock response for personalization"""
    import copy
    
    personalized = copy.deepcopy(response)
    
    # Extract user data with fallbacks
    situation = user_fields.get("situation", "[Situation]")
    revenus = user_fields.get("revenus", "[Revenus]")
    foyer = user_fields.get("foyer", "[Composition foyer]")
    ville = user_fields.get("ville", "[Ville]")
    aide_demandee = user_fields.get("aide_demandee", "RSA")
    
    # Personalize resume
    personalized["resume"][0] = f"Analyser votre éligibilité aux aides avec {revenus}€ de revenus pour {foyer} personne(s) en situation de {situation}"
    personalized["resume"][1] = f"Identifier les aides disponibles à {ville} selon votre profil"
    personalized["resume"][2] = f"Constituer un dossier de demande d'{aide_demandee} adapté à votre situation"
    
    # Personalize letter
    lettre = personalized["lettre"]
    
    if aide_demandee.upper() == "RSA":
        lettre["destinataire_bloc"] = f"Conseil Départemental de {ville}\nService RSA\n[Adresse du Conseil Départemental]\n[Code postal] [Ville]"
        lettre["objet"] = f"Demande de RSA - Foyer {foyer} personne(s) - Revenus {revenus}€ - Situation {situation}"
    else:
        lettre["destinataire_bloc"] = f"Service des Aides Sociales\nMairie de {ville}\n[Adresse de la mairie]\n[Code postal] [Ville]"
        lettre["objet"] = f"Demande d'aide sociale - {aide_demandee} - Foyer {foyer} personne(s)"
    
    lettre["corps"] = f"""Madame, Monsieur,

Je sollicite par la présente l'attribution de l'aide {aide_demandee} pour mon foyer composé de {foyer} personne(s).

Ma situation actuelle : {situation}, avec des revenus mensuels de {revenus}€, me place dans une situation de précarité qui justifie cette demande d'aide.

Résidant à {ville}, je souhaite bénéficier des dispositifs d'aide sociale auxquels ma situation me donne droit selon la réglementation en vigueur.

Vous trouverez ci-joint l'ensemble des pièces justificatives nécessaires à l'examen de ma demande.

Dans l'attente de votre réponse, je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations respectueuses."""
    
    # Customize pieces jointes based on aid type
    base_pj = ["Justificatifs de revenus des 3 derniers mois", "Justificatif de domicile récent", "Pièce d'identité en cours de validité", f"Justificatifs de situation ({situation})"]
    
    if aide_demandee.upper() == "RSA":
        lettre["pj"] = base_pj + ["Attestation Pôle emploi (si applicable)", "RIB", "Formulaire de demande RSA complété"]
    else:
        lettre["pj"] = base_pj + ["Devis ou factures selon l'aide demandée", "Attestation de situation familiale"]
    
    # Personalize checklist
    personalized["checklist"][0] = f"Vérifier l'éligibilité à l'{aide_demandee} avec {revenus}€ pour {foyer} personne(s)"
    personalized["checklist"][1] = f"Se renseigner sur les aides spécifiques disponibles à {ville}"
    personalized["checklist"][2] = f"Déposer le dossier complet au service compétent de {ville}"
    
    return personalized

def integrate_sante_data(response: Dict[str, Any], user_fields: dict) -> Dict[str, Any]:
    """Integrate user data into sante mock response for personalization"""
    import copy
    
    personalized = copy.deepcopy(response)
    
    # Extract user data with fallbacks
    type_demande = user_fields.get("type_demande", "accès aux soins")
    ville = user_fields.get("ville", "[Ville]")
    urgence = user_fields.get("urgence", "non")
    probleme = user_fields.get("probleme", "difficulté d'accès aux soins")
    medecin_souhaite = user_fields.get("medecin_souhaite", "généraliste")
    
    # Personalize resume
    if "urgence" in str(urgence).lower() or urgence == "oui":
        personalized["resume"][0] = f"URGENT - Contacter immédiatement le 15 (SAMU) ou vous rendre aux urgences de {ville}"
        personalized["resume"][1] = f"Si non urgent, rechercher un médecin {medecin_souhaite} disponible rapidement à {ville}"
    else:
        personalized["resume"][0] = f"Rechercher un médecin {medecin_souhaite} disponible à {ville} dans les 6 jours (délai légal)"
        personalized["resume"][1] = f"Utiliser les plateformes de téléconsultation si pas de médecin disponible à {ville}"
    
    # Personalize letter
    lettre = personalized["lettre"]
    
    if "medecin_traitant" in str(type_demande).lower():
        lettre["destinataire_bloc"] = f"Ordre des Médecins de {ville}\n[Adresse départementale]\n[Code postal] {ville}"
        lettre["objet"] = f"Demande d'aide pour trouver un médecin traitant - Résidence {ville}"
    else:
        lettre["destinataire_bloc"] = f"Centre de soins de {ville}\n[Adresse du centre]\n[Code postal] {ville}"
        lettre["objet"] = f"Demande de {type_demande} - {probleme} - Résidence {ville}"
    
    lettre["corps"] = f"""Madame, Monsieur,

Résidant à {ville}, je rencontre des difficultés pour {type_demande} : {probleme}.

{"Cette situation revêt un caractère urgent nécessitant une prise en charge rapide." if urgence == "oui" else "Je sollicite votre aide pour accéder aux soins dans les délais légaux de 6 jours."}

Je recherche un médecin {medecin_souhaite} disponible pour assurer un suivi médical régulier et de qualité selon mes besoins de santé.

Pourriez-vous m'orienter vers les professionnels de santé disponibles à {ville} ou les dispositifs d'aide existants ?

Je vous remercie de votre aide et vous prie d'agréer, Madame, Monsieur, l'expression de ma considération distinguée."""
    
    # Customize pieces jointes
    lettre["pj"] = [f"Justificatif de domicile à {ville}", "Carte Vitale ou attestation Sécurité Sociale", "Ordonnances médicales récentes (si applicable)", "Courriers médicaux antérieurs (si pertinents)"]
    
    # Personalize checklist
    personalized["checklist"][0] = f"Contacter votre CPAM ou le 3646 pour obtenir la liste des médecins à {ville}"
    personalized["checklist"][1] = f"Consulter doctolib.fr ou autres plateformes pour {ville}"
    if urgence == "oui":
        personalized["checklist"][2] = f"En cas d'urgence : 15 (SAMU), 112 (urgences européennes) ou urgences de {ville}"
    
    return personalized

def integrate_usure_data(response: Dict[str, Any], user_fields: dict) -> Dict[str, Any]:
    """Integrate user data into usure mock response for personalization"""
    import copy
    
    personalized = copy.deepcopy(response)
    
    # Extract user data with fallbacks
    banque = user_fields.get("banque", "[Nom de la banque]")
    taux_pratique = user_fields.get("taux_pratique", "[Taux pratiqué]")
    montant_pret = user_fields.get("montant_pret", "[Montant du prêt]")
    type_credit = user_fields.get("type_credit", "crédit à la consommation")
    date_signature = user_fields.get("date_signature", "[Date de signature]")
    
    # Calculate potential usury
    taux_usure_legal = "21%" # Simplified for demonstration
    depassement = "Oui" if isinstance(taux_pratique, (int, float, str)) and str(taux_pratique).replace("%", "").replace(",", ".").replace(" ", "").isdigit() and float(str(taux_pratique).replace("%", "").replace(",", ".")) > 21 else "À vérifier"
    
    # Personalize resume
    personalized["resume"][0] = f"Vérifier si le taux de {taux_pratique}% pratiqué par {banque} dépasse le seuil d'usure légal"
    personalized["resume"][1] = f"Calculer le TEG réel du {type_credit} de {montant_pret}€ signé le {date_signature}"
    personalized["resume"][2] = f"Contester auprès de {banque} le dépassement du taux d'usure ({depassement})"
    
    # Personalize letter
    lettre = personalized["lettre"]
    lettre["destinataire_bloc"] = f"{banque}\nService Juridique - Contentieux\n[Adresse de l'agence ou siège]\n[Code postal] [Ville]"
    lettre["objet"] = f"Contestation taux d'usure - {type_credit.title()} du {date_signature} - TEG {taux_pratique}%"
    
    lettre["corps"] = f"""Madame, Monsieur,

Par la présente, je conteste formellement le taux d'intérêt appliqué au {type_credit} que j'ai souscrit auprès de votre établissement {banque} le {date_signature} pour un montant de {montant_pret}€.

Le taux effectif global (TEG) de {taux_pratique}% appliqué à ce crédit dépasse manifestement le taux d'usure légal fixé par la Banque de France (actuellement {taux_usure_legal} pour ce type de crédit).

Cette situation constitue une infraction à l'article L314-6 du Code de la consommation et rend le contrat de crédit partiellement nul.

Je vous demande de procéder immédiatement à la rectification de ce taux et au remboursement des intérêts indûment perçus.

Dans l'attente de votre réponse sous 30 jours, je vous prie d'agréer, Madame, Monsieur, l'expression de ma considération distinguée."""
    
    # Customize pieces jointes
    lettre["pj"] = [f"Contrat de crédit {banque} du {date_signature}", f"Tableaux d'amortissement montrant le TEG de {taux_pratique}%", "Taux d'usure Banque de France en vigueur", "Calcul détaillé du dépassement", "Justificatif d'identité"]
    
    # Personalize checklist
    personalized["checklist"][0] = f"Consulter les taux d'usure officiels sur banque-france.fr pour votre type de crédit"
    personalized["checklist"][1] = f"Calculer précisément le TEG de votre {type_credit} chez {banque}"
    personalized["checklist"][2] = f"Conserver tous les documents du crédit {banque} de {montant_pret}€"
    
    return personalized

def integrate_expulsions_data(response: Dict[str, Any], user_fields: dict) -> Dict[str, Any]:
    """Integrate user data into expulsions mock response for personalization"""
    import copy
    from datetime import datetime, timedelta
    
    personalized = copy.deepcopy(response)
    
    # Extract user data with fallbacks
    type_expulsion = user_fields.get("type", "locatif")
    date_assignation = user_fields.get("date_assignation", "[Date d'assignation]")
    bailleur = user_fields.get("bailleur", "[Nom du bailleur]")
    motif = user_fields.get("motif", "loyers impayés")
    montant_dette = user_fields.get("montant_dette", "[Montant de la dette]")
    
    # Check if we're in winter truce period
    today = datetime.now()
    winter_start = datetime(today.year, 11, 1)  # November 1
    winter_end = datetime(today.year + 1, 3, 31)  # March 31 next year
    if today.month < 4:  # January to March
        winter_end = datetime(today.year, 3, 31)
    in_winter_truce = winter_start <= today <= winter_end
    
    # Personalize resume
    personalized["resume"][0] = f"{'PROTECTION : Vous êtes en trêve hivernale jusqu\'au 31 mars - l\'expulsion est suspendue' if in_winter_truce else 'Analyser l\'assignation du ' + str(date_assignation) + ' pour ' + str(motif)}"
    personalized["resume"][1] = f"Préparer votre défense contre {bailleur} pour une dette de {montant_dette}€"
    personalized["resume"][2] = f"Saisir le Fonds de Solidarité Logement (FSL) et la commission de médiation"
    
    # Personalize letter
    lettre = personalized["lettre"]
    
    if "coupure" in str(type_expulsion).lower():
        lettre["destinataire_bloc"] = f"[Fournisseur d'énergie]\nService Recouvrement\n[Adresse du fournisseur]\n[Code postal] [Ville]"
        lettre["objet"] = f"Opposition à coupure illégale - {'Période de trêve hivernale' if in_winter_truce else 'Demande de délais'}"
    else:
        lettre["destinataire_bloc"] = f"{bailleur}\n[Qualité du bailleur]\n[Adresse du bailleur]\n[Code postal] [Ville]"
        lettre["objet"] = f"Demande de délais de paiement - {motif} - Assignation du {date_assignation}"
    
    lettre["corps"] = f"""Madame, Monsieur,

Suite à {"l'assignation en expulsion" if "assignation" in str(date_assignation) else "votre courrier"} du {date_assignation} concernant {motif} d'un montant de {montant_dette}€, je vous adresse la présente.

{"Je vous rappelle que nous sommes en période de trêve hivernale du 1er novembre au 31 mars, période durant laquelle toute expulsion locative est interdite sauf exceptions très limitées." if in_winter_truce else "Ma situation financière actuelle ne me permet pas de régler immédiatement cette dette."}

Je sollicite par la présente un échéancier de paiement qui me permettrait de régulariser ma situation progressivement tout en conservant mon logement.

Je suis également en démarche auprès du Fonds de Solidarité Logement (FSL) pour obtenir une aide financière.

Je vous remercie de votre compréhension et vous prie d'agréer, Madame, Monsieur, l'expression de ma considération distinguée."""
    
    # Customize pieces jointes
    lettre["pj"] = [f"Copie de l'assignation du {date_assignation}", "Justificatifs de revenus actuels", "Demande d'aide FSL en cours", "Proposition d'échéancier de paiement", "Justificatif de domicile"]
    
    # Personalize checklist
    if in_winter_truce:
        personalized["checklist"][0] = f"PROTECTION ACTIVE : Trêve hivernale jusqu'au 31 mars - expulsion interdite"
    personalized["checklist"][1] = f"Déposer rapidement une demande FSL dans votre département"
    personalized["checklist"][2] = f"Préparer votre défense pour l'audience concernant la dette de {montant_dette}€"
    
    return personalized

def integrate_ecole_data(response: Dict[str, Any], user_fields: dict) -> Dict[str, Any]:
    """Integrate user data into ecole mock response for personalization"""
    import copy
    
    personalized = copy.deepcopy(response)
    
    # Extract user data with fallbacks
    etablissement = user_fields.get("etablissement", "[Nom de l'établissement]")
    type_harcelement = user_fields.get("type_harcelement", "harcèlement scolaire")
    enfant_nom = user_fields.get("enfant_nom", "[Prénom de l'enfant]")
    classe = user_fields.get("classe", "[Classe]")
    gravite = user_fields.get("gravite", "modérée")
    
    # Personalize resume
    personalized["resume"][0] = f"URGENT - Signaler immédiatement le {type_harcelement} contre {enfant_nom} au chef d'établissement {etablissement}"
    personalized["resume"][1] = f"Contacter le 3020 (numéro national anti-harcèlement) pour accompagnement spécialisé"
    personalized["resume"][2] = f"Constituer un dossier de preuves du {type_harcelement} en classe de {classe}"
    
    # Personalize letter
    lettre = personalized["lettre"]
    lettre["destinataire_bloc"] = f"Monsieur/Madame le Chef d'Établissement\n{etablissement}\n[Adresse de l'établissement]\n[Code postal] [Ville]"
    lettre["objet"] = f"SIGNALEMENT URGENT - {type_harcelement.title()} - Élève {enfant_nom} - Classe {classe}"
    
    lettre["corps"] = f"""Monsieur/Madame le Chef d'Établissement,

Je porte à votre connaissance avec la plus grande urgence que mon enfant {enfant_nom}, élève en classe de {classe} dans votre établissement {etablissement}, est victime de {type_harcelement}.

Les faits se caractérisent par {"des violences physiques répétées nécessitant une intervention immédiate" if "physique" in str(type_harcelement).lower() else "des actes répétés de nature à porter atteinte à sa dignité et à son bien-être scolaire"}.

Cette situation, d'une gravité {"majeure" if gravite == "grave" else gravite}, nécessite la mise en œuvre immédiate du protocole de prise en charge du harcèlement scolaire prévu par l'Éducation Nationale.

Je sollicite un rendez-vous en urgence pour mettre en place les mesures de protection et d'accompagnement nécessaires.

Dans l'attente de votre réaction rapide, je vous prie d'agréer, Monsieur/Madame le Chef d'Établissement, l'expression de ma considération."""
    
    # Customize pieces jointes
    lettre["pj"] = [f"Témoignages et preuves du {type_harcelement} contre {enfant_nom}", "Certificats médicaux ou psychologiques (si applicable)", f"Correspondances antérieures avec {etablissement}", "Photos ou captures d'écran (si disponibles)"]
    
    # Personalize checklist
    personalized["checklist"][0] = f"Contacter immédiatement le 3020 pour signaler le {type_harcelement} contre {enfant_nom}"
    personalized["checklist"][1] = f"Demander un rendez-vous urgent avec la direction de {etablissement}"
    personalized["checklist"][2] = f"Documenter tous les faits de {type_harcelement} avec dates et témoins"
    if gravite == "grave":
        personalized["checklist"][3] = f"Porter plainte au commissariat si violences physiques avérées"
    
    return personalized

def integrate_decodeur_data(response: Dict[str, Any], user_fields: dict) -> Dict[str, Any]:
    """Integrate user data into decodeur mock response for personalization"""
    import copy
    
    personalized = copy.deepcopy(response)
    
    # Extract user data with fallbacks
    expediteur = user_fields.get("expediteur", "[Expéditeur]")
    objet_courrier = user_fields.get("objet_courrier", "[Objet du courrier]")
    date_courrier = user_fields.get("date_courrier", "[Date du courrier]")
    contenu = user_fields.get("contenu", "[Contenu principal]")
    delai_mentionne = user_fields.get("delai_mentionne", "[Délai]")
    
    # Personalize resume
    personalized["resume"][0] = f"Analyser en détail le courrier de {expediteur} du {date_courrier} concernant : {objet_courrier}"
    personalized["resume"][1] = f"Identifier vos obligations et droits suite à ce courrier de {expediteur}"
    personalized["resume"][2] = f"Respecter le délai de {delai_mentionne} pour votre réponse (si applicable)"
    
    # Personalize letter
    lettre = personalized["lettre"]
    lettre["destinataire_bloc"] = f"{expediteur}\n[Service expéditeur]\n[Adresse de l'organisme]\n[Code postal] [Ville]"
    lettre["objet"] = f"Réponse à votre courrier du {date_courrier} - {objet_courrier}"
    
    lettre["corps"] = f"""Madame, Monsieur,

J'ai bien reçu votre courrier du {date_courrier} concernant {objet_courrier}.

Après examen attentif de votre demande, je vous apporte les éléments de réponse suivants :

[Votre réponse détaillée selon le contenu du courrier reçu]

{"Je respecte le délai de " + str(delai_mentionne) + " que vous avez fixé pour cette réponse." if delai_mentionne != "[Délai]" else "Je vous réponds dans les meilleurs délais comme demandé."}

Je me tiens à votre disposition pour tout complément d'information nécessaire.

Je vous prie d'agréer, Madame, Monsieur, l'expression de ma considération distinguée."""
    
    # Customize pieces jointes
    lettre["pj"] = [f"Copie du courrier {expediteur} du {date_courrier}", "Documents justificatifs demandés", "Pièce d'identité (si requise)", "Tout document pertinent selon la demande"]
    
    # Personalize checklist
    personalized["checklist"][0] = f"Conserver l'original du courrier {expediteur} et en faire des copies"
    personalized["checklist"][1] = f"Respecter impérativement le délai de {delai_mentionne} mentionné"
    personalized["checklist"][2] = f"Rassembler tous les documents demandés par {expediteur}"
    
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
                "Bonne nouvelle : vérifier votre éligibilité CSS selon vos revenus - vous pourriez être surpris(e) des économies possibles !",
                "Rassembler tranquillement vos justificatifs - on vous guide pour ne rien oublier",
                "Remplir le formulaire S3715 sans stress - il est plus simple qu'il n'y paraît",
                "Déposer votre dossier à la CPAM - ils sont là pour vous aider, n'hésitez pas à demander conseil",
                "Suivre sereinement le traitement (2 mois maximum) - la CPAM a l'obligation de vous répondre",
                "Dès l'accord, votre CSS fonctionne immédiatement - fini les frais médicaux qui plombent le budget !",
                "Programmer le renouvellement dans un an - un simple rappel et vous êtes tranquille",
                "Profiter de votre protection santé - vous l'avez mérité et c'est votre droit !"
            ],
            "lettre": {
                "destinataire_bloc": "Caisse Primaire d'Assurance Maladie\nService Complémentaire Santé Solidaire\n[Adresse CPAM de votre département]\n[Code postal] [Ville]",
                "objet": "Demande de Complémentaire Santé Solidaire - Situation [situation spécifique]",
                "corps": "Madame, Monsieur,\n\nJ'ai l'honneur de solliciter l'attribution de la Complémentaire Santé Solidaire pour mon foyer.\n\nMa situation actuelle me permet de prétendre à cette aide précieuse qui m'assurerait un accès aux soins sans frais supplémentaires.\n\n[Ici sera intégrée votre situation personnelle selon vos données]\n\nCette demande s'inscrit dans le cadre de la solidarité nationale pour l'accès aux soins, et j'espère que mon dossier recevra un accueil favorable.\n\nVous trouverez ci-joint l'ensemble des pièces justificatives requises. Je me tiens à votre disposition pour tout complément d'information.\n\nJe vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations respectueuses.",
                "pj": ["Formulaire S3715 dûment complété et signé", "Justificatifs de revenus des 3 derniers mois", "Justificatif de domicile récent", "Copie de pièce d'identité", "Attestation de situation (si applicable)", "RIB pour les remboursements"],
                "signature": "[Votre prénom et NOM]\n[Votre adresse complète]\n[Code postal et ville]\nN° Sécurité Sociale : [Votre numéro]\nTéléphone : [Votre numéro]\nFait à [Votre ville], le [Date du jour]"
            },
            "checklist": [
                "✅ Calculer votre éligibilité précise selon vos revenus annuels - utilisez le simulateur ameli.fr si besoin",
                "📋 Récupérer le formulaire S3715 sur ameli.fr ou dans votre agence CPAM (accueil toujours disponible)",
                "💼 Rassembler vos justificatifs de revenus récents - même modestes, ils prouvent vos droits",
                "🏠 Joindre un justificatif de domicile récent - facture, quittance, ou attestation d'hébergement",
                "📮 Déposer rapidement votre dossier complet - plus vite c'est fait, plus vite vous êtes protégé(e)",
                "📁 Conserver précieusement vos copies et l'accusé de réception - c'est votre sécurité",
                "⏰ Noter le délai de 2 mois pour la réponse - et n'hésitez pas à relancer si besoin",
                "🔄 Prévoir le renouvellement annuel à l'avance - un courrier vous le rappellera"
            ],
            "mentions": "🤖 Cette aide automatisée évalue vos droits selon la législation en vigueur. 💰 La CSS peut vous faire économiser des centaines d'euros par an en frais de santé. ⚖️ En cas de refus, vous avez 2 mois pour faire un recours auprès de la CRA. 🏥 Avec la CSS, tous vos soins courants sont pris en charge sans avance de frais. 💪 N'hésitez pas à faire valoir vos droits - c'est fait pour vous aider ! 📞 Votre CPAM peut vous renseigner : ils sont là pour ça."
        },
        "caf": {
            "resume": [
                "Analyser le courrier CAF reçu pour identifier précisément votre situation et vos droits",
                "Rassembler tous les justificatifs prouvant l'erreur ou l'irrégularité de la décision CAF",
                "Rédiger un recours gracieux argumenté dans le délai de 2 mois suivant la notification",
                "Envoyer votre contestation en LRAR à la CAF avec votre numéro d'allocataire",
                "Suivre votre recours et relancer la CAF si nécessaire après 2 mois",
                "Préparer un éventuel recours devant la CRA en cas de rejet du recours gracieux"
            ],
            "lettre": {
                "destinataire_bloc": "Caisse d'Allocations Familiales\nService Contentieux et Recours\n[Adresse CAF de votre département]\n[Code postal] [Ville]",
                "objet": "Recours gracieux - Numéro allocataire [N° allocataire]",
                "corps": "Madame, Monsieur,\n\nAllocataire sous le numéro [N° allocataire], je vous adresse la présente afin de contester votre décision.\n\nAprès examen de votre courrier, je conteste cette décision pour les motifs suivants :\n\n[Exposé de votre situation et arguments]\n\nConformément au Code de la sécurité sociale, je sollicite un recours gracieux et vous demande de réexaminer mon dossier.\n\nJe vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations respectueuses.",
                "pj": ["Courrier CAF contesté", "Justificatifs de situation", "Pièce d'identité", "Numéro allocataire"],
                "signature": "[Prénom NOM]\n[Adresse]\nAllocataire n° [N° allocataire]\nLe [Date]"
            },
            "checklist": [
                "Respecter le délai de recours de 2 mois après réception du courrier CAF",
                "Rassembler tous justificatifs prouvant l'erreur de la CAF",
                "Envoyer le recours en LRAR avec numéro allocataire",
                "Conserver copies et accusés de réception"
            ],
            "mentions": "Aide automatisée – ne remplace pas un conseil d'avocat. Délai de recours : 2 mois. Possibilité de saisir la CRA en cas d'échec."
        },
        "energie": {
            "resume": [
                "Analyser la facture d'énergie anormalement élevée pour identifier les éléments contestables",
                "Relever et photographier les index de compteurs pour constitution de preuves",
                "Comparer avec l'historique de consommation des périodes précédentes",
                "Contester formellement auprès du fournisseur dans le délai de 2 mois",
                "Demander une vérification du comptage et une rectification de facturation",
                "Saisir le médiateur de l'énergie en cas d'échec de la contestation amiable"
            ],
            "lettre": {
                "destinataire_bloc": "[Fournisseur d'énergie]\nService Clientèle - Réclamations\n[Adresse du fournisseur]\n[Code postal] [Ville]",
                "objet": "Contestation facture - Facturation anormalement élevée",
                "corps": "Madame, Monsieur,\n\nClient de votre société, je conteste la facture reçue qui présente une consommation anormalement élevée.\n\nAprès vérification, cette facturation semble erronée par rapport à ma consommation habituelle.\n\nJe vous demande de procéder à une vérification et rectification.\n\nJe vous prie d'agréer, Madame, Monsieur, l'expression de ma considération distinguée.",
                "pj": ["Facture contestée", "Relevés antérieurs", "Photos index compteurs", "Historique factures"],
                "signature": "[Prénom NOM]\n[Adresse]\nN° client : [Numéro]\nLe [Date]"
            },
            "checklist": [
                "Conserver la facture originale et tous documents",
                "Relever et photographier les index de compteurs",
                "Envoyer la contestation en LRAR dans les 2 mois",
                "Préparer le recours au médiateur si nécessaire"
            ],
            "mentions": "Aide automatisée – ne remplace pas un conseil d'avocat. Délai de contestation : 2 mois. Recours possible au médiateur de l'énergie."
        },
        "aides": {
            "resume": [
                "Analyser votre situation pour identifier toutes les aides auxquelles vous pouvez prétendre",
                "Calculer votre éligibilité selon vos revenus et composition familiale",
                "Constituer un dossier complet avec tous les justificatifs nécessaires",
                "Déposer les demandes auprès des organismes compétents (CAF, Conseil Départemental, etc.)",
                "Suivre le traitement de vos demandes et relancer si nécessaire",
                "Faire valoir vos droits en cas de refus non justifié"
            ],
            "lettre": {
                "destinataire_bloc": "Service des Aides Sociales\n[Organisme compétent]\n[Adresse]\n[Code postal] [Ville]",
                "objet": "Demande d'aide sociale",
                "corps": "Madame, Monsieur,\n\nJe sollicite l'attribution d'une aide sociale compte tenu de ma situation.\n\nMa situation me place dans une précarité qui justifie cette demande selon la réglementation.\n\nVous trouverez ci-joint les pièces justificatives nécessaires.\n\nJe vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations respectueuses.",
                "pj": ["Justificatifs de revenus", "Justificatif de domicile", "Pièce d'identité", "Justificatifs de situation"],
                "signature": "[Prénom NOM]\n[Adresse]\nLe [Date]"
            },
            "checklist": [
                "Vérifier l'éligibilité aux différentes aides selon vos revenus",
                "Rassembler tous les justificatifs demandés",
                "Déposer les dossiers dans les délais",
                "Suivre les réponses et faire les recours si nécessaire"
            ],
            "mentions": "Aide automatisée – ne remplace pas un conseil d'assistant social. Délais variables selon les aides. Recours possibles en cas de refus."
        },
        "sante": {
            "resume": [
                "Identifier vos besoins de santé urgents ou non urgents selon votre situation",
                "Rechercher un médecin disponible dans les délais légaux (6 jours maximum)",
                "Utiliser les plateformes de téléconsultation si accès difficile",
                "Contacter les services d'urgence si situation critique (15, 112)",
                "Faire valoir vos droits à l'accès aux soins dans votre secteur géographique",
                "Solliciter l'aide des organismes compétents si difficultés persistantes"
            ],
            "lettre": {
                "destinataire_bloc": "Centre de soins\n[Adresse du centre]\n[Code postal] [Ville]",
                "objet": "Demande d'accès aux soins",
                "corps": "Madame, Monsieur,\n\nJe rencontre des difficultés pour accéder aux soins dans ma région.\n\nJe sollicite votre aide pour être orienté(e) vers les professionnels disponibles.\n\nJe vous remercie de votre aide.\n\nJe vous prie d'agréer, Madame, Monsieur, l'expression de ma considération distinguée.",
                "pj": ["Justificatif de domicile", "Carte Vitale", "Ordonnances récentes"],
                "signature": "[Prénom NOM]\n[Adresse]\nLe [Date]"
            },
            "checklist": [
                "Contacter votre CPAM pour obtenir la liste des médecins",
                "Consulter les plateformes en ligne (Doctolib, etc.)",
                "En urgence : composer le 15 (SAMU) ou 112",
                "Faire valoir le délai légal de 6 jours"
            ],
            "mentions": "Aide automatisée – ne remplace pas un conseil médical. En urgence : 15 ou 112. Délai légal d'accès aux soins : 6 jours."
        },
        "usure": {
            "resume": [
                "Vérifier si le taux d'intérêt de votre crédit dépasse le seuil d'usure légal",
                "Calculer précisément le TEG et comparer aux taux Banque de France",
                "Rassembler tous les documents du contrat de crédit litigieux",
                "Contester auprès de la banque le dépassement du taux d'usure",
                "Demander le remboursement des intérêts indûment perçus",
                "Saisir l'ACPR ou la Banque de France en cas d'échec"
            ],
            "lettre": {
                "destinataire_bloc": "[Banque]\nService Juridique\n[Adresse]\n[Code postal] [Ville]",
                "objet": "Contestation taux d'usure - Crédit",
                "corps": "Madame, Monsieur,\n\nJe conteste le taux d'intérêt appliqué à mon crédit qui dépasse le taux d'usure légal.\n\nCette situation constitue une infraction au Code de la consommation.\n\nJe demande la rectification immédiate et le remboursement des intérêts indus.\n\nJe vous prie d'agréer, Madame, Monsieur, l'expression de ma considération distinguée.",
                "pj": ["Contrat de crédit", "Tableaux d'amortissement", "Taux d'usure Banque de France"],
                "signature": "[Prénom NOM]\n[Adresse]\nLe [Date]"
            },
            "checklist": [
                "Consulter les taux d'usure sur banque-france.fr",
                "Calculer précisément le TEG de votre crédit",
                "Conserver tous documents du crédit",
                "Préparer recours ACPR si échec"
            ],
            "mentions": "Aide automatisée – ne remplace pas un conseil d'avocat. Vérifier taux d'usure Banque de France. Recours ACPR possible."
        },
        "expulsions": {
            "resume": [
                "Vérifier si vous êtes en période de trêve hivernale (protection renforcée)",
                "Analyser la procédure d'expulsion pour identifier les irrégularités",
                "Saisir le Fonds de Solidarité Logement (FSL) en urgence",
                "Négocier un échéancier de paiement avec le bailleur",
                "Préparer votre défense pour l'audience au tribunal",
                "Faire valoir tous vos droits et protections légales"
            ],
            "lettre": {
                "destinataire_bloc": "[Bailleur]\n[Adresse]\n[Code postal] [Ville]",
                "objet": "Demande de délais - Expulsion locative",
                "corps": "Madame, Monsieur,\n\nSuite à l'assignation reçue, je sollicite un délai de paiement.\n\nMa situation ne me permet pas un règlement immédiat.\n\nJe suis en démarche FSL et propose un échéancier.\n\nJe vous prie d'agréer, Madame, Monsieur, l'expression de ma considération distinguée.",
                "pj": ["Assignation", "Justificatifs revenus", "Demande FSL", "Proposition échéancier"],
                "signature": "[Prénom NOM]\n[Adresse]\nLe [Date]"
            },
            "checklist": [
                "Vérifier période trêve hivernale (1er nov - 31 mars)",
                "Déposer demande FSL en urgence",
                "Préparer défense pour audience",
                "Négocier échéancier avec bailleur"
            ],
            "mentions": "Aide automatisée – ne remplace pas un conseil d'avocat. Trêve hivernale protège contre expulsions. Aide FSL disponible."
        },
        "ecole": {
            "resume": [
                "URGENT - Signaler immédiatement le harcèlement au chef d'établissement",
                "Contacter le 3020 (numéro national anti-harcèlement) pour accompagnement",
                "Constituer un dossier de preuves détaillé avec dates et témoignages",
                "Exiger la mise en place du protocole anti-harcèlement de l'établissement",
                "Solliciter un accompagnement psychologique pour votre enfant",
                "Porter plainte si violences physiques avérées"
            ],
            "lettre": {
                "destinataire_bloc": "Chef d'Établissement\n[Établissement]\n[Adresse]\n[Code postal] [Ville]",
                "objet": "SIGNALEMENT URGENT - Harcèlement scolaire",
                "corps": "Madame, Monsieur le Chef d'Établissement,\n\nJe porte à votre connaissance avec urgence que mon enfant est victime de harcèlement scolaire.\n\nCette situation nécessite la mise en œuvre immédiate du protocole de protection.\n\nJe sollicite un rendez-vous urgent.\n\nJe vous prie d'agréer, Madame, Monsieur, l'expression de ma considération.",
                "pj": ["Preuves du harcèlement", "Certificats médicaux", "Témoignages"],
                "signature": "[Prénom NOM]\nParent de [Prénom enfant]\nLe [Date]"
            },
            "checklist": [
                "Contacter le 3020 immédiatement",
                "Demander rendez-vous urgent avec direction",
                "Documenter tous les faits avec preuves",
                "Porter plainte si violences physiques"
            ],
            "mentions": "Aide automatisée – ne remplace pas un conseil spécialisé. Urgence : 3020. Harcèlement = délit pénal si avéré."
        },
        "decodeur": {
            "resume": [
                "Analyser méthodiquement le courrier reçu pour en comprendre les enjeux",
                "Identifier vos obligations légales et délais à respecter",
                "Distinguer ce qui relève de l'information et ce qui exige une action",
                "Préparer une réponse adaptée si une réaction est nécessaire",
                "Conserver l'original et constituer un dossier de suivi",
                "Faire valoir vos droits en cas de demande abusive"
            ],
            "lettre": {
                "destinataire_bloc": "[Expéditeur]\n[Adresse]\n[Code postal] [Ville]",
                "objet": "Réponse à votre courrier",
                "corps": "Madame, Monsieur,\n\nJ'ai bien reçu votre courrier.\n\nAprès examen, je vous apporte les éléments suivants :\n\n[Votre réponse selon le contenu]\n\nJe me tiens à disposition pour complément.\n\nJe vous prie d'agréer, Madame, Monsieur, l'expression de ma considération distinguée.",
                "pj": ["Copie courrier reçu", "Documents justificatifs", "Pièce d'identité"],
                "signature": "[Prénom NOM]\n[Adresse]\nLe [Date]"
            },
            "checklist": [
                "Conserver l'original et faire des copies",
                "Respecter les délais mentionnés",
                "Rassembler documents demandés",
                "Vérifier la légitimité des demandes"
            ],
            "mentions": "Aide automatisée – ne remplace pas un conseil juridique. Vérifier légitimité des demandes. Respecter délais légaux."
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
        elif tool_id == "travail" and user_fields:
            response = integrate_travail_data(response, user_fields)
        elif tool_id == "caf" and user_fields:
            response = integrate_caf_data(response, user_fields)
        elif tool_id == "energie" and user_fields:
            response = integrate_energie_data(response, user_fields)
        elif tool_id == "aides" and user_fields:
            response = integrate_aides_data(response, user_fields)
        elif tool_id == "sante" and user_fields:
            response = integrate_sante_data(response, user_fields)
        elif tool_id == "usure" and user_fields:
            response = integrate_usure_data(response, user_fields)
        elif tool_id == "expulsions" and user_fields:
            response = integrate_expulsions_data(response, user_fields)
        elif tool_id == "ecole" and user_fields:
            response = integrate_ecole_data(response, user_fields)
        elif tool_id == "decodeur" and user_fields:
            response = integrate_decodeur_data(response, user_fields)
        
        # Apply quality enhancement to all responses
        response = enhance_response_quality(response, user_fields, tool_id)
        
        # Also render letter template for mock responses to maintain consistency
        try:
            prompt_data = prompting.build_prompt(tool_id, user_fields or {})
            template_str = prompt_data['template']
            
            # Ensure we have valid template variables by merging response letter data with user fields
            template_vars = {
                'tool_id': tool_id,
                **(user_fields or {}),  # User form data
                **response.get('lettre', {}),  # Generated letter components from mock
            }
            
            # Special handling to ensure key elements appear in rendered letters
            if tool_id == "amendes" and user_fields:
                template_vars.update({
                    'numero_process_verbal': user_fields.get('numero_process_verbal'),
                    'date_infraction': user_fields.get('date_infraction'),
                    'lieu': user_fields.get('lieu'),
                    'motif_contestation': user_fields.get('motif_contestation'),
                })
            elif tool_id == "caf" and user_fields:
                template_vars.update({
                    'numero_allocataire': user_fields.get('numero_allocataire'),
                    'type_courrier': user_fields.get('type_courrier'),
                })
            
            rendered_letter = render_letter_with_template(template_str, {'lettre': template_vars}, template_vars, tool_id)
            response['lettre'] = rendered_letter
        except Exception as e:
            logger.warning(f"Template rendering failed in mock response: {e}")
            # Keep the original dict format as fallback
        
        return response
    
    # Generic enhanced fallback for other tools
    generic_response = {
        "resume": [
            "Pas de panique : analyser calmement votre situation pour identifier vos droits et les démarches appropriées",
            "Prendre le temps de rassembler tous vos documents - même si cela semble complexe, chaque pièce a son importance",
            "Rédiger votre courrier en suivant nos conseils - vous avez toutes les clés pour être convaincant(e)",
            "Envoyer en lettre recommandée pour être pris(e) au sérieux - c'est votre garantie légale",
            "Suivre votre dossier sans stress - les administrations ont des délais à respecter",
            "Rester confiant(e) : en connaissant vos droits et en suivant la procédure, vous maximisez vos chances de succès",
            "Si besoin, ne pas hésiter à faire appel - vous avez des recours, utilisez-les !",
            "Garder toutes vos preuves précieusement - c'est votre meilleure protection"
        ],
        "lettre": {
            "destinataire_bloc": "Service compétent\n[Nom précis du service concerné]\n[Adresse complète du service]\n[Code postal] [Ville]",
            "objet": f"Demande concernant {tool_id.replace('_', ' ').title()} - Dossier personnel",
            "corps": "Madame, Monsieur,\n\nJ'ai l'honneur de m'adresser à vos services concernant ma situation qui nécessite votre expertise et votre intervention.\n\n[Ici, vous exposerez clairement votre situation en vous appuyant sur les faits et vos droits]\n\nJe suis convaincu(e) que ma demande est justifiée et j'espère qu'elle recevra un accueil favorable de votre part.\n\nVous trouverez ci-joint les documents nécessaires à l'examen de mon dossier. Je reste à votre disposition pour tout complément d'information.\n\nDans l'attente de votre réponse, je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations respectueuses.",
            "pj": ["Documents justifiant votre situation", "Pièce d'identité en cours de validité", "Justificatif de domicile récent", "Tout document pertinent selon votre cas"],
            "signature": "[Votre prénom et NOM]\n[Votre adresse complète]\n[Code postal et ville]\nTéléphone : [Votre numéro]\nEmail : [Votre email]\n\nFait à [Votre ville], le [Date du jour]"
        },
        "checklist": [
            "📋 Faire une copie de tous vos documents avant envoi - c'est votre sécurité",
            "⏰ Bien noter les délais à respecter et les programmer dans votre agenda",
            "📎 Rassembler toutes les pièces demandées - même si cela prend du temps, c'est essentiel",
            "📬 Envoyer en recommandé avec accusé de réception - gardez précieusement ce papier",
            "📅 Noter la date limite de réponse et programmer un rappel si nécessaire",
            "💪 Rester patient(e) mais vigilant(e) - vous avez fait le nécessaire",
            "🔄 En cas de problème, ne pas hésiter à relancer ou faire appel - c'est votre droit",
            "📞 Si vous avez des doutes, contacter le service concerné - ils sont là pour vous aider"
        ],
        "mentions": "🤖 Cette aide automatisée vous donne les bases pour bien démarrer vos démarches. 💪 Vous avez des droits, n'hésitez pas à les faire valoir ! ⚖️ En cas de doute, un avocat peut vous conseiller pour les situations complexes. 📞 Les services publics ont l'obligation de vous renseigner - n'hésitez pas à les contacter. 🕒 Respectez bien les délais, mais ne vous mettez pas de pression inutile. 🎯 Avec de la méthode et de la persévérance, la plupart des démarches aboutissent positivement."
    }
    
    return enhance_response_quality(generic_response, user_fields, tool_id)

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

def render_letter_with_template(template_str: str, generated_data: Dict[str, Any], user_fields: Dict[str, Any], tool_id: str) -> str:
    """Render final letter using Jinja template"""
    try:
        # Prepare template variables
        template_vars = {
            'tool_id': tool_id,
            **user_fields,  # Include all user form data
            **generated_data.get('lettre', {}),  # Include generated letter components
        }
        
        # Render template
        template = Template(template_str)
        rendered = template.render(**template_vars)
        
        return rendered.strip()
        
    except Exception as e:
        logger.error(f"Template rendering failed: {e}")
        # Fallback to basic letter structure
        lettre = generated_data.get('lettre', {})
        return f"""DESTINATAIRE: {lettre.get('destinataire_bloc', 'Service compétent')}

OBJET: {lettre.get('objet', f'Courrier – {tool_id.upper()}')}

CORPS:
{lettre.get('corps', 'Corps de la lettre...')}

PIÈCES JOINTES:
{chr(10).join(f'- {pj}' for pj in lettre.get('pj', ['Document de référence']))}

SIGNATURE:
{lettre.get('signature', '[Votre nom et adresse]')}

---
Lettre générée automatiquement – à relire avant envoi."""

def generate_with_schema_driven_approach(tool_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate response using schema-driven approach with 2-pass system"""
    try:
        # Build prompt using schema-driven approach
        prompt_data = prompting.build_prompt(tool_id, payload)
        
        # Construct enhanced system prompt for 2-pass generation
        system_prompt = f"""{prompt_data['system']}

{prompt_data['instructions']}

Tu dois OBLIGATOIREMENT répondre avec un JSON valide contenant exactement ces 4 clés:
- "resume": array de 5-8 strings concrètes (étapes à suivre avec conseil rassurant)
- "lettre": objet avec les clés "destinataire_bloc", "objet", "corps", "pj" (array), "signature"  
- "checklist": array de 3-6 strings (actions claires, verbes à l'infinitif)
- "mentions": string (2-4 rappels juridiques bienveillants)

PASS 1: Génère un brouillon JSON avec toutes les clés requises."""
        
        # User prompt with context and examples
        user_prompt = f"""Contexte utilisateur:
{prompt_data['context']}

Utilise ces blueprints comme guide:
Checklist: {prompt_data['checklist_blueprint']}
Mentions: {prompt_data['mentions_blueprint']}

Génère une réponse JSON complète et personnalisée selon le contexte."""
        
        # Pass 1: Initial generation
        logger.info(f"Schema-driven Pass 1 - Initial generation for tool: {tool_id}")
        pass1_response = call_openai_with_retry(system_prompt, user_prompt)
        
        # Validate Pass 1 response
        validated_pass1 = validate_and_fix_response(pass1_response, tool_id)
        
        # Pass 2: Auto-critique and refinement
        logger.info(f"Schema-driven Pass 2 - Auto-critique for tool: {tool_id}")
        critique_prompt = f"""PASS 2 - AUTO-CRITIQUE ET AMÉLIORATION:

JSON généré en Pass 1:
{json.dumps(validated_pass1, ensure_ascii=False, indent=2)}

AMÉLIORE selon ces critères:

1. PERSONNALISATION MAXIMALE : Intègre tous les éléments du contexte utilisateur (dates, noms, références, montants). Évite les formulations génériques comme "[à compléter]".

2. TONALITÉ ADMINISTRATIVE FRANÇAISE : Équilibre professionnel et accessible. Formules de politesse appropriées mais humaines.

3. STRUCTURE ARGUMENTATIVE : Corps de lettre logique avec introduction, développement factuel, demande claire, conclusion cordiale.

4. EXHAUSTIVITÉ RASSURANTE :
   - resume: 5-8 étapes détaillées avec conseils encourageants  
   - checklist: 3-6 actions concrètes avec délais précis
   - mentions: 2-4 rappels juridiques bienveillants

5. PIÈCES JOINTES PERTINENTES : Liste précise et adaptée au cas d'espèce.

Réponds avec le JSON amélioré, identique en structure mais optimisé en qualité."""

        pass2_response = call_openai_with_retry(system_prompt, critique_prompt)
        
        # Final validation
        final_response = validate_and_fix_response(pass2_response, tool_id)
        
        # Render letter using Jinja template
        template_str = prompt_data['template']
        rendered_letter = render_letter_with_template(template_str, final_response, payload, tool_id)
        
        # Replace the generated letter with the rendered template
        final_response['lettre'] = rendered_letter
        
        logger.info(f"Schema-driven generation completed for tool: {tool_id}")
        return final_response
        
    except Exception as e:
        logger.error(f"Schema-driven generation failed for {tool_id}: {e}")
        # Fallback to existing mock system
        return get_mock_response(tool_id, payload)

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
    
    # Try schema-driven generation with OpenAI, fallback to mock on any error
    if openai_client:
        try:
            # Use new schema-driven approach
            return generate_with_schema_driven_approach(in_.tool_id, in_.fields)
            
        except Exception as e:
            logger.error(f"Schema-driven generation failed for tool {in_.tool_id}: {e}")
    
    # Fallback to mock response
    logger.info(f"Using mock response for tool: {in_.tool_id}")
    return get_mock_response(in_.tool_id, in_.fields)