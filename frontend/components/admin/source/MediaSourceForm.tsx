"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import {api} from "@/lib/api";
import VisualSectionSource from "@/components/visuals/VisualSectionSource";

const modes=[['MANUAL','Copie / colle'],['NEWSLETTER_MANUAL','Newsletter copiée / collée'],
  ['LINKEDIN_PROFILE','LinkedIn — copier-coller Studio'],['LINKEDIN_BRIGHTDATA','LinkedIn — automatisé Bright Data'],
  ['HTML','Découverte via page HTML'],['RSS','Flux RSS'],['SITEMAP','Sitemap'],['WORDPRESS_API','API WordPress'],['API','API'],['PDF_MANUAL','PDF manuel']];
const control="border p-2 w-full rounded";
const empty={name:"",type_source:"",description:"",domain:"",author:"",author_profile:"",universe_id:"",acquisition_mode:"MANUAL"};
const errorText=(e:unknown)=>e instanceof Error?e.message:"Opération impossible";

export default function MediaSourceForm({id}:{id?:string}) {
  const [data,setData]=useState({...empty});
  const [sourceId,setSourceId]=useState(id || "");
  const [universes,setUniverses]=useState<{id_universe:string;label:string}[]>([]);
  const [logo,setLogo]=useState<string|null>(null);
  const [loading,setLoading]=useState(!!id);
  const [saving,setSaving]=useState(false);
  const [error,setError]=useState("");
  const [notice,setNotice]=useState("");
  const [loadFailed,setLoadFailed]=useState(false);
  const [revision,setRevision]=useState(0);
  useEffect(()=>{
    let cancelled=false;
    api.get('/universe/list').then(r=>{if(!cancelled)setUniverses(r.universes || []);})
      .catch(e=>{if(!cancelled)setError(errorText(e));});
    return ()=>{cancelled=true;};
  },[]);
  useEffect(()=>{
    if(!id)return;
    let cancelled=false;setLoading(true);setLoadFailed(false);
    api.get(`/source/${encodeURIComponent(id)}`).then(r=>{
      if(cancelled)return;
      setSourceId(id);setLogo(r.logo || null);
      setData({name:r.name||"",type_source:r.type_source||"",description:r.description||"",domain:r.domain||"",
        author:r.author||"",author_profile:r.author_profile||"",universe_id:r.universe_id||"",acquisition_mode:r.acquisition_mode||"MANUAL"});
    }).catch(e=>{if(!cancelled){setError(errorText(e));setLoadFailed(true);}}).finally(()=>{if(!cancelled)setLoading(false);});
    return ()=>{cancelled=true;};
  },[id,revision]);
  async function save(event:React.FormEvent<HTMLFormElement>){
    event.preventDefault();if(saving||loadFailed)return;
    if(!data.name.trim()){setError('Nom requis');return;}
    if(data.acquisition_mode==='LINKEDIN_BRIGHTDATA'){
      try{
        const u=new URL(data.domain);
        if(u.protocol!=='https:' || u.hostname!=='linkedin.com' && !u.hostname.endsWith('.linkedin.com') || !/^\/(in|company)\/[^/]+/.test(u.pathname))throw new Error();
      }catch{setError('Renseignez une URL LinkedIn de profil ou de société dans Domaine.');return;}
    }
    setSaving(true);setError('');setNotice('');
    try{
      const payload={name:data.name.trim(),type_source:data.type_source||null,description:data.description||null,
        domain:data.domain.trim()||null,author:data.author||null,author_profile:data.author_profile||null,
        universe_id:data.universe_id||null,acquisition_mode:data.acquisition_mode};
      if(sourceId)await api.put(`/source/update/${encodeURIComponent(sourceId)}`,payload);
      else{
        const r=await api.post('/source/create',payload);
        if(!r.source_id)throw new Error('ID source manquant');setSourceId(r.source_id);
      }
      setNotice('Source enregistrée. Le logo peut être ajouté ci-dessous.');
    }catch(e){setError(errorText(e));}finally{setSaving(false);}
  }
  async function remove(){
    if(!sourceId||saving||!window.confirm('Supprimer cette source ?'))return;
    setSaving(true);setError('');
    try{await api.delete(`/source/${encodeURIComponent(sourceId)}`);window.location.href='/admin/source';}
    catch(e){setError(errorText(e));setSaving(false);}
  }
  async function reloadLogo(){if(sourceId){const r=await api.get(`/source/${encodeURIComponent(sourceId)}`);setLogo(r.logo||null);}}
  if(loading)return <p>Chargement…</p>;
  return <div className="space-y-8">
    <header className="flex justify-between"><h1 className="text-2xl font-semibold">{sourceId?'Modifier la source':'Ajouter une source'}</h1><Link href="/admin/source" className="underline">← Retour</Link></header>
    {error&&<p role="alert" className="text-red-700">{error}</p>}{notice&&<p role="status" className="text-green-700">{notice}</p>}
    {loadFailed&&<button onClick={()=>setRevision(v=>v+1)} className="underline">Réessayer le chargement</button>}
    <form onSubmit={save} className="space-y-5 max-w-3xl"><fieldset disabled={saving||loadFailed} className="space-y-5">
      {([['name','Nom'],['type_source','Type de source']] as const).map(([key,label])=><label key={key} className="block space-y-1"><span>{label}</span><input className={control} required={key==='name'} value={data[key]} onChange={e=>setData(v=>({...v,[key]:e.target.value}))}/></label>)}
      <label className="block space-y-1"><span>Mode d’acquisition</span><select className={control} value={data.acquisition_mode} onChange={e=>setData(v=>({...v,acquisition_mode:e.target.value}))}>
        {modes.map(([value,label])=><option key={value} value={value}>{value} — {label}</option>)}</select></label>
      {data.acquisition_mode==='LINKEDIN_BRIGHTDATA'&&<p className="text-sm bg-blue-50 p-3 rounded">Le scan automatique se lance dans Discovery / Médias. Le copier-coller du LinkedIn Studio reste disponible. La collecte peut être partielle.</p>}
      <label className="block space-y-1"><span>Univers</span><select className={control} value={data.universe_id} onChange={e=>setData(v=>({...v,universe_id:e.target.value}))}><option value="">— Aucun univers —</option>{universes.map(u=><option key={u.id_universe} value={u.id_universe}>{u.label}</option>)}</select></label>
      {([['domain','Domaine / URL du compte LinkedIn'],['author','Auteur par défaut'],['author_profile','Profil auteur']] as const).map(([key,label])=><label key={key} className="block space-y-1"><span>{label}</span><input className={control} value={data[key]} onChange={e=>setData(v=>({...v,[key]:e.target.value}))}/></label>)}
      <label className="block space-y-1"><span>Description</span><textarea className={`${control} h-24`} value={data.description} onChange={e=>setData(v=>({...v,description:e.target.value}))}/></label>
      <div className="flex gap-4"><button type="submit" className="bg-ratecard-blue text-white rounded px-6 py-2">{saving?'Enregistrement…':sourceId?'Enregistrer':'Créer la source'}</button>{sourceId&&<button type="button" onClick={()=>void remove()} className="bg-red-600 text-white rounded px-6 py-2">Supprimer</button>}</div>
    </fieldset></form>
    {sourceId&&<VisualSectionSource entityId={sourceId} rectUrl={logo?`${process.env.NEXT_PUBLIC_GCS_BASE_URL}/sources/${logo}`:null} onUpdated={reloadLogo}/>}
  </div>;
}
