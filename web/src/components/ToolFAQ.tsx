interface FAQItem {
  question: string;
  answer: string;
}

interface ToolFAQProps {
  toolId: string;
}

const toolFAQs: Record<string, FAQItem[]> = {
  amendes: [
    {
      question: "Comment contester une amende de stationnement ?",
      answer: "Vous pouvez contester une amende en envoyant une lettre recommandée avec accusé de réception dans les 45 jours suivant la réception de l'avis de contravention."
    },
    {
      question: "Quels documents joindre à ma contestation ?",
      answer: "Joignez tous les éléments de preuve : photos, tickets de stationnement valides, témoignages, justificatifs médicaux selon votre situation."
    },
    {
      question: "Dans quels délais dois-je contester ?",
      answer: "Vous avez 45 jours à partir de la date de réception de l'avis de contravention pour contester l'amende."
    }
  ],
  caf: [
    {
      question: "Comment répondre à un courrier de la CAF ?",
      answer: "Répondez toujours par courrier recommandé avec accusé de réception en fournissant tous les justificatifs demandés dans les délais impartis."
    },
    {
      question: "Puis-je contester une décision de la CAF ?",
      answer: "Oui, vous pouvez formuler un recours administratif puis un recours contentieux devant le tribunal administratif si nécessaire."
    }
  ],
  loyers: [
    {
      question: "Comment contester une augmentation de loyer ?",
      answer: "Vous pouvez contester si l'augmentation dépasse l'indice de référence des loyers (IRL) ou en cas de non-conformité avec la réglementation."
    },
    {
      question: "Quels sont mes droits en cas de logement insalubre ?",
      answer: "Vous pouvez exiger des travaux, demander une diminution de loyer ou déposer plainte auprès des services d'hygiène municipaux."
    }
  ],
  travail: [
    {
      question: "Comment contester un licenciement ?",
      answer: "Vous pouvez saisir le conseil de prud'hommes dans les 12 mois suivant la notification du licenciement pour contester sa validité."
    },
    {
      question: "Quels sont mes droits en cas de harcèlement au travail ?",
      answer: "Vous pouvez alerter votre employeur, saisir l'inspection du travail et engager une procédure judiciaire. La protection du salarié est légale."
    }
  ],
  sante: [
    {
      question: "Comment contester un refus de remboursement ?",
      answer: "Contactez d'abord votre caisse d'assurance maladie, puis le médiateur de l'assurance maladie si le différend persiste."
    },
    {
      question: "Quels recours en cas d'erreur médicale ?",
      answer: "Vous pouvez saisir la commission de conciliation puis le tribunal administratif ou judiciaire selon le cas."
    }
  ],
  // Default FAQ for other tools
  default: [
    {
      question: "Comment utiliser cet outil ?",
      answer: "Remplissez le formulaire avec vos informations, puis cliquez sur 'Générer' pour obtenir votre lettre personnalisée."
    },
    {
      question: "Mes données sont-elles sécurisées ?",
      answer: "Oui, vos données sont traitées de manière sécurisée et ne sont pas conservées après la génération de votre document."
    }
  ]
};

export function ToolFAQ({ toolId }: ToolFAQProps) {
  const faqs = toolFAQs[toolId] || toolFAQs.default;

  return (
    <div className="bg-white rounded-3xl shadow-xl p-8 lg:p-12 mb-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        Questions fréquentes
      </h2>
      <div className="space-y-6">
        {faqs.map((faq, index) => (
          <div key={index} className="border-b border-gray-200 pb-6 last:border-b-0 last:pb-0">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">
              {faq.question}
            </h3>
            <p className="text-gray-600 leading-relaxed">
              {faq.answer}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export function generateFAQJsonLD(toolId: string): string {
  const faqs = toolFAQs[toolId] || toolFAQs.default;
  
  const jsonLD = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": faqs.map(faq => ({
      "@type": "Question",
      "name": faq.question,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": faq.answer
      }
    }))
  };

  return JSON.stringify(jsonLD);
}