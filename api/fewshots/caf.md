# Exemples pour Recours CAF

## Exemple 1: Suspension APL pour pièce manquante

**Contexte d'entrée JSON:**
```json
{
  "numero_allocataire": "1234567",
  "type_courrier": "suspension APL",
  "motif": "Pièce manquante dans le dossier",
  "periode": "Mars 2024",
  "identite": {
    "nom": "BERNARD",
    "prenom": "Sophie",
    "adresse": "789 rue de la Liberté, 13001 Marseille"
  },
  "piece_reclamee": "Quittance de loyer février 2024",
  "date_envoi_piece": "25/02/2024"
}
```

**Sortie JSON attendue:**
```json
{
  "resume": [
    "Analyser le courrier CAF de suspension APL pour le dossier n° 1234567",
    "Rassembler les preuves d'envoi de la quittance de loyer février 2024",
    "Contester la suspension en prouvant l'envoi de la pièce dans les délais",
    "Déposer un recours gracieux en LRAR dans les 2 mois",
    "Demander le rétablissement immédiat des prestations",
    "Préparer un recours CRA en cas de rejet du recours gracieux"
  ],
  "lettre": {
    "destinataire_bloc": "Caisse d'Allocations Familiales\nService Contentieux et Recours\n13001 Marseille",
    "objet": "Recours gracieux - Suspension APL n° allocataire 1234567 - Période Mars 2024",
    "corps": "Madame, Monsieur,\n\nAllocataire sous le numéro 1234567, je conteste formellement la suspension de mes APL pour le mois de mars 2024 motivée par l'absence de quittance de loyer février 2024.\n\nCette pièce a été transmise à vos services le 25/02/2024 en temps voulu, comme l'atteste l'accusé de réception ci-joint.\n\nCette suspension me semble donc injustifiée et porte préjudice à ma situation financière. Ma quittance était dans vos services avant la date limite.\n\nConformément à l'article R142-1 du Code de la sécurité sociale, je sollicite un recours gracieux et vous demande :\n- Le réexamen immédiat de mon dossier\n- Le rétablissement de mes APL pour mars 2024\n- Le versement des sommes dues\n\nDans l'attente de votre réponse sous 2 mois, je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations respectueuses.",
    "pj": [
      "Courrier CAF de suspension APL",
      "Quittance de loyer février 2024 envoyée le 25/02/2024",
      "Accusé de réception postal du 25/02/2024",
      "Relevé d'identité bancaire",
      "Copie pièce d'identité"
    ],
    "signature": "Sophie BERNARD\nAllocataire n° 1234567\n789 rue de la Liberté, 13001 Marseille\nTéléphone : 04.91.23.45.67\n\nFait à Marseille, le 15/03/2024"
  },
  "checklist": [
    "Respecter le délai de recours de 2 mois après réception du courrier CAF",
    "Rassembler tous les accusés de réception prouvant l'envoi des pièces",
    "Envoyer le recours en LRAR avec numéro allocataire 1234567 visible",
    "Demander expressément le rétablissement et le rattrapage des sommes",
    "Conserver copies de tous les documents et accusés de réception",
    "Préparer un dossier CRA si pas de réponse sous 2 mois"
  ],
  "mentions": "Aide automatisée – ne remplace pas un conseil spécialisé. Délai de recours : 2 mois impératif. Possibilité de saisir la Commission de Recours Amiable en cas d'échec. Aide juridictionnelle possible pour les recours."
}
```

## Exemple 2: Indu RSA contesté

**Contexte d'entrée JSON:**
```json
{
  "numero_allocataire": "9876543",
  "type_courrier": "indu RSA", 
  "montant": "850",
  "periode": "Janvier-Février 2024",
  "motif": "Révision de situation déclarée tardivement",
  "identite": {
    "nom": "GARCIA",
    "prenom": "Carlos",
    "adresse": "321 boulevard du Travail, 31000 Toulouse"
  },
  "date_declaration": "05/03/2024",
  "changement_situation": "Reprise d'emploi CDD"
}
```

**Sortie JSON attendue:**
```json
{
  "resume": [
    "Analyser l'indu RSA de 850€ réclamé par la CAF (dossier n° 9876543)",
    "Vérifier les délais de déclaration du changement de situation professionnelle", 
    "Contester l'indu en prouvant la bonne foi et le respect des obligations",
    "Déposer un recours gracieux documenté dans les 2 mois",
    "Demander un échéancier en cas de maintien partiel de l'indu",
    "Préparer les éléments pour un éventuel recours devant la CRA"
  ],
  "lettre": {
    "destinataire_bloc": "Caisse d'Allocations Familiales\nService Contentieux et Recours\n31000 Toulouse",
    "objet": "Recours gracieux - Indu RSA n° allocataire 9876543 - Montant 850€ - Période Janvier-Février 2024",
    "corps": "Madame, Monsieur,\n\nAllocataire sous le numéro 9876543, je conteste l'indu RSA de 850€ que vous réclamez pour la période janvier-février 2024, motivé par une déclaration tardive de changement de situation.\n\nMa reprise d'emploi en CDD a été déclarée le 05/03/2024, soit dans le délai légal de 30 jours suivant la fin de période concernée. Cette déclaration respecte mes obligations d'allocataire.\n\nDe plus, ce CDD était de courte durée et ne modifiait pas fondamentalement ma situation précaire justifiant le RSA.\n\nJe conteste donc cet indu qui me semble injustifié au regard :\n- Du respect des délais de déclaration\n- De la nature temporaire de l'emploi\n- De ma bonne foi dans les démarches\n\nJe sollicite le réexamen de mon dossier et l'annulation de cet indu.\n\nJe vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations respectueuses.",
    "pj": [
      "Courrier CAF réclamant l'indu de 850€",
      "Déclaration de changement de situation du 05/03/2024",
      "Contrat CDD et bulletins de paie de la période",
      "Attestation Pôle emploi de fin de CDD",
      "Justificatifs de revenus actuels",
      "Copie pièce d'identité"
    ],
    "signature": "Carlos GARCIA\nAllocataire n° 9876543\n321 boulevard du Travail, 31000 Toulouse\nTéléphone : 05.34.56.78.90\n\nFait à Toulouse, le 20/03/2024"
  },
  "checklist": [
    "Respecter le délai de recours de 2 mois après réception de la réclamation d'indu",
    "Rassembler tous les justificatifs de la déclaration dans les délais",
    "Prouver la nature temporaire et précaire de l'emploi concerné",
    "Envoyer le recours en LRAR avec numéro allocataire 9876543",
    "Demander un échéancier si l'indu est partiellement maintenu",
    "Contacter un travailleur social pour aide si difficultés financières"
  ],
  "mentions": "Aide automatisée – conseil juridique spécialisé recommandé. Délai de recours : 2 mois maximum. Commission de Recours Amiable en second recours. Possibilité d'aide juridictionnelle. Échéancier possible même en cas d'indu confirmé."
}
```