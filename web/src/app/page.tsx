import Link from 'next/link'

const tools = [
  'amendes', 'aides', 'loyers', 'travail', 'sante', 'caf', 
  'usure', 'energie', 'expulsions', 'css', 'ecole', 'decodeur'
]

export default function Page() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto max-w-4xl px-4 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">Outils Citoyens</h1>
          <p className="text-xl text-gray-600">12 outils gratuits pour générer des lettres et procédures.</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {tools.map(tool => (
            <Link 
              key={tool} 
              href={`/outil/${tool}`}
              className="block p-6 bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg hover:border-blue-300 transition-all duration-200"
            >
              <h3 className="text-lg font-semibold text-gray-800 capitalize">
                {tool.replace('_', ' ')}
              </h3>
              <p className="text-sm text-gray-600 mt-2">
                Générer une lettre pour {tool}
              </p>
            </Link>
          ))}
        </div>
        
        <div className="text-center">
          <p className="text-sm text-gray-500">
            Aide automatisée – ne remplace pas un conseil d&apos;avocat.
          </p>
        </div>
      </div>
    </div>
  )
}