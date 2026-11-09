"use client";
import {useEffect,useRef,useState} from 'react';
import Link from 'next/link';
import {api} from '@/lib/api';
import {changed,errorText} from '@/lib/contacts';

type Item={id_contact:string;name:string;old_company_name?:string;source_name?:string;source_url?:string;status:string;reason?:string};
type Job={id_run:string;status:string;created_at:string;updated_at:string;excluded_network:number;network_snapshot_at?:string;include_network:boolean;error?:string;snapshots?:string[];mode?:string};
type Result={job:Job|null;counts?:Record<string,number>;total?:number;items?:Item[]};
type PendingRow={id_contact:string;first_name:string;last_name:string;source_company_name?:string;profile_url:string;status:string;reason?:string;group_key:string;last_attempt_status?:string};
type Pending={items:PendingRow[];companies:{id_company:string;name:string}[];has_more:boolean};
const labels:Record<string,string>={PENDING:'En attente',CONFIRMED:'Société confirmée',MOVED:'Transféré',UNMATCHED:'Société à rapprocher',REVIEW:'À vérifier',ERROR:'Erreur de lecture',CONFLICT:'Fiche modifiée — non appliqué',NOT_CHECKED:'Non contrôlé'};
const button='border rounded px-3 py-2 disabled:opacity-40';
function date(value?:string){return value?new Date(value).toLocaleString('fr-FR'):'aucune récupération réseau enregistrée';}
export default function ContactEmployerCheck(){
 const [result,setResult]=useState<Result>({job:null}),[pending,setPending]=useState<Pending>({items:[],companies:[],has_more:false});
 const [include,setInclude]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[pollError,setPollError]=useState(''),[snapshot,setSnapshot]=useState(''),[refresh,setRefresh]=useState(0),[maps,setMaps]=useState<Record<string,string>>({});
 const lock=useRef(false),completed=useRef('');const job=result.job;const active=job?.status==='RUNNING';
 useEffect(()=>{
  let stopped=false;let timer:ReturnType<typeof setTimeout>|undefined;
  async function load(){
   const outcomes=await Promise.allSettled([api.get('/contact/employer-check/latest'),api.get('/contact/employer-check/pending')]);
   if(stopped)return;const errors:string[]=[];
   if(outcomes[0].status==='fulfilled'){
    const value=outcomes[0].value as Result;setResult(value);
    if(value.job?.status==='COMPLETE'&&completed.current!==value.job.id_run){completed.current=value.job.id_run;changed();}
   }else errors.push('Suivi du contrôle indisponible');
   if(outcomes[1].status==='fulfilled')setPending(outcomes[1].value as Pending);else errors.push('Rapprochements indisponibles');
   setPollError(errors.join(' · '));if(active)timer=setTimeout(load,8000);
  }
  void load();return()=>{stopped=true;if(timer)clearTimeout(timer);};
 },[active,refresh]);
 async function action(path:string,body:unknown={}){
  if(lock.current)return;lock.current=true;setBusy(true);setError('');
  try{await api.post(path,body);const next:Result=await api.get('/contact/employer-check/latest');setResult(next);setRefresh(v=>v+1);}
  catch(e){setError(errorText(e));}finally{lock.current=false;setBusy(false);}
 }
 const groups=Array.from(new Map(pending.items.filter(r=>r.status==='UNMATCHED'&&r.source_company_name).map(r=>[r.group_key,{key:r.group_key,name:r.source_company_name!}])).values());
 const choices=groups.filter(g=>maps[g.key]).map(g=>({group_key:g.key,id_company:maps[g.key]}));
 const running=!!job&&['RUNNING','PARTIAL','NEEDS_SNAPSHOT'].includes(job.status);
 const done=(result.total||0)-(result.counts?.PENDING||0);
 return <section className="border rounded-xl bg-white p-6 space-y-4">
  <div className="flex flex-wrap justify-between gap-3"><div><h2 className="text-xl font-semibold">Contacts — contrôle des sociétés</h2><p className="text-sm text-gray-500 mt-1">Vérifier les employeurs déclarés sur LinkedIn via Bright Data. Déclenchement manuel, sans filtre d’ancienneté ni récurrence imposée.</p></div><button type="button" className="underline text-sm" onClick={()=>setRefresh(v=>v+1)}>Actualiser</button></div>
  <div className="flex flex-wrap gap-4 items-center"><label className="text-sm flex items-center gap-2"><input type="checkbox" checked={include} disabled={busy||running} onChange={e=>setInclude(e.target.checked)}/>Inclure aussi les contacts présents dans mon réseau LinkedIn</label><button type="button" disabled={busy||running} className="bg-ratecard-blue text-white rounded px-4 py-2 disabled:opacity-40" onClick={()=>void action('/contact/employer-check/start',{include_network:include})}>Lancer le contrôle</button></div>
  <p className="text-xs text-gray-500">Par défaut : contacts suivis hors réseau, ainsi que les rattachements automatiquement mis en attente. Les contacts du réseau sont laissés à la comparaison de tes relations LinkedIn. Les profils et employeurs restent déclaratifs.</p>
  {error&&<p role="alert" className="text-red-700">{error}</p>}{pollError&&<p role="status" className="text-amber-800">{pollError}. Le suivi de cette page ne pilote pas le traitement serveur.</p>}
  {job&&<div className="border rounded p-4 space-y-3 text-sm">
   <strong>{job.mode==='MAPPINGS'?'Application des rapprochements':'Contrôle des employeurs'} · {job.status==='RUNNING'?'En cours':job.status==='COMPLETE'?'Terminé':job.status==='NEEDS_SNAPSHOT'?'Collecte Bright Data à rattacher':'Interrompu — reprise possible'}</strong>
   <p>{done}/{result.total||0} contacts traités · {result.counts?.CONFIRMED||0} confirmés · {result.counts?.MOVED||0} transférés · {result.counts?.UNMATCHED||0} à rapprocher · {result.counts?.REVIEW||0} à vérifier · {result.counts?.ERROR||0} erreurs · {result.counts?.CONFLICT||0} conflits · {result.counts?.NOT_CHECKED||0} non contrôlés</p>
   <p>{job.excluded_network||0} contacts du réseau exclus. Snapshot des relations utilisé : {date(job.network_snapshot_at)}.</p>
   <p className="text-gray-500">Lancé le {date(job.created_at)}. Tu peux quitter le Cockpit : le serveur poursuit le traitement. Après une interruption du backend, reprendre le même contrôle.</p>
   {job.error&&<p className="text-amber-800">{job.error}</p>}
   {running&&job.status!=='NEEDS_SNAPSHOT'&&<button type="button" disabled={busy} className={button} onClick={()=>void action(`/contact/employer-check/${encodeURIComponent(job.id_run)}/resume`)}>Reprendre après interruption</button>}
   {job.status==='NEEDS_SNAPSHOT'&&<div className="space-y-2"><p>Un appel a pu être accepté sans réponse. Retrouver son snapshot dans Bright Data pour éviter un second appel payant.</p><label>Snapshot <input className="border rounded p-2" placeholder="sd_…" value={snapshot} onChange={e=>setSnapshot(e.target.value)}/></label><button type="button" className={button} disabled={busy||!snapshot.trim()} onClick={()=>void action(`/contact/employer-check/${encodeURIComponent(job.id_run)}/resume`,{snapshot_id:snapshot.trim()})}>Rattacher et reprendre</button></div>}
   {['PARTIAL','NEEDS_SNAPSHOT'].includes(job.status)&&<button type="button" disabled={busy} className="underline" onClick={()=>{if(window.confirm('Clore ce contrôle en conservant les résultats acquis ? Les profils restants ne seront pas vérifiés. Une collecte déjà lancée chez Bright Data peut continuer.'))void action(`/contact/employer-check/${encodeURIComponent(job.id_run)}/finish`);}}>Clore ce contrôle sans traiter les profils restants</button>}
   <details><summary>Détail des contacts et des collectes</summary><div className="max-h-96 overflow-auto mt-2">{(result.items||[]).map(i=><div key={i.id_contact} className="border-t py-2"><Link className="underline" href={`/admin/contact/edit/${encodeURIComponent(i.id_contact)}`}>{i.name}</Link> · {labels[i.status]||i.status}<p>{i.old_company_name||'Sans rattachement'}{i.source_name&&` → employeur déclaré : ${i.source_name}`}</p>{i.reason&&<p className="text-xs text-gray-500">{i.reason}</p>}</div>)}</div><p className="text-xs break-all mt-2">Snapshots : {(job.snapshots||[]).join(' · ')||'aucun'}</p></details>
  </div>}
  <details className="border-t pt-4" open={pending.items.length>0}>
   <summary className="font-semibold cursor-pointer">Rattachements en attente ({pending.items.length}{pending.has_more?'+':''})</summary>
   <p className="text-sm text-gray-500 my-3">Les sociétés inconnues utilisent la mémoire de rapprochement existante. Choisis les sociétés, puis valide le lot. Une société créée plus tard pourra être sélectionnée après actualisation. Les situations ambiguës se corrigent depuis la fiche contact.</p>
   <div className="space-y-2">{groups.map(g=><label key={g.key} className="flex flex-wrap items-center gap-3 text-sm"><span className="min-w-[180px]">{g.name} · {pending.items.filter(r=>r.group_key===g.key&&r.status==='UNMATCHED').length} contact(s)</span><select className="border rounded p-2" disabled={busy||running} value={maps[g.key]||''} onChange={e=>setMaps(v=>({...v,[g.key]:e.target.value}))}><option value="">À rapprocher plus tard</option>{pending.companies.map(c=><option key={c.id_company} value={c.id_company}>{c.name}</option>)}</select></label>)}</div>
   {!!groups.length&&<button type="button" className={button+' mt-3'} disabled={busy||running||!choices.length} onClick={()=>void action('/contact/employer-check/mappings',{mappings:choices})}>Valider les {choices.length} rapprochements de sociétés</button>}
   <div className="max-h-72 overflow-auto mt-3 text-sm">{pending.items.map(r=><div key={r.id_contact} className="border-t py-2"><Link className="underline" href={`/admin/contact/edit/${encodeURIComponent(r.id_contact)}`}>{r.first_name} {r.last_name}</Link> · {r.source_company_name||'Employeur non confirmé'} · {labels[r.status]}<p className="text-xs text-gray-500">{r.reason}</p></div>)}</div>
  </details>
 </section>;
}
