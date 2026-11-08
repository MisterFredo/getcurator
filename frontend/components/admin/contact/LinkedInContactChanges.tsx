"use client";
import {useEffect,useMemo,useRef,useState} from 'react';
import {api} from '@/lib/api';
export type LinkedInContactCurrent={id_contact:string;display_name:string;id_company:string|null;company_name:string|null;job_title:string|null;email:string|null;updated_at:string;linkedin_follow_enabled:boolean;is_active:boolean};
type Person={key:string;first_name:string;last_name:string;job_title:string|null;email:string|null;current?:LinkedInContactCurrent|null;identity_conflict?:string|null};
export type LinkedInChangeJob={id_job:string;status:string;total:number;counts:Record<string,number>;error?:string|null;items:{contact_key:string;name:string;status:string;message?:string|null}[]};
type Props={runId:string;groups:{key:string;label:string;contacts:Person[]}[];companies:Record<string,string>;companyNames:{id_company:string;name:string}[];job?:LinkedInChangeJob;locked:boolean;onRefresh:()=>void};
type Field='company'|'job_title'|'email';
const normalize=(s:string|null|undefined)=>(s||'').normalize('NFKC').trim().replace(/\s+/g,' ').toLocaleLowerCase();
const labels:Record<Field,string>={company:'Société',job_title:'Fonction',email:'E-mail'};
export default function LinkedInContactChanges({runId,groups,companies,companyNames,job,locked,onRefresh}:Props){
 const [selected,setSelected]=useState<Record<string,Field[]>>({});const [follow,setFollow]=useState<Record<string,boolean>>({});const [busy,setBusy]=useState(false);const [error,setError]=useState('');const [limit,setLimit]=useState(50);const [q,setQ]=useState('');
 const mounted=useRef(true);const pending=useRef(false);const request=useRef<{signature:string;id:string}|null>(null);
 useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;};},[]);
 useEffect(()=>{setSelected({});setFollow({});setError('');setLimit(50);request.current=null;},[runId]);
 useEffect(()=>{if(job?.status==='COMPLETE'){setSelected({});setFollow({});}},[job?.id_job,job?.status]);
 const proposed=useMemo(()=>groups.flatMap(g=>g.contacts.flatMap(p=>{
  const current=p.current;const company=companies[g.key];if(!current||p.identity_conflict||!company)return [];
  const fields:Field[]=[];
  if(company!==current.id_company)fields.push('company');
  if(p.job_title&&normalize(p.job_title)!==normalize(current.job_title))fields.push('job_title');
  if(p.email&&normalize(p.email)!==normalize(current.email))fields.push('email');
  return fields.length?[{person:p,current,company,group:g,fields}]:[];
 })),[groups,companies]);
 const conflicts=groups.flatMap(g=>g.contacts.filter(p=>p.identity_conflict));
 const unmapped=groups.flatMap(g=>companies[g.key]?[]:g.contacts.filter(p=>!!p.current));
 const approvals=proposed.map(p=>({contact_key:p.person.key,id_contact:p.current.id_contact,id_company:p.company,expected_updated_at:p.current.updated_at,
  fields:p.fields.filter(f=>(selected[p.person.key]||[]).includes(f)),continue_follow:!!follow[p.person.key]&&(selected[p.person.key]||[]).includes('company')})).filter(p=>p.fields.length);
 const running=job?.status==='RUNNING';const disabled=locked||busy||running;
 const filtered=proposed.filter(p=>`${p.current.display_name} ${p.group.label} ${p.current.company_name||''}`.toLocaleLowerCase().includes(q.toLocaleLowerCase()));
 function choose(key:string,field:Field,checked:boolean){setSelected(prev=>({...prev,[key]:checked?Array.from(new Set([...(prev[key]||[]),field])):(prev[key]||[]).filter(v=>v!==field)}));if(field==='company'&&!checked)setFollow(prev=>({...prev,[key]:false}));}
 async function apply(resume=false){if(pending.current)return;pending.current=true;setBusy(true);setError('');try{
  if(resume){await api.post(`/contact/linkedin/preview/${encodeURIComponent(runId)}/changes/resume`,{});}
  else{
   const signature=JSON.stringify(approvals);
   if(!request.current||request.current.signature!==signature)request.current={signature,id:crypto.randomUUID()};
   await api.post(`/contact/linkedin/preview/${encodeURIComponent(runId)}/changes`,{request_id:request.current.id,approvals});
  }
  onRefresh();
 }catch(e){if(mounted.current)setError(e instanceof Error?e.message:'Mise à jour impossible.');}finally{pending.current=false;if(mounted.current)setBusy(false);}}
 return <section className="border border-blue-200 rounded-lg p-4 space-y-4">
  <div><h3 className="text-lg font-semibold">Évolutions des contacts existants</h3><p className="text-sm text-gray-500">{proposed.length} contact(s) avec différences · {unmapped.length} contact(s) connu(s) dans une société à rapprocher · {conflicts.length} conflit(s) d’identité.</p></div>
  <p className="text-sm text-gray-600">Coche les champs à modifier puis valide. Les noms corrigés et les champs vides LinkedIn sont conservés. Une absence dans le réseau ne supprime aucun contact.</p>
  {error&&<p role="alert" className="text-red-700">{error}</p>}
  {job&&<div className="bg-gray-50 border rounded p-3 space-y-2"><p className="text-sm">{running?'Mises à jour en cours':job.status==='INTERRUPTED'?'Mises à jour interrompues':job.status==='PARTIAL'?'Mises à jour partiellement terminées':'Dernier passage terminé'} · {job.counts.APPLIED||0} modifiée(s) · {job.counts.ALREADY_CURRENT||0} déjà à jour · {job.counts.CONFLICT||0} conflit(s) · {job.counts.ERROR||0} erreur(s) · {job.counts.PENDING||0} en attente.</p>
   {running&&<p className="text-xs text-gray-500">Le traitement continue côté backend ; tu peux changer de page.</p>}
   {job.error==='UPDATE_MAPPING_MEMORY_FAILED'&&<p className="text-amber-700 text-sm">Les contacts sont traités, mais la mémorisation du rapprochement société a échoué.</p>}
   {['PARTIAL','INTERRUPTED'].includes(job.status)&&(job.counts.PENDING>0||job.counts.ERROR>0)&&<button disabled={busy||locked} onClick={()=>void apply(true)} className="underline">Reprendre les mises à jour</button>}
   {job.items.some(i=>['CONFLICT','ERROR'].includes(i.status))&&<details><summary className="cursor-pointer text-sm">Détails des conflits et erreurs</summary><ul className="text-sm mt-2 space-y-1">{job.items.filter(i=>['CONFLICT','ERROR'].includes(i.status)).map(i=><li key={i.contact_key}>{i.name} : {i.message||i.status}</li>)}</ul><button disabled={disabled} onClick={onRefresh} className="underline mt-2">Actualiser la comparaison</button></details>}
  </div>}
  {!!unmapped.length&&<p className="text-sm text-amber-800">Pour ces contacts, choisis d’abord la société dans « À rapprocher / hors import » ; leurs évolutions apparaîtront ensuite ici.</p>}
  {!!conflicts.length&&<details><summary className="cursor-pointer text-sm">Conflits d’identité à vérifier</summary><ul className="text-sm mt-2">{conflicts.map(p=><li key={p.key}>{p.first_name} {p.last_name} : {p.identity_conflict}</li>)}</ul></details>}
  {!!proposed.length&&<><div className="flex flex-wrap gap-3"><input className="border rounded p-2" value={q} onChange={e=>{setQ(e.target.value);setLimit(50);}} placeholder="Rechercher un contact ou une société…"/><button disabled={disabled} className="underline" onClick={()=>setSelected(Object.fromEntries(filtered.slice(0,1000).map(p=>[p.person.key,p.fields])))}>Sélectionner les différences de cette recherche (max. 1 000)</button><button disabled={disabled} className="underline" onClick={()=>{setSelected({});setFollow({});}}>Tout décocher</button></div>
  <div className="space-y-3">{filtered.slice(0,limit).map(p=>{
   const key=p.person.key;const companyName=companyNames.find(c=>c.id_company===p.company)?.name||p.group.label;
   const before:Record<Field,string|null>={company:p.current.company_name,job_title:p.current.job_title,email:p.current.email};
   const after:Record<Field,string|null>={company:companyName,job_title:p.person.job_title,email:p.person.email};
   return <div key={key} className="border rounded p-3"><div className="font-medium"><a className="underline" href={`/admin/contact/edit/${encodeURIComponent(p.current.id_contact)}`}>{p.current.display_name}</a></div>
    {p.fields.map(field=><label key={field} className="flex items-start gap-2 text-sm mt-2"><input className="mt-1" type="checkbox" disabled={disabled} checked={(selected[key]||[]).includes(field)} onChange={e=>choose(key,field,e.target.checked)}/><span><strong>{labels[field]}</strong> : {before[field]||'—'} → {after[field]||'—'}</span></label>)}
    {p.fields.includes('company')&&<p className="text-xs text-gray-500 mt-2">L’ancien rattachement et ses documents seront conservés. L’ancien point de suivi sera suspendu.</p>}
    {p.fields.includes('company')&&p.current.linkedin_follow_enabled&&p.current.is_active&&(selected[key]||[]).includes('company')&&<label className="flex items-center gap-2 text-sm mt-2"><input type="checkbox" disabled={disabled} checked={!!follow[key]} onChange={e=>setFollow(prev=>({...prev,[key]:e.target.checked}))}/>Poursuivre le suivi LinkedIn chez {companyName} (aucun scan lancé)</label>}
   </div>;
  })}</div>
  {filtered.length>limit&&<button onClick={()=>setLimit(v=>v+50)} className="underline">Afficher 50 évolutions supplémentaires</button>}
  <button disabled={disabled||!approvals.length||approvals.length>1000} onClick={()=>void apply()} className="bg-ratecard-blue text-white rounded px-4 py-2 disabled:opacity-40">{busy?'Enregistrement…':`Appliquer ${approvals.length} mise(s) à jour`}</button>
  {approvals.length>1000&&<p className="text-amber-700">Sélectionner au maximum 1 000 contacts par validation.</p>}
  </>}
  {!proposed.length&&!running&&<p className="text-sm text-gray-500">Aucune différence exploitable pour les contacts rapprochés.</p>}
 </section>;
}
