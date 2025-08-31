import Link from 'next/link'
const tools=['amendes','aides','loyers','travail','sante','caf','usure','energie','expulsions','css','ecole','decodeur']
export default function Page(){
  return (<main style={{maxWidth:1000,margin:'40px auto',padding:20}}>
    <h1>Outils Citoyens</h1>
    <p>12 outils gratuits pour générer des lettres et procédures.</p>
    <ul style={{columns:2,gap:24}}>{tools.map(t=>(<li key={t}><Link href={`/outil/${t}`}>{t}</Link></li>))}</ul>
    <p style={{fontSize:12,opacity:.7,marginTop:24}}>Aide automatisée – ne remplace pas un conseil d’avocat.</p>
  </main>) }