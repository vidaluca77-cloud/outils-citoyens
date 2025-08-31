import { Metadata } from 'next'
import { promises as fs } from 'fs'
import path from 'path'
import { ToolPageClient } from './ToolPageClient'

// Utility functions to generate metadata descriptions for tools
function generateToolDescription(toolId: string): string {
  const descriptions: Record<string, string> = {
    amendes: "Générez gratuitement une lettre de contestation d'amende en quelques minutes.",
    caf: "Modèles gratuits pour répondre à un courrier CAF ou formuler un recours.",
    loyers: "Lettres types pour problèmes de logement et gestion locative.",
    travail: "Modèles pour le droit du travail et résolution de conflits professionnels.",
    sante: "Lettres pour remboursements santé et réclamations médicales.",
    aides: "Demandes d'aides sociales et allocations personnalisées.",
    usure: "Courriers pour problèmes de surendettement et solutions financières.",
    energie: "Lettres pour factures d'énergie et litiges avec fournisseurs.",
    expulsions: "Procédures pour prévenir ou contester une expulsion locative.",
    css: "Demandes de couverture santé solidaire et complémentaire santé.",
    ecole: "Courriers pour scolarité et relations avec établissements scolaires.",
    decodeur: "Outil pour décrypter et comprendre vos droits administratifs."
  };
  
  return descriptions[toolId] || "Générateur gratuit de lettres administratives personnalisées.";
}

// Generate metadata for individual tool pages
export async function generateMetadata({ params }: { params: { id: string } }): Promise<Metadata> {
  const { id } = params;
  
  try {
    // Read schema from public/schemas directory
    const schemaPath = path.join(process.cwd(), 'public', 'schemas', `${id}.json`);
    const schemaContent = await fs.readFile(schemaPath, 'utf-8');
    const schema = JSON.parse(schemaContent);
    
    const title = schema.title;
    const description = generateToolDescription(id);
    const canonicalUrl = `https://outils-citoyens.vercel.app/outil/${id}`;
    
    return {
      title,
      description,
      alternates: {
        canonical: canonicalUrl,
      },
      openGraph: {
        title: `${schema.title} — Outils Citoyens`,
        description,
        url: canonicalUrl,
        siteName: 'Outils Citoyens',
        locale: 'fr_FR',
        type: 'website',
      },
      twitter: {
        card: 'summary_large_image',
        title: `${schema.title} — Outils Citoyens`,
        description,
      },
    };
  } catch (error) {
    // Fallback metadata if schema can't be loaded
    const title = `Outil ${id}`;
    const description = generateToolDescription(id);
    
    return {
      title,
      description,
      alternates: {
        canonical: `https://outils-citoyens.vercel.app/outil/${id}`,
      },
    };
  }
}

// Main page component (server component)
export default function Page({ params }: { params: { id: string } }) {
  return <ToolPageClient params={params} />;
}