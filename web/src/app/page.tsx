import Link from 'next/link'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
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
  Search,
  CheckCircle,
  Clock,
  Lock
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

export default function Page() {
  return (
    <div className="section">
      <div className="container">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-6">
            <span className="mr-2">🇫🇷</span>
            Outils citoyens français
          </div>
          <h1 className="text-5xl lg:text-6xl font-bold bg-gradient-to-r from-primary via-primary/80 to-primary bg-clip-text text-transparent mb-6">
            Outils Citoyens
          </h1>
          <p className="text-xl lg:text-2xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            <span className="font-semibold text-primary">12 outils gratuits</span> pour générer automatiquement 
            vos lettres et procédures administratives en quelques clics.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 mt-8">
            <div className="flex items-center text-green-600 font-medium">
              <CheckCircle className="w-5 h-5 mr-2" />
              100% Gratuit
            </div>
            <div className="flex items-center text-primary font-medium">
              <Clock className="w-5 h-5 mr-2" />
              Génération instantanée
            </div>
            <div className="flex items-center text-purple-600 font-medium">
              <Lock className="w-5 h-5 mr-2" />
              Données sécurisées
            </div>
          </div>
        </div>
        
        {/* Assistant CTA */}
        <div className="mb-12">
          <Link 
            href="/assistant"
            className="block bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 text-primary-foreground p-8 rounded-3xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300"
          >
            <div className="flex items-center justify-center text-center">
              <div className="text-4xl mr-4">🤖</div>
              <div>
                <h2 className="text-2xl font-bold mb-2">Assistant Juridique Conversationnel</h2>
                <p className="text-lg opacity-90">
                  Discutez avec notre IA pour identifier l&apos;outil adapté à votre situation
                </p>
                <div className="inline-flex items-center mt-3 text-lg font-medium">
                  <span className="mr-2">Commencer la conversation</span>
                  <span className="transform group-hover:translate-x-1 transition-transform">→</span>
                </div>
              </div>
            </div>
          </Link>
        </div>
        
        {/* Tools Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
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
        
        {/* Features Section */}
        <Card className="mb-16">
          <h2 className="text-3xl font-bold text-center text-card-foreground mb-8">
            Comment ça fonctionne ?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📝</span>
              </div>
              <h3 className="text-xl font-bold text-card-foreground mb-2">1. Remplissez</h3>
              <p className="text-muted-foreground">Complétez le formulaire avec vos informations</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚡</span>
              </div>
              <h3 className="text-xl font-bold text-card-foreground mb-2">2. Générez</h3>
              <p className="text-muted-foreground">L&apos;IA crée votre lettre personnalisée</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📄</span>
              </div>
              <h3 className="text-xl font-bold text-card-foreground mb-2">3. Téléchargez</h3>
              <p className="text-muted-foreground">Récupérez votre document prêt à envoyer</p>
            </div>
          </div>
        </Card>
        
        {/* Footer */}
        <div className="text-center">
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 inline-block">
            <div className="flex items-center justify-center mb-2">
              <span className="text-amber-600 mr-2">⚠️</span>
              <span className="font-semibold text-amber-800">Avertissement Important</span>
            </div>
            <p className="text-sm text-amber-700 max-w-2xl">
              Ces outils fournissent une aide automatisée et ne remplacent pas un conseil juridique professionnel. 
              Pour des situations complexes, consultez un avocat.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}