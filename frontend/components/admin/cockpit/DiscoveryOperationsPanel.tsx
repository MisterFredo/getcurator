"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import WatchScanControls from "@/components/admin/company/WatchScanControls";
import ContactEmployerCheck from "@/components/admin/cockpit/ContactEmployerCheck";
import {api} from "@/lib/api";
import LibraryPostBacklog from "@/components/admin/cockpit/LibraryPostBacklog";
type SourceRow={id_source:string;name:string;status:string;new:number;error?:string;warnings?:string[]};
type MediaJob={id_job:string;scope:string;status:string;created_at:string;sources:SourceRow[]};
type CorpoJob={id_job:string;status:string;total:number;finished:number;new_mentions:number;current_company?:string};
const scopeLabel={ALL:"Toutes les sources",WEB:"Hors LinkedIn Bright Data",LINKEDIN:"LinkedIn Bright Data uniquement"};
const btn="border rounded px-4 py-2 disabled:opacity-50";
type WatchJob={status:string;sources:{status:string}[]};
type LibraryJob={status:string;registered?:number;qualified?:number;registration_failed?:number;qualification_failed?:number};
const statusLabel:Record<string,string>={RUNNING:"En cours",COMPLETE:"Terminé",PARTIAL:"À reprendre",FAILED:"En échec",PAUSED:"Suspendu",IDLE:"À lancer"};
export default function DiscoveryOperationsPanel({overview=false}:{overview?:boolean}){
 const [media,setMedia]=useState<MediaJob|null>(null);const [corpo,setCorpo]=useState<CorpoJob|null>(null);
 const [watch,setWatch]=useState<WatchJob|null>(null);
 const [library,setLibrary]=useState<LibraryJob|null>(null);
 const [busy,setBusy]=useState(false);const [error,setError]=useState("");const [notice,setNotice]=useState("");const [pollError,setPollError]=useState("");const [refresh,setRefresh]=useState(0);

 useEffect(()=>{
  let stopped=false;let timer:ReturnType<typeof setTimeout>|undefined;
  async function poll(){
   const results=await Promise.allSettled([api.get('/cockpit/discovery/media/jobs'),api.get('/company/watch/mention-jobs'),api.get('/company/watch/operations/jobs'),api.get('/cockpit/operations/library-post-backlog/status')]);
   if(stopped)return;
   const failures:string[]=[];
   if(results[0].status==='fulfilled')setMedia(results[0].value.jobs?.[0]||null);else failures.push('Suivi Médias indisponible');
   if(results[1].status==='fulfilled')setCorpo(results[1].value.jobs?.[0]||null);else failures.push('Suivi Mentions indisponible');
   if(results[2].status==='fulfilled')setWatch(results[2].value.jobs?.[0]||null);else failures.push('Suivi Veille indisponible');
   if(results[3].status==='fulfilled')setLibrary(results[3].value);else failures.push('Suivi Library indisponible');
   setPollError(failures.join(' · '));
   const statuses = [
    results[0].status === "fulfilled" && results[0].value.jobs?.[0]?.status,
    results[1].status === "fulfilled" && results[1].value.jobs?.[0]?.status,
    results[2].status === "fulfilled" && results[2].value.jobs?.[0]?.status,
    results[3].status === "fulfilled" && results[3].value.status,
   ];
   const running = statuses.some(status => ["RUNNING", "PENDING", "QUEUED"].includes(String(status)));
   timer = setTimeout(poll, running ? 10000 : 60000);
  }
  void poll();return()=>{stopped=true;if(timer)clearTimeout(timer);};
 },[refresh]);
 async function start(path:string,body:unknown,kind:'media'|'corpo'){
  if(busy)return;setBusy(true);setError("");setNotice("");
  try{const res=await api.post(path,body);if(kind==='media')setMedia(res);else setCorpo(res);setNotice(res.reused?'Collecte existante reprise côté serveur.':'Collecte lancée côté serveur. Vous pouvez quitter le Cockpit.');setRefresh(v=>v+1);}
  catch(e){setError(e instanceof Error?e.message:'Lancement impossible.');}finally{setBusy(false);}
 }
 const followUp = <section className="rounded-xl border bg-white p-5 space-y-3">
  <div className="flex flex-wrap items-center justify-between gap-3">
   <h2 className="text-lg font-semibold">Suivi des collectes et de la Library</h2>
   {overview ? <a className="underline text-sm" href="#collecte">Ouvrir Collecte &amp; Library</a>
    : <button className="underline text-sm" onClick={()=>setRefresh(v=>v+1)}>Actualiser</button>}
  </div>
  <ul className="grid gap-2 text-sm sm:grid-cols-2">
   <li><strong>Médias</strong> · {media ? (statusLabel[media.status] || media.status) : "—"}
    {media && ` · ${media.sources.filter(s=>s.status==="FAILED").length} échec(s)`}</li>
   <li><strong>Veille</strong> · {watch ? (statusLabel[watch.status] || watch.status) : "—"}
    {watch && ` · ${watch.sources.filter(s=>["COMPLETE","FAILED","SKIPPED"].includes(s.status)).length}/${watch.sources.length} sources · ${watch.sources.filter(s=>s.status==="FAILED").length} échec(s)`}</li>
   <li><strong>Mentions</strong> · {corpo ? (statusLabel[corpo.status] || corpo.status) : "—"}
    {corpo && ` · ${corpo.finished}/${corpo.total} sociétés`}</li>
   <li><strong>Rattrapage LinkedIn</strong> · {library ? (statusLabel[library.status] || library.status) : "—"}
    {library && library.status!=="IDLE" && ` · ${library.qualified ?? 0} qualifiés · ${(library.registration_failed ?? 0) + (library.qualification_failed ?? 0)} échec(s)`}</li>
  </ul>
  {pollError&&<p role="status" className="text-sm text-amber-800">{pollError}</p>}
 </section>;
 if(overview)return followUp;
 return <>{followUp}<section className="border rounded-xl bg-white p-6 space-y-5"><div className="flex justify-between"><h2 className="text-xl font-semibold">Lancer une collecte</h2></div>
 {media&&<div className="border rounded p-3 text-sm"><strong>{scopeLabel[media.scope as keyof typeof scopeLabel]||media.scope} · {media.status}</strong><p>{media.sources.filter(s=>['COMPLETE','FAILED'].includes(s.status)).length}/{media.sources.length} sources terminées · {media.sources.reduce((n,s)=>n+s.new,0)} nouvelles URL</p>{media.status==='RUNNING'&&<button disabled={busy} className="underline mt-2" onClick={()=>void start(`/cockpit/discovery/media/jobs/${encodeURIComponent(media.id_job)}/resume`,{},'media')}>Reprendre après interruption du serveur</button>}<details className="mt-2"><summary>Détail des sources</summary>{media.sources.map(s=><div key={s.id_source} className="border-t py-2"><strong>{s.name}</strong> · {s.status} · {s.new} nouvelle(s) URL{s.error&&<p className="text-amber-800">{s.error}</p>}{s.warnings?.map((w,i)=><p key={i} className="text-gray-500">{w}</p>)}</div>)}</details></div>}
 <div className="space-y-3"><h3 className="font-semibold">Médias</h3><div className="flex flex-wrap gap-2">{(['ALL','WEB','LINKEDIN'] as const).map(scope=><button key={scope} disabled={busy} className={btn} onClick={()=>void start('/cockpit/discovery/media/start',{scope},'media')}>{scopeLabel[scope]}</button>)}</div><p className="text-sm text-gray-500">Toutes les sources automatiques du périmètre choisi, sans filtre d’univers. Jusqu’à trois comptes LinkedIn actifs à la fois.</p><Link className="underline text-sm" href="/admin/discovery">Ouvrir Discovery Médias pour sélectionner les URL</Link>

 </div><div className="border-t pt-4 space-y-3"><h3 className="font-semibold">Veille — sites et LinkedIn</h3><WatchScanControls/><Link href="/admin/discovery/corpo" className="underline text-sm">Ouvrir la Veille et les diagnostics des sources</Link></div><div className="border-t pt-4 space-y-3"><h3 className="font-semibold">Corpo — Mentions</h3><button disabled={busy} className={btn} onClick={()=>void start('/company/watch/mention-jobs/global',{max_pages:3,search_budget_seconds:90,max_candidates:1000,excluded_domains:[]},'corpo')}>Lancer la collecte globale des Mentions</button><p className="text-sm text-gray-500">Sociétés actives éligibles uniquement. Les URL déjà traitées sont reconnues.</p>{corpo&&<p className="text-sm">{corpo.status} · {corpo.finished}/{corpo.total} sociétés · {corpo.new_mentions} nouvelle(s) mention(s){corpo.current_company&&` · ${corpo.current_company}`}</p>}<div className="flex flex-wrap gap-4 text-sm"><Link className="underline" href={corpo?`/admin/discovery/corpo/mentions?job=${encodeURIComponent(corpo.id_job)}`:'/admin/discovery/corpo/mentions'}>Suivi et collecte individuelle</Link><Link className="underline" href="/admin/discovery/corpo">Sources Corpo suivies</Link></div></div>
 {notice&&<p role="status" className="text-blue-800">{notice}</p>}{error&&<p role="alert" className="text-red-700">{error}</p>}
 <p className="text-xs text-gray-500">Après un redémarrage ou un déploiement de l’API, reprendre manuellement les collectes interrompues. Aucun déclenchement programmé.</p>
 </section><ContactEmployerCheck/>
 <details className="rounded-xl border bg-white p-5">
  <summary className="cursor-pointer font-semibold">Opérations ponctuelles</summary>
  <div className="mt-4"><LibraryPostBacklog/></div>
 </details></>;
}
