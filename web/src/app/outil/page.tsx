import Link from 'next/link'
import { Card } from '../../components/ui/Card'

const tools = [
  { id: 'amendes', name: 'Amendes', description: 'Contester une amende ou infraction', icon: '🚗' },
  { id: 'aides', name: 'Aides Sociales', description: 'Demander des aides et allocations', icon: '🤝' },
  { id: 'loyers', name: 'Logement', description: 'Problèmes de loyers et logement', icon: '🏠' },
  { id: 'travail', name: 'Travail', description: 'Droit du travail et emploi', icon: '💼' },
  { id: 'sante', name: 'Santé', description: 'Remboursements et soins médicaux', icon: '🏥' },
  { id: 'caf', name: 'CAF', description: 'Allocations familiales et CAF', icon: '👨‍👩‍👧‍👦' },
  { id: 'usure', name: 'Surendettement', description: 'Problèmes financiers et dettes', icon: '💳' },
  { id: 'energie', name: 'Énergie', description: 'Factures électricité et gaz', icon: '⚡' },
  { id: 'expulsions', name: 'Expulsions', description: 'Prévenir une expulsion locative', icon: '🚪' },
  { id: 'css', name: 'Couverture Santé', description: 'CSS et complémentaire santé', icon: '🏥' },
  { id: 'ecole', name: 'Éducation', description: 'Scolarité et établissements', icon: '🎓' },
  { id: 'decodeur', name: 'Décodeur', description: 'Décrypter vos droits', icon: '🔍' }
]

export default function OutilsPage() {
  return (
    <div className="px-4 py-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
          Choisissez votre outil
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Sélectionnez l'outil correspondant à votre situation pour générer votre document personnalisé
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
        {tools.map((tool) => (
          <Link 
            key={tool.id} 
            href={`/outil/${tool.id}`}
            className="group block transform transition-all duration-200 hover:scale-105 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-2xl"
          >
            <Card className="h-full transition-all duration-200 group-hover:border-blue-300 group-hover:shadow-md">
              <div className="flex items-center mb-4">
                <div className="text-4xl mr-4 transform group-hover:scale-110 transition-transform duration-200">
                  {tool.icon}
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-800 group-hover:text-blue-600 transition-colors">
                    {tool.name}
                  </h3>
                </div>
              </div>
              <p className="text-gray-600 leading-relaxed mb-4">
                {tool.description}
              </p>
              <div className="flex items-center text-blue-600 font-medium group-hover:text-blue-700">
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