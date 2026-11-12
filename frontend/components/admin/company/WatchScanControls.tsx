"use client";
import {useEffect,useRef,useState} from 'react';
import type {CompanyWatch} from '@/lib/companyWatch';
import {launchWatchJob,listWatchJobs,resumeWatchJob,pauseWatchJob,watchClass} from '@/lib/watchOperations';
import type {WatchJob,WatchKind,WatchChannel,WatchRole} from '@/lib/watchOperations';
const btn='border rounded px-3 py-2 text-sm disabled:opacity-50';
const errorText=(e:unknown)=>e instanceof Error?e.message:'Opération impossible';
export default function WatchScanControls({companyId,watch,role='ALL',channel='ALL',kind='ALL',onComplete}:{companyId?:string;watch?:CompanyWatch;role?:WatchRole;channel?:WatchChannel;kind?:WatchKind;onComplete?:()=>void}){
 const [job,setJob]=useState<WatchJob|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[pollError,setPollError]=useState('');
 const [refresh,setRefresh]=useState(0);const complete=useRef(onComplete);complete.current=onComplete;
 const scopeCompany=watch?.id_company||companyId;const scopeWatch=watch?.id_company_watch;
 const scopeRole=watch ? (watch.id_contact || watch.source_role==='EMPLOYEE' ? 'EMPLOYEE' : 'CORPORATE') : role;
 const running=job?.status==='RUNNING';const paused=job?.status==='PAUSED';const blocked=running||paused;const lastCompletion=useRef('');
 useEffect(()=>{
  let cancelled=false;let timer:ReturnType<typeof setTimeout>|undefined;
  async function poll(){
   try{const result=await listWatchJobs(scopeCompany,scopeWatch,scopeRole);if(cancelled)return;
    const value=result.jobs[0]||null;setJob(value);setPollError('');
    if(value&&['COMPLETE','PARTIAL','FAILED'].includes(value.status)&&lastCompletion.current!==value.id_job+value.updated_at){
     lastCompletion.current=value.id_job+value.updated_at;complete.current?.();window.dispatchEvent(new Event('watch-scan-updated'));
    }
    if(value?.status==='RUNNING')timer=setTimeout(poll,10000);
   }catch(e){if(cancelled)return;setPollError(errorText(e));timer=setTimeout(poll,15000);}
  }
  void poll();return()=>{cancelled=true;if(timer)clearTimeout(timer);};
 },[scopeCompany,scopeWatch,scopeRole,refresh]);
 async function start(target:WatchKind,failed=false,recover=false){
  if(busy)return;setBusy(true);setError('');
  try{const result=await launchWatchJob({role:scopeRole,kind:watch?watchClass(watch).kind:target,channel:watch?watchClass(watch).channel:channel,
   company_id:scopeCompany,watch_id:scopeWatch,failed_only:failed,recover_only:recover});setJob(result);setRefresh(v=>v+1);window.dispatchEvent(new Event('watch-scan-updated'));}
  catch(e){setError(errorText(e));}finally{setBusy(false);}
 }
 async function resume(){if(!job||busy)return;setBusy(true);setError('');try{setJob(await resumeWatchJob(job.id_job));setRefresh(v=>v+1);}catch(e){setError(errorText(e));}finally{setBusy(false);}}
 async function pause(){if(!job||busy)return;setBusy(true);setError('');try{setJob(await pauseWatchJob(job.id_job));setRefresh(v=>v+1);}catch(e){setError(errorText(e));}finally{setBusy(false);}}
 const available=!watch||(watch.is_active&&['HTML','BRIGHTDATA'].includes(watch.collection_method)&&watch.source_type!=='PDF');
 const finished=job?.sources.filter(s=>['COMPLETE','FAILED','SKIPPED'].includes(s.status)).length||0;
 return <section aria-label="Collectes Veille" className="border rounded bg-white p-4 space-y-3">
 <div className="flex flex-wrap gap-2">
 {watch?<button className={btn} disabled={busy||blocked||!available} onClick={()=>void start(watchClass(watch).kind)}>{watchClass(watch).kind==='SINGLE_PAGE'?'Contrôler cette page unique':'Collecter les publications de ce point'}</button>:<>
 {kind!=='SINGLE_PAGE'&&<button className={btn} disabled={busy||blocked} onClick={()=>void start('PUBLICATIONS')}>Collecter les nouvelles publications</button>}
 {kind!=='PUBLICATIONS'&&<button className={btn} disabled={busy||blocked} onClick={()=>void start('SINGLE_PAGE')}>Contrôler les pages uniques</button>}
 </>}
 <button className={btn} disabled={busy||blocked||!available} onClick={()=>void start(kind,true)}>Reprendre les sources en échec</button>
 {watch?.collection_method==='BRIGHTDATA'&&<button className={btn} disabled={busy||blocked||!available} onClick={()=>void start('PUBLICATIONS',false,true)}>Récupérer le dernier scan LinkedIn</button>}
 <button className={btn} disabled={busy} onClick={()=>setRefresh(v=>v+1)}>Actualiser le suivi</button>
 </div>
 <p className="text-xs text-gray-500">Les publications incluent les listes d’URL des sites et les posts LinkedIn. Les pages uniques ont leur propre contrôle. L’onglet actif, les filtres de canal et de type et la société sélectionnée définissent le périmètre du lancement. Vous pouvez quitter cette page après le lancement ; le backend poursuit la collecte. Aucun calendrier automatique.</p>
 {job&&<div className="text-sm space-y-2"><strong>{job.failed_only?'Reprise des échecs':job.kind==='SINGLE_PAGE'?'Contrôle des pages uniques':'Collecte des publications'} · {job.status}</strong>
 <p>{finished}/{job.sources.length} sources terminées · {job.sources.reduce((n,s)=>n+s.new,0)} nouveautés · {job.sources.reduce((n,s)=>n+s.known,0)} connues · {job.sources.reduce((n,s)=>n+s.unchanged,0)} inchangées · {job.sources.filter(s=>s.status==='FAILED').length} échecs</p>
 {running&&<button className="underline mr-4" disabled={busy} onClick={()=>void pause()}>Suspendre après l’étape en cours</button>}
 {(running||paused)&&<button className="underline" disabled={busy} onClick={()=>void resume()}>{paused?'Reprendre cette collecte':'Reprendre après interruption du serveur'}</button>}
 {paused&&<p>Suspension demandée : les requêtes déjà en cours peuvent encore se terminer. Leurs résultats sont conservés.</p>}
 <details><summary className="cursor-pointer">Résultats et problèmes par source</summary>{job.sources.map(s=><div key={s.id_company_watch} className="border-t py-2"><strong>{s.company_name} / {s.label}</strong> · {s.channel==='LINKEDIN'?'LinkedIn':'Site'} · {s.kind==='SINGLE_PAGE'?'Page unique':'Publications'} · {s.status} · {s.new} nouveauté(s){s.error&&<p className="text-red-700">{s.error}</p>}{s.warnings?.map((w,i)=><p className="text-amber-800" key={i}>{w}</p>)}</div>)}</details>
 </div>}
 {error&&<p role="alert" className="text-red-700">{error}</p>}{pollError&&<p role="status" className="text-amber-800">Suivi indisponible : {pollError}. Cela ne signifie pas que la collecte est arrêtée.</p>}
 </section>;
}
