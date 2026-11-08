"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

type Person={key:string;first_name:string;last_name:string;job_title:string|null;linkedin_url:string;email:string|null;existing:boolean;email_warning:boolean};
type Company={id_company:string;name:string};
type Group={key:string;label:string;company_id:string;match:string;suggestions:Company[];contacts:Person[]};
type Result={imported:number;skipped:number;email_conflicts:number};
type Preview={id_run:string;status:string;pages:number;received:number;error:string|null;groups?:Group[];companies?:Company[];stats?:{invalid:number;duplicates:number;conflicting_profiles:number};result?:Result;phase?:string;import_processed?:number;import_total?:number};
const BASE="/contact/linkedin/preview";
const LAST="contacts-linkedin-last-run-v1";
const message=(e:unknown)=>e instanceof Error?e.message:"Opération impossible.";
function store(key:string,value:string){try{localStorage.setItem(key,value);}catch{/* Storage can be disabled. */}}
function saved(key:string){try{return localStorage.getItem(key);}catch{return null;}}
const ERRORS:Record<string,string>={
 IMPORT_TIME_BUDGET:"Le temps de traitement est écoulé. Reprendre pour importer la suite ; les contacts acquis sont conservés.",
 IMPORT_COMPANY_CHANGED:"Une société sélectionnée a été désactivée ou supprimée. Rétablir son état avant de reprendre cet import, ou lancer un nouvel aperçu.",
 IMPORT_WRITE_FAILED:"Écriture interrompue. Reprendre : les lots déjà importés sont conservés et dédupliqués.",
 LINKEDIN_HTTP_401:"Le token LinkedIn a expiré ou n'est plus valide. Remplace-le dans Render, puis reprends la récupération.",
 LINKEDIN_HTTP_403:"LinkedIn refuse l'accès : vérifier les droits du token et le produit Member Data Portability.",
 LINKEDIN_HTTP_429:"Limite d'appels LinkedIn atteinte. Réessaie plus tard ; les pages reçues sont conservées.",
 LINKEDIN_DATA_NOT_READY:"Les données ne sont pas encore disponibles. Réessaie plus tard.",
 LINKEDIN_REPEATED_PAGE:"LinkedIn a renvoyé une page déjà reçue. La collecte est arrêtée pour éviter une boucle.",
 LINKEDIN_REQUEST_FAILED:"Appel LinkedIn interrompu. Les pages déjà reçues sont conservées.",
 LINKEDIN_SAFETY_LIMIT:"La collecte a atteint une limite de sécurité. Aucun import partiel n'est autorisé.",
 LINKEDIN_TIME_BUDGET:"Le temps de récupération est écoulé. Reprendre pour récupérer la suite.",
};
export default function LinkedInContactImport(){
 const [previewLoading,setPreviewLoading]=useState(false);const [revision,setRevision]=useState(0);const [id,setId]=useState("");const [data,setData]=useState<Preview|null>(null);
 const [selected,setSelected]=useState<Set<string>>(new Set());const [companies,setCompanies]=useState<Record<string,string>>({});
 const [open,setOpen]=useState<Record<string,boolean>>({});const [q,setQ]=useState("");const [filter,setFilter]=useState("matched");const [limit,setLimit]=useState(50);
 const [busy,setBusy]=useState(false);const [error,setError]=useState("");const [notice,setNotice]=useState("");
 const mounted=useRef(true);const initialized=useRef("");const busyRef=useRef(false);
 useEffect(()=>{mounted.current=true;setId(saved(LAST)||"");return()=>{mounted.current=false;};},[]);
 useEffect(()=>{
  if(!id)return;setPreviewLoading(true);let stopped=false;let timer:ReturnType<typeof setTimeout>|undefined;
  async function refresh(){try{
   const result=await api.get(`${BASE}/${encodeURIComponent(id)}`) as Preview;
   if(stopped)return;setPreviewLoading(false);setData(result);setError("");
   if(result.groups&&initialized.current!==id){
    let choice: {selected:string[];companies:Record<string,string>}|null=null;
    try{const raw=saved(`contacts-linkedin-choice-${id}`);if(raw)choice=JSON.parse(raw);}catch{/* Default choices. */}
    const companyMap=Object.fromEntries(result.groups.map(g=>[g.key,g.company_id]));
    const defaults=result.groups.flatMap(g=>g.company_id?g.contacts.filter(c=>!c.existing).map(c=>c.key):[]);
    setSelected(new Set(choice?.selected||defaults));setCompanies({...companyMap,...choice?.companies});initialized.current=id;
   }
   if(result.status==="IMPORTED")window.dispatchEvent(new Event("contacts-updated"));
   if(["FETCHING","IMPORTING"].includes(result.status))timer=setTimeout(()=>void refresh(),3000);
  }catch(e){if(!stopped){setPreviewLoading(false);setError(message(e));timer=setTimeout(()=>void refresh(),10000);}}}
  void refresh();return()=>{stopped=true;if(timer)clearTimeout(timer);};
 },[id,revision]);
 useEffect(()=>{if(id&&initialized.current===id)store(`contacts-linkedin-choice-${id}`,JSON.stringify({selected:Array.from(selected),companies}));},[id,selected,companies]);
 async function start(resume=false){if(busyRef.current)return;busyRef.current=true;setBusy(true);setError("");setNotice("");try{
  const result=await api.post(resume?`${BASE}/${encodeURIComponent(id)}/resume`:BASE,{}) as {id_run:string};
  store(LAST,result.id_run);
  if(mounted.current){if(result.id_run!==id){initialized.current="";setData(null);setId(result.id_run);}else{setRevision(v=>v+1);}}
 }catch(e){if(mounted.current)setError(message(e));}finally{busyRef.current=false;if(mounted.current)setBusy(false);}}
 async function continuePreview(){if(busyRef.current)return;busyRef.current=true;setBusy(true);setError("");try{
  const result=await api.post(`${BASE}/${encodeURIComponent(id)}/continue`,{}) as {id_run:string};
  store(LAST,result.id_run);
  if(mounted.current){initialized.current="";setData(null);setFilter('unmatched');setLimit(50);setId(result.id_run);setNotice("Aperçu rouvert depuis les données sauvegardées. Aucun nouvel appel LinkedIn.");}
 }catch(e){if(mounted.current)setError(message(e));}finally{busyRef.current=false;if(mounted.current)setBusy(false);}}
 const groups=data?.groups||[];const available=data?.companies||[];
 const eligible=groups.flatMap(g=>companies[g.key]?g.contacts.filter(c=>!c.existing&&selected.has(c.key)):[]);
 async function commit(){if(busyRef.current||!eligible.length)return;busyRef.current=true;setBusy(true);setError("");try{
  const selections=groups.filter(g=>companies[g.key]).map(g=>({group_key:g.key,id_company:companies[g.key],contact_keys:g.contacts.filter(c=>!c.existing&&selected.has(c.key)).map(c=>c.key)})).filter(g=>g.contact_keys.length);
  const result=await api.post(`${BASE}/${encodeURIComponent(id)}/import`,{selections}) as {status:string};
  if(mounted.current){setData(current=>current?{...current,status:result.status}:current);setNotice("Import lancé côté backend. Tu peux changer de page.");setRevision(v=>v+1);}
 }catch(e){if(mounted.current)setError(message(e));}finally{busyRef.current=false;if(mounted.current)setBusy(false);}}
 function toggle(keys:string[],checked:boolean){setSelected(prev=>{const next=new Set(prev);keys.forEach(k=>checked?next.add(k):next.delete(k));return next;});}
 const filtered=groups.filter(g=>(filter==='all'||(filter==='matched'?!!companies[g.key]:!companies[g.key]))&&(`${g.label} ${available.find(c=>c.id_company===companies[g.key])?.name||''}`).toLocaleLowerCase().includes(q.toLocaleLowerCase()));
 const fetching=data?.status==='FETCHING';const importing=data?.status==='IMPORTING';const ready=data?.status==='READY';const done=data?.status==='IMPORTED';
 return <section className="border rounded-xl p-5 bg-white space-y-4">
  <div className="flex flex-wrap justify-between gap-3"><div><h2 className="text-xl font-semibold">Importer mes relations LinkedIn</h2><p className="text-sm text-gray-500 mt-1">Rapprochement par société GetCurator. Les majuscules et les espaces sont ignorés. Aucun suivi activé à l'import.</p></div>
  <button disabled={busy||previewLoading||fetching||importing} onClick={()=>void start()} className="border rounded px-4 py-2 disabled:opacity-40">{busy?'Démarrage…':previewLoading&&!data?'Chargement de l’aperçu…':data?'Nouvelle récupération LinkedIn':'Récupérer mes relations'}</button></div>
  {previewLoading&&!data&&<p role="status" className="text-sm text-gray-500">Chargement de l’aperçu sauvegardé et des rapprochements société…</p>}
  {error&&<p role="alert" className="text-red-700">{error}</p>}{notice&&<p role="status" className="text-green-800">{notice}</p>}
  {data&&<p className="text-sm">{importing?'Import en cours':fetching?'Récupération en cours':ready?'Aperçu prêt':done?'Import terminé':'Récupération à reprendre'} · {data.pages} page(s) reçue(s) · {data.received} relation(s) reçue(s)</p>}
  {importing&&<p className="text-sm">{data?.import_processed||0} / {data?.import_total||0} contact(s) traité(s) par lots. Tu peux changer de page.</p>}
  {fetching&&<p className="text-sm text-gray-500">Tu peux changer de page : la récupération continue côté backend. L'aperçu sera retrouvé ici. Un redémarrage du backend peut nécessiter une reprise.</p>}
  {data&&['PARTIAL','FAILED','INTERRUPTED'].includes(data.status)&&<div className="bg-amber-50 p-3 rounded space-y-2"><p>{ERRORS[data.error||'']||'Récupération interrompue. Les pages déjà reçues sont conservées.'}</p><button disabled={busy} onClick={()=>void start(true)} className="underline">Reprendre la récupération</button><p className="text-sm">{data.phase==='IMPORT'?'Les lots déjà importés sont conservés. La reprise poursuit la sélection validée.':"L’import sera disponible une fois la pagination terminée."}</p></div>}
  {(ready||done)&&<>
   <p className="text-sm">{groups.filter(g=>companies[g.key]).length} libellé(s) société rapproché(s) · {groups.filter(g=>!companies[g.key]).length} sans rapprochement · {eligible.length} contact(s) sélectionné(s)</p>
   <p className="text-xs text-gray-500">{data?.stats?.duplicates||0} répétition(s) regroupée(s) · {data?.stats?.invalid||0} ligne(s) invalide(s) · {data?.stats?.conflicting_profiles||0} profil(s) avec sociétés contradictoires, hors import.</p>
   {done&&data?.result&&<p className="text-green-800">{data.result.imported} contact(s) importé(s) · {data.result.skipped} déjà présent(s). {data.result.email_conflicts>0?`${data.result.email_conflicts} adresse(s) partagée(s) omise(s) sur les profils supplémentaires.`:''}</p>}
   {done&&<button disabled={busy} onClick={()=>void continuePreview()} className="border rounded px-4 py-2 disabled:opacity-40">Rapprocher et importer d’autres contacts</button>}
   <div className="flex flex-wrap gap-3"><input className="border rounded p-2" placeholder="Rechercher une société…" value={q} onChange={e=>{setQ(e.target.value);setLimit(50);}}/><select className="border rounded p-2" value={filter} onChange={e=>{setFilter(e.target.value);setLimit(50);}}><option value="matched">Sociétés rapprochées</option><option value="unmatched">À rapprocher / hors import</option><option value="all">Toutes</option></select></div>
   <div className="space-y-2">{filtered.slice(0,limit).map(g=>{
    const keys=g.contacts.filter(c=>!c.existing).map(c=>c.key);const count=keys.filter(k=>selected.has(k)).length;const company=available.find(c=>c.id_company===companies[g.key]);
    return <div key={g.key} className="border rounded p-3"><div className="flex items-center justify-between gap-3"><button className="text-left font-medium" aria-expanded={!!open[g.key]} onClick={()=>setOpen(prev=>({...prev,[g.key]:!prev[g.key]}))}>{open[g.key]?'▾':'▸'} {g.label} → {company?.name||'Hors import'} <span className="font-normal text-gray-500">· {g.contacts.length} relation(s) · {count} sélectionnée(s)</span></button>
    <input aria-label={`Sélectionner les contacts de ${g.label}`} type="checkbox" disabled={!ready||!companies[g.key]||!keys.length||busy} checked={!!keys.length&&count===keys.length} onChange={e=>toggle(keys,e.target.checked)}/></div>
    {open[g.key]&&<div className="mt-3 space-y-3"><label className="block text-sm">Société GetCurator<select className="border rounded p-2 ml-2 max-w-full" disabled={!ready||busy} value={companies[g.key]||''} onChange={e=>{const value=e.target.value;setCompanies(prev=>({...prev,[g.key]:value}));toggle(keys,!!value);}}><option value="">Ne pas importer</option>{available.map(c=><option key={c.id_company} value={c.id_company}>{c.name}</option>)}</select></label>
    {!company&&g.suggestions.length>0&&<p className="text-sm text-gray-500">Suggestions à vérifier : {g.suggestions.map(c=>c.name).join(' · ')}</p>}
    <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="text-left"><th>Sélection</th><th>Contact</th><th>Fonction</th><th>E-mail</th><th>État</th></tr></thead><tbody>{g.contacts.map(c=><tr key={c.key} className="border-t"><td className="py-2"><input type="checkbox" aria-label={`Importer ${c.first_name} ${c.last_name}`} disabled={!ready||!companies[g.key]||c.existing||busy} checked={!c.existing&&selected.has(c.key)} onChange={e=>toggle([c.key],e.target.checked)}/></td><td><a href={c.linkedin_url} target="_blank" rel="noreferrer" className="underline">{c.first_name} {c.last_name}</a></td><td>{c.job_title||'—'}</td><td>{c.email||'—'}</td><td>{c.existing?'Déjà présent — conservé':c.email_warning?'Nouveau — e-mail invalide omis':'Nouveau'}</td></tr>)}</tbody></table></div></div>}
    </div>;
   })}</div>
   {!filtered.length&&<p className="text-gray-500">Aucune société dans cette sélection.</p>}{filtered.length>limit&&<button className="underline" onClick={()=>setLimit(v=>v+50)}>Afficher 50 sociétés supplémentaires</button>}
   {ready&&<div className="sticky bottom-0 bg-white border-t py-3 flex flex-wrap justify-between items-center gap-3"><p className="text-sm">Les sociétés non rapprochées et les contacts décochés restent hors import.</p><button disabled={busy||!eligible.length} onClick={()=>void commit()} className="bg-ratecard-blue text-white rounded px-4 py-2 disabled:opacity-40">{busy?'Import en cours…':`Importer ${eligible.length} contact(s)`}</button></div>}
  </>}
 </section>;
}
