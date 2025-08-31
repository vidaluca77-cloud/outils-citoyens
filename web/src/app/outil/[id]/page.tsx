'use client'
import { useEffect, useState } from 'react'
import axios from 'axios'
export default function Page({params}:{params:{id:string}}){
  const {id}=params
  const [schema,setSchema]=useState<any>(null)
  const [values,setValues]=useState<any>({})
  const [resp,setResp]=useState<any>(null)
  const API=process.env.NEXT_PUBLIC_API_BASE||'http://localhost:8000'
  useEffect(()=>{fetch(`/schemas/${id}.json`).then(r=>r.json()).then(setSchema)},[id])
  if(!schema) return <main style={{padding:20}}>Chargement…</main>
  return (<main style={{maxWidth:900,margin:'40px auto',padding:20}}>
    <h1>{schema.title} ({id})</h1>
    <form onSubmit={(e)=>{e.preventDefault();(async()=>{
      const r=await axios.post(`${API}/generate`,{tool_id:id,fields:values}); setResp(r.data);
    })()}}>
      {Object.entries(schema.properties).map(([k,def]:any)=>(
        <div key={k} style={{marginBottom:12}}>
          <label style={{display:'block',fontWeight:600}}>{k}</label>
          <input type="text" placeholder={def.description||''}
            onChange={e=>setValues((s:any)=>({...s,[k]:e.target.value}))}
            style={{width:'100%',padding:8,border:'1px solid #ccc',borderRadius:8}}/>
        </div>
      ))}
      <button type="submit">Générer</button>
    </form>
    {resp && (<section style={{marginTop:24}}>
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
  </main>) }