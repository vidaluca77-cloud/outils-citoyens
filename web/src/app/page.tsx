import Link from 'next/link'

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

export default function Page() {
  return (
    <div className="page-container">
      <div className="content-container">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <span className="mr-2">🇫🇷</span>
            Outils citoyens français
          </div>
          <h1 className="text-5xl lg:text-6xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-blue-800 bg-clip-text text-transparent mb-6">
            Outils Citoyens
          </h1>
          <p className="text-xl lg:text-2xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            <span className="font-semibold text-blue-600">12 outils gratuits</span> pour générer automatiquement 
            vos lettres et procédures administratives en quelques clics.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-8">
            <div className="flex items-center text-green-600 font-medium">
              <span className="mr-2">✅</span>
              100% Gratuit
            </div>
            <div className="flex items-center text-blue-600 font-medium">
              <span className="mr-2">⚡</span>
              Génération instantanée
            </div>
            <div className="flex items-center text-purple-600 font-medium">
              <span className="mr-2">🔒</span>
              Données sécurisées
            </div>
          </div>
        </div>
        
        {/* Assistant CTA */}
        <div className="mb-12">
          <Link 
            href="/assistant"
            className="block bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white p-8 rounded-3xl shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300"
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {tools.map((tool, index) => (
            <Link 
              key={tool.id} 
              href={`/outil/${tool.id}`}
              className="card-gradient group hover:scale-105"
              style={{
                animationDelay: `${index * 100}ms`
              }}
            >
              <div className="p-8">
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
              </div>
            </Link>
          ))}
        </div>
        
        {/* Features Section */}
        <div className="bg-white rounded-3xl shadow-xl p-8 lg:p-12 mb-16">
          <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">
            Comment ça fonctionne ?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📝</span>
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">1. Remplissez</h3>
              <p className="text-gray-600">Complétez le formulaire avec vos informations</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚡</span>
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">2. Générez</h3>
              <p className="text-gray-600">L&apos;IA crée votre lettre personnalisée</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📄</span>
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">3. Téléchargez</h3>
              <p className="text-gray-600">Récupérez votre document prêt à envoyer</p>
            </div>
          </div>
        </div>
        
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