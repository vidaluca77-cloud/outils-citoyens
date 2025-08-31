'use client'
import { useEffect, useState } from 'react'
import axios from 'axios'
export default function Page({params}:{params:{id:string}}){
  const {id}=params
  const [schema,setSchema]=useState<any>(null)
  const [values,setValues]=useState<any>({})
  const [resp,setResp]=useState<any>(null)
  const [loading,setLoading]=useState<boolean>(false)
  const [error,setError]=useState<string>('')
  const [toast,setToast]=useState<string>('')
  const API=process.env.NEXT_PUBLIC_API_BASE||'http://localhost:8000'
  useEffect(()=>{fetch(`/schemas/${id}.json`).then(r=>r.json()).then(setSchema)},[id])
  
  // Auto-hide toast after 3 seconds
  useEffect(()=>{
    if(toast){
      const timer = setTimeout(()=>setToast(''),3000)
      return ()=>clearTimeout(timer)
    }
  },[toast])

  // Format response data as structured text
  const formatAsText = (): string => {
    if (!resp || !schema) return ''
    
    let text = `=== ${schema.title} ===\n\n`
    
    // RÉSUMÉ section
    text += '[RÉSUMÉ]\n'
    if (resp.resume?.length) {
      resp.resume.forEach((item: string) => {
        text += `- ${item}\n`
      })
    }
    text += '\n'
    
    // LETTRE section
    text += '[LETTRE]\n'
    if (resp.lettre) {
      text += `Destinataire :\n${resp.lettre.destinataire_bloc || ''}\n\n`
      text += `Objet : ${resp.lettre.objet || ''}\n\n`
      text += `Corps :\n${resp.lettre.corps || ''}\n\n`
      text += 'Pièces jointes :\n'
      if (resp.lettre.pj?.length) {
        resp.lettre.pj.forEach((pj: string) => {
          text += `- ${pj}\n`
        })
      }
      text += '\n'
      text += `Signature :\n${resp.lettre.signature || ''}\n\n`
    }
    
    // CHECKLIST section
    text += '[CHECKLIST]\n'
    if (resp.checklist?.length) {
      resp.checklist.forEach((item: string) => {
        text += `- ${item}\n`
      })
    }
    text += '\n'
    
    // MENTIONS section
    text += '[MENTIONS]\n'
    text += `${resp.mentions || ''}\n`
    
    return text
  }

  // Copy formatted text to clipboard
  const copyToClipboard = async () => {
    try {
      const text = formatAsText()
      await navigator.clipboard.writeText(text)
      setToast('Copié ✅')
    } catch (err) {
      // Fallback for older browsers
      alert('Texte copié dans le presse-papiers')
    }
  }

  // Download formatted text as .txt file
  const downloadTxt = () => {
    try {
      const text = formatAsText()
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      
      // Generate filename with current date
      const now = new Date()
      const dateStr = now.getFullYear() + '-' + 
        String(now.getMonth() + 1).padStart(2, '0') + '-' + 
        String(now.getDate()).padStart(2, '0')
      const filename = `${id}_${dateStr}.txt`
      
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      setToast('Téléchargé ✅')
    } catch (err) {
      alert('Erreur lors du téléchargement')
    }
  }

  // Handle form submission with loading state
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      const r = await axios.post(`${API}/generate`, {tool_id: id, fields: values})
      setResp(r.data)
    } catch (err) {
      setError('Erreur lors de la génération. Veuillez réessayer.')
    } finally {
      setLoading(false)
    }
  }
  if(!schema) return <main style={{padding:20}}>Chargement…</main>
  return (<main style={{maxWidth:900,margin:'40px auto',padding:20}}>
    <h1>{schema.title} ({id})</h1>
    {error && (<div style={{background:'#fee',border:'1px solid #fcc',borderRadius:8,padding:12,marginBottom:16,color:'#c33'}}>{error}</div>)}
    <form onSubmit={handleSubmit}>
      {Object.entries(schema.properties).map(([k,def]:any)=>(
        <div key={k} style={{marginBottom:12}}>
          <label style={{display:'block',fontWeight:600}}>{k}</label>
          <input type="text" placeholder={def.description||''}
            onChange={e=>setValues((s:any)=>({...s,[k]:e.target.value}))}
            style={{width:'100%',padding:8,border:'1px solid #ccc',borderRadius:8}}/>
        </div>
      ))}
      <button type="submit" disabled={loading} style={{padding:'10px 20px',border:'none',borderRadius:8,background:loading?'#ccc':'#007bff',color:'white',cursor:loading?'not-allowed':'pointer'}}>
        {loading ? 'Génération...' : 'Générer'}
      </button>
    </form>
    {resp && (<section style={{marginTop:24}}>
      {/* Action buttons */}
      <div style={{display:'flex',gap:12,marginBottom:16}}>
        <button onClick={copyToClipboard} style={{padding:'8px 16px',border:'1px solid #007bff',borderRadius:8,background:'white',color:'#007bff',cursor:'pointer'}}>
          Copier tout
        </button>
        <button onClick={downloadTxt} style={{padding:'8px 16px',border:'none',borderRadius:8,background:'#28a745',color:'white',cursor:'pointer'}}>
          Télécharger .txt
        </button>
      </div>
      
      <h2>Résumé</h2><ul>{resp.resume?.map((s:string,i:number)=>(<li key={i}>{s}</li>))}</ul>
      <h2>Lettre</h2>
      <pre style={{whiteSpace:'pre-wrap',background:'#f7f7f7',padding:12,borderRadius:8}}>
Destinataire:
{resp.lettre?.destinataire_bloc}

Objet: {resp.lettre?.objet}

{resp.lettre?.corps}

Pièces jointes: {(resp.lettre?.pj||[]).join(', ')}

Signature:
{resp.lettre?.signature}
      </pre>
      <h2>Checklist</h2><ul>{resp.checklist?.map((s:string,i:number)=>(<li key={i}>{s}</li>))}</ul>
      <p style={{fontSize:12,opacity:.7}}>{resp.mentions}</p>
    </section>)}
    
    {/* Toast notification */}
    {toast && (
      <div style={{
        position:'fixed',
        top:20,
        right:20,
        background:'#28a745',
        color:'white',
        padding:'12px 20px',
        borderRadius:8,
        boxShadow:'0 4px 12px rgba(0,0,0,0.1)',
        zIndex:1000
      }}>
        {toast}
      </div>
    )}
  </main>) }