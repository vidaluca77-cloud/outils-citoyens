import Link from 'next/link'
import { Card } from '../../components/ui/Card'
import { 
  Gavel, 
  HandHeart, 
  Home, 
  Briefcase, 
  Heart, 
  Baby, 
  CreditCard, 
  Zap, 
  DoorOpen, 
  Shield, 
  GraduationCap, 
  Search
} from 'lucide-react'

const tools = [
  { id: 'amendes', name: 'Amendes', description: 'Contester une amende ou infraction', icon: Gavel },
  { id: 'aides', name: 'Aides Sociales', description: 'Demander des aides et allocations', icon: HandHeart },
  { id: 'loyers', name: 'Logement', description: 'Problèmes de loyers et logement', icon: Home },
  { id: 'travail', name: 'Travail', description: 'Droit du travail et emploi', icon: Briefcase },
  { id: 'sante', name: 'Santé', description: 'Remboursements et soins médicaux', icon: Heart },
  { id: 'caf', name: 'CAF', description: 'Allocations familiales et CAF', icon: Baby },
  { id: 'usure', name: 'Surendettement', description: 'Problèmes financiers et dettes', icon: CreditCard },
  { id: 'energie', name: 'Énergie', description: 'Factures électricité et gaz', icon: Zap },
  { id: 'expulsions', name: 'Expulsions', description: 'Prévenir une expulsion locative', icon: DoorOpen },
  { id: 'css', name: 'Couverture Santé', description: 'CSS et complémentaire santé', icon: Shield },
  { id: 'ecole', name: 'Éducation', description: 'Scolarité et établissements', icon: GraduationCap },
  { id: 'decodeur', name: 'Décodeur', description: 'Décrypter vos droits', icon: Search }
]

export default function OutilsPage() {
  return (
    <div className="section">
      <div className="text-center mb-8">
        <h1 className="text-3xl lg:text-4xl font-bold text-foreground mb-4">
          Choisissez votre outil
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Sélectionnez l&apos;outil correspondant à votre situation pour générer votre document personnalisé
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
        {tools.map((tool, index) => (
          <Link 
            key={tool.id} 
            href={`/outil/${tool.id}`}
            className="group block transform transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded-lg"
            style={{
              animationDelay: `${index * 50}ms`
            }}
          >
            <Card className="h-full transition-all duration-200 group-hover:border-primary/20 group-hover:shadow-md animate-fade-in">
              <div className="flex items-center mb-4">
                <div className="p-2 bg-primary/10 rounded-lg mr-4 transform group-hover:scale-110 transition-transform duration-200">
                  <tool.icon className="w-6 h-6 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-card-foreground group-hover:text-primary transition-colors">
                    {tool.name}
                  </h3>
                </div>
              </div>
              <p className="text-muted-foreground leading-relaxed mb-4">
                {tool.description}
              </p>
              <div className="flex items-center text-primary font-medium group-hover:text-primary/80">
                <span className="mr-2">Générer une lettre</span>
                <span className="transform group-hover:translate-x-1 transition-transform">→</span>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}