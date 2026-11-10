"use client";
import {useEffect,useRef,useState} from 'react';
import {api} from '@/lib/api';
import {changed,errorText} from '@/lib/contacts';

type Company={id_company:string;name:string};
type Row={line:number;company_name:string;id_company:string|null;status:string;reason:string;data?:{first_name:string;last_name:string;job_title?:string;linkedin_url?:string;sales_navigator_url?:string};raw:Record<string,string>};
type Run={id_run:string;status:string;rows:Row[];companies:Company[];processed:number;imported:number;skipped:number;selected_count?:number;error?:string};
const KEY='getcurator_contact_csv_run';
const eligible=(r:Row)=>r.status==='NEW'||r.status==='UNMATCHED';
const labels:Record<string,string>={NEW:'Nouveau',UNMATCHED:'Société à rapprocher',EXISTS:'Déjà présent',CONFLICT:'Conflit',INVALID:'Invalide'};
export default function ContactCsvImport(){
 const [run,setRun]=useState<Run|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[picked,setPicked]=useState<Record<number,boolean>>({}),[mapping,setMapping]=useState<Record<string,string>>({}),[page,setPage]=useState(0);
 const mounted=useRef(true),mutating=useRef(false),notified=useRef('');
 useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;};},[]);
 function install(value:Run,defaults=false){
  setRun(value);
  if(defaults){const selections:Record<number,boolean>={},maps:Record<string,string>={};value.rows.forEach(r=>{selections[r.line]=eligible(r)&&!!r.id_company;if(r.id_company)maps[r.company_name]=r.id_company;});setPicked(selections);setMapping(maps);setPage(0);}
  if(value.status==='COMPLETE'&&notified.current!==value.id_run){notified.current=value.id_run;changed();}
 }
 useEffect(()=>{
  let stopped=false;const id=localStorage.getItem(KEY);if(id)void api.get(`/contact/csv/imports/${encodeURIComponent(id)}`).then((v:Run)=>{if(!stopped)install(v,true);}).catch(e=>{if(!stopped)setError('Import précédent : '+errorText(e));});
  return()=>{stopped=true;};
 },[]);
 useEffect(()=>{
  if(!run||run.status!=='IMPORTING')return;
  let stopped=false;let timer:ReturnType<typeof setTimeout>|undefined;
  const id=run.id_run;
  async function poll(){try{const value:Run=await api.get(`/contact/csv/imports/${encodeURIComponent(id)}`);if(!stopped){install(value);setError('');}}catch(e){if(!stopped)setError(errorText(e));}finally{if(!stopped)timer=setTimeout(poll,4000);}}
  timer=setTimeout(poll,1500);return()=>{stopped=true;if(timer)clearTimeout(timer);};
 },[run?.id_run,run?.status]);
 async function upload(file:File){
  if(mutating.current)return;mutating.current=true;setBusy(true);setError('');
  try{if(file.size>3_000_000)throw new Error('Fichier limité à 3 Mo.');const value:Run=await api.post('/contact/csv/preview',{csv_text:await file.text()});localStorage.setItem(KEY,value.id_run);if(mounted.current)install(value,true);}
  catch(e){if(mounted.current)setError(errorText(e));}finally{mutating.current=false;if(mounted.current)setBusy(false);}
 }
 async function commit(resume=false){
  if(!run||mutating.current)return;mutating.current=true;setBusy(true);setError('');
  try{
   if(resume)await api.post(`/contact/csv/imports/${encodeURIComponent(run.id_run)}/resume`,{});
   else{const selections=run.rows.filter(r=>eligible(r)&&picked[r.line]&&mapping[r.company_name]).map(r=>({line:r.line,id_company:mapping[r.company_name]}));if(!selections.length)throw new Error('Sélectionner au moins un contact avec une société rapprochée.');await api.post(`/contact/csv/imports/${encodeURIComponent(run.id_run)}/commit`,{selections});}
   const value:Run=await api.get(`/contact/csv/imports/${encodeURIComponent(run.id_run)}`);if(mounted.current)install(value);
  }catch(e){if(mounted.current)setError(errorText(e));}finally{mutating.current=false;if(mounted.current)setBusy(false);}
 }
 const ready=run?.status==='READY';
 const groups=Array.from(new Set((run?.rows||[]).filter(eligible).map(r=>r.company_name)));
 const selected=(run?.rows||[]).filter(r=>eligible(r)&&picked[r.line]&&mapping[r.company_name]).length;
 const active=run?.status==='IMPORTING'||run?.status==='PARTIAL';
 return <details className="border rounded bg-white p-5" open={!!run}>
  <summary className="font-semibold cursor-pointer">Importer des contacts depuis Sheets / CSV</summary>
  <div className="space-y-4 mt-4">
   <p className="text-sm text-gray-600">Charge l’onglet Export CSV préparé dans Sheets. Les sociétés et doublons sont vérifiés avant validation. Les nouveaux contacts ne sont pas suivis par défaut ; aucun scan n’est lancé. Les fiches déjà présentes ne sont pas modifiées.</p>
   <input type="file" accept=".csv,text/csv" disabled={busy||!!active} aria-label="Choisir le CSV des contacts" onChange={e=>{const f=e.target.files?.[0];if(f)void upload(f);e.target.value='';}}/>
   <p className="text-xs text-gray-500">Colonnes : first_name, last_name, company_name, job_title, email, linkedin_url, sales_navigator_url. URL de profil /in/ obligatoire ; e-mail et lien Sales Navigator facultatifs. Maximum 2 000 contacts.</p>
   {busy&&<p role="status">Enregistrement…</p>}{error&&<p role="alert" className="text-red-700">{error}</p>}
   {run&&<>
    <p className="text-sm">{run.rows.length} ligne(s) · {run.rows.filter(r=>r.status==='EXISTS').length} déjà présente(s) · {run.rows.filter(r=>r.status==='CONFLICT'||r.status==='INVALID').length} anomalie(s) · {run.rows.filter(r=>r.status==='UNMATCHED').length} à rapprocher initialement</p>
    {ready&&<>
     {groups.map(group=><label key={group} className="flex flex-wrap gap-3 items-center text-sm"><span className="min-w-[180px]">{group}</span><select className="border rounded p-2" value={mapping[group]||''} disabled={busy} onChange={e=>{const id=e.target.value;setMapping(v=>({...v,[group]:id}));setPicked(v=>{const next={...v};run.rows.filter(r=>eligible(r)&&r.company_name===group).forEach(r=>{next[r.line]=!!id;});return next;});}}><option value="">Ne pas importer / choisir une société</option>{run.companies.map(c=><option key={c.id_company} value={c.id_company}>{c.name}</option>)}</select></label>)}
     <div className="flex flex-wrap gap-3 items-center"><button type="button" disabled={busy} className="underline" onClick={()=>{const next:Record<number,boolean>={};run.rows.forEach(r=>{next[r.line]=eligible(r)&&!!mapping[r.company_name];});setPicked(next);}}>Tout sélectionner parmi les lignes importables</button><button type="button" disabled={busy} className="underline" onClick={()=>setPicked({})}>Tout décocher</button><button type="button" disabled={busy||!selected} className="bg-ratecard-blue text-white rounded px-4 py-2 disabled:opacity-40" onClick={()=>void commit()}>Importer les {selected} contacts sélectionnés</button></div>
    </>}
    {active&&<div className="text-sm space-y-2"><p>{run.status==='PARTIAL'?'Import interrompu':'Import côté serveur en cours'} · {run.processed||0}/{run.selected_count||0} traités · {run.imported||0} créés · {run.skipped||0} déjà présents ou conflits apparus depuis l’aperçu</p>{run.error&&<p className="text-amber-800">{run.error}</p>}<p>Tu peux quitter cette page. Après une interruption du backend, reprends le même import.</p><button type="button" disabled={busy} className="underline" onClick={()=>void commit(true)}>Reprendre l’import si interrompu</button></div>}
    {run.status==='COMPLETE'&&<p role="status" className="text-green-800">Import terminé : {run.imported} contact(s) créé(s), {run.skipped} ligne(s) déjà présente(s) ou en conflit à l’écriture. Aucun contact existant modifié.</p>}
    <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="text-left border-b">{['Sélection','Ligne','Contact','Société source','Fonction','État à l’aperçu'].map(x=><th key={x} className="p-2">{x}</th>)}</tr></thead><tbody>{run.rows.slice(page*100,page*100+100).map(r=><tr key={r.line} className="border-b"><td className="p-2"><input type="checkbox" aria-label={`Importer la ligne ${r.line}`} checked={!!picked[r.line]&&!!mapping[r.company_name]} disabled={!ready||busy||!eligible(r)||!mapping[r.company_name]} onChange={e=>setPicked(v=>({...v,[r.line]:e.target.checked}))}/></td><td className="p-2">{r.line}</td><td className="p-2">{r.data?r.data.first_name+' '+r.data.last_name:r.raw.first_name+' '+r.raw.last_name}<p className="text-xs text-gray-500 break-all">{r.data?.linkedin_url||r.raw.linkedin_url}</p></td><td className="p-2">{r.company_name}</td><td className="p-2">{r.data?.job_title||r.raw.job_title}</td><td className="p-2">{labels[r.status]||r.status}<p className="text-xs text-amber-800">{r.reason}</p></td></tr>)}</tbody></table></div>
    <div className="flex gap-3 text-sm"><button type="button" disabled={page===0} className="underline disabled:opacity-40" onClick={()=>setPage(v=>v-1)}>Précédent</button><span>Page {page+1}</span><button type="button" disabled={(page+1)*100>=run.rows.length} className="underline disabled:opacity-40" onClick={()=>setPage(v=>v+1)}>Suivant</button></div>
   </>}
  </div>
 </details>;
}
