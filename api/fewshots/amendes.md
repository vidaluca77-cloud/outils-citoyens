# Exemples pour Contestation d'Amende

## Exemple 1: Feu rouge masqué par travaux

**Contexte d'entrée JSON:**
```json
{
  "type_amende": "autre",
  "date_infraction": "15/03/2024", 
  "lieu": "Avenue de la République, Paris 11e",
  "numero_process_verbal": "12345678",
  "motif_contestation": "Feu tricolore masqué par travaux de voirie",
  "elements_preuve": "Photos du chantier masquant le feu, témoins présents",
  "identite": {
    "nom": "MARTIN",
    "prenom": "Pierre", 
    "adresse": "123 rue des Exemples, 75011 Paris"
  }
}
```

**Sortie JSON attendue:**
```json
{
  "resume": [
    "Analyser le procès-verbal n° 12345678 du 15/03/2024 pour identifier les éléments contestables",
    "Rassembler les preuves du feu masqué : photos du chantier, témoignages",
    "Rédiger la contestation en invoquant le défaut de visibilité du feu tricolore",
    "Envoyer en LRAR avant le 29/04/2024 (45e jour après réception)",
    "Constituer un dossier de suivi avec copies et accusés de réception",
    "Surveiller la réponse de l'OMP dans un délai de 3 mois maximum"
  ],
  "lettre": {
    "destinataire_bloc": "Monsieur l'Officier du Ministère Public\nTribunal de Police de Paris\nService des Contraventions\n75001 Paris",
    "objet": "Contestation formelle du procès-verbal n° 12345678 - Feu tricolore masqué par travaux - Art. L121-3 du Code de la route",
    "corps": "Monsieur l'Officier du Ministère Public,\n\nJ'ai l'honneur de porter à votre connaissance ma contestation formelle du procès-verbal n° 12345678 dressé le 15/03/2024 pour non-respect du feu tricolore sur l'Avenue de la République, Paris 11e.\n\nAprès examen des circonstances, je conteste cette verbalisation car le feu tricolore était masqué par des travaux de voirie en cours, rendant impossible sa perception par les usagers.\n\nLes éléments de preuve suivants appuient ma contestation : photos du chantier masquant le feu, témoignages de personnes présentes.\n\nEn conséquence, conformément à l'article 530 du Code de procédure pénale, je sollicite l'annulation de cette contravention.\n\nDans l'attente de votre décision motivée, je vous prie d'agréer, Monsieur l'Officier du Ministère Public, l'expression de ma haute considération.",
    "pj": [
      "Copie du procès-verbal n° 12345678", 
      "Photos du chantier masquant le feu tricolore",
      "Attestations de témoins présents sur les lieux",
      "Justificatif d'identité"
    ],
    "signature": "Pierre MARTIN\n123 rue des Exemples, 75011 Paris\nTéléphone : 01.23.45.67.89\n\nFait à Paris, le 20/03/2024"
  },
  "checklist": [
    "Respecter impérativement le délai de 45 jours (échéance : 29/04/2024)",
    "Photographier à nouveau les lieux si les travaux sont toujours en cours",
    "Recueillir des témoignages écrits et signés",
    "Vérifier l'exactitude des mentions du PV n° 12345678",
    "Envoyer en LRAR et conserver l'accusé de réception",
    "Ne pas payer l'amende pendant la contestation"
  ],
  "mentions": "Aide juridique automatisée – ne remplace pas un conseil d'avocat. Délai impératif : 45 jours. Recours possible devant le tribunal en cas de rejet. Ne pas payer l'amende pendant la contestation."
}
```

## Exemple 2: Stationnement contesté

**Contexte d'entrée JSON:**
```json
{
  "type_amende": "stationnement",
  "date_infraction": "08/02/2024",
  "lieu": "Rue Victor Hugo, Lyon 2e", 
  "numero_process_verbal": "87654321",
  "motif_contestation": "Véhicule en stationnement payant valide, ticket visible",
  "elements_preuve": "Ticket de stationnement horodaté, photo du véhicule avec ticket visible",
  "identite": {
    "nom": "DURAND",
    "prenom": "Marie",
    "adresse": "456 avenue de la Paix, 69002 Lyon"
  }
}
```

**Sortie JSON attendue:**
```json
{
  "resume": [
    "Analyser le PV n° 87654321 du 08/02/2024 pour stationnement irrégulier",
    "Rassembler les preuves du paiement : ticket horodaté, photos",
    "Rédiger la contestation en prouvant la régularité du stationnement", 
    "Envoyer en LRAR avant le 25/03/2024 (45e jour)",
    "Joindre tous les justificatifs de paiement du stationnement",
    "Suivre la procédure et conserver tous les documents"
  ],
  "lettre": {
    "destinataire_bloc": "Monsieur l'Officier du Ministère Public\nTribunal de Police de Lyon\nService des Contraventions\n69001 Lyon",
    "objet": "Contestation formelle du procès-verbal n° 87654321 - Stationnement payant régulier - Art. L121-3 du Code de la route",
    "corps": "Monsieur l'Officier du Ministère Public,\n\nJ'ai l'honneur de contester le procès-verbal n° 87654321 dressé le 08/02/2024 rue Victor Hugo à Lyon 2e pour stationnement irrégulier.\n\nMon véhicule était en stationnement payant régulier avec ticket d'horodateur valide et visible. Le ticket acheté couvrait la période de stationnement.\n\nLes preuves jointes démontrent la régularité de mon stationnement : ticket horodaté et photographies.\n\nJe sollicite donc l'annulation de cette contravention injustifiée.\n\nJe vous prie d'agréer, Monsieur l'Officier du Ministère Public, l'expression de ma considération distinguée.",
    "pj": [
      "Copie du procès-verbal n° 87654321",
      "Ticket de stationnement horodaté du 08/02/2024", 
      "Photos du véhicule avec ticket visible",
      "Justificatif d'identité"
    ],
    "signature": "Marie DURAND\n456 avenue de la Paix, 69002 Lyon\nTéléphone : 04.56.78.90.12\n\nFait à Lyon, le 12/02/2024"
  },
  "checklist": [
    "Respecter le délai de 45 jours (échéance : 25/03/2024)",
    "Conserver le ticket de stationnement original",
    "Photographier l'horodateur et la signalisation",
    "Vérifier les horaires de stationnement payant",
    "Envoyer en LRAR avec tous les justificatifs",
    "Ne pas régler l'amende avant la décision"
  ],
  "mentions": "Aide automatisée – conseil d'avocat recommandé pour les cas complexes. Délai strict : 45 jours. Conservation obligatoire des preuves de paiement. Recours possible en cas de rejet non motivé."
}
```