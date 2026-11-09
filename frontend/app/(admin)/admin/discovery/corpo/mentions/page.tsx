"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import {api} from "@/lib/api";
import MentionConnectorTest from "@/components/admin/company/MentionConnectorTest";

type Company={id_company:string;name:string};
type Progress={stage:string;new_mentions:number;known_urls:number;search_requests:number;raw_urls:number;resolved:number;examined:number;pages:number;warnings:number;timings?:Record<string,number>};
type Row={id_company:string;name:string;status:string;id_run:string;error?:string;message?:string;priority_requested?:boolean;progress?:Partial<Progress>;retry_after?:string};
type Summary={id_job:string;kind:string;status:string;created_at:string;updated_at:string;total:number;finished:number;new_mentions:number;failed:number;current_company?:string};
type Job={id_job:string;kind:string;status:string;created_at:string;updated_at:string;companies:Row[]};
type Result={url:string;resolved_url?:string;title?:string;status:string;reason?:string;technical_detail?:string;qualification_reason?:string;explanation?:string;id_document?:string};
type Run={id_run:string;id_company:string;company_name:string;status:string;results:Result[];resolutions?:Result[];warnings:string[];timings?:Record<string,number>;search_errors?:unknown[]};
const terminal=(status:string)=>["COMPLETE","PARTIAL","FAILED","SKIPPED"].includes(status);
const label=(status:string)=>({QUEUED:"En attente",PENDING:"À traiter",RUNNING:"En cours",WAITING:"En attente de reprise",SEARCHING:"Recherche",RESOLVING:"Lecture",QUALIFYING:"Qualification / Library",COMPLETE:"Terminé",PARTIAL:"Terminé — couverture partielle",FAILED:"Erreur",SKIPPED:"Non traité"} as Record<string,string>)[status]||status;
const errorText=(e:unknown)=>e instanceof Error?e.message:"Opération impossible";
const control="border rounded px-3 py-2 bg-white";
function dateText(value:string){const d=new Date(value);return Number.isNaN(d.getTime())?value:d.toLocaleString("fr-FR");}
function safeUrl(value:string){try{const url=new URL(value);return ["https:","http:"].includes(url.protocol)?url.href:undefined;}catch{return undefined;}}

export default function MentionsPage(){
  const [companies,setCompanies]=useState<Company[]>([]);
  const [company,setCompany]=useState("");
  const [companiesLoading,setCompaniesLoading]=useState(true);
  const [jobs,setJobs]=useState<Summary[]>([]);
  const [queueLoaded,setQueueLoaded]=useState(false);
  const [tracked,setTracked]=useState("");
  const [job,setJob]=useState<Job|null>(null);
  const [runId,setRunId]=useState("");
  const [run,setRun]=useState<Run|null>(null);
  const [worker,setWorker]=useState<{available:boolean;last_seen_at?:string}>({available:false});
  const [error,setError]=useState("");
  const [pollError,setPollError]=useState("");
  const [notice,setNotice]=useState("");
  const [busy,setBusy]=useState(false);
  const [pages,setPages]=useState(3);
  const [budget,setBudget]=useState(90);
  const [refresh,setRefresh]=useState(0);
  useEffect(()=>{
    let stopped=false;
    const params=new URLSearchParams(window.location.search);
    setTracked(params.get("job")||localStorage.getItem("corpo_mentions_job")||"");
    setRunId(params.get("run")||"");
    setCompany(params.get("id_company")||"");
    async function load(){
      setCompaniesLoading(true);
      try{const res=await api.get("/company/mention-watch/companies");if(!stopped)setCompanies(res.companies||[]);}
      catch(e){if(!stopped)setError(errorText(e));}
      finally{if(!stopped)setCompaniesLoading(false);}
    }
    load();window.addEventListener("focus",load);
    return()=>{stopped=true;window.removeEventListener("focus",load);};
  },[]);

  // Read-only polling: no processing step is ever triggered by the browser.
  useEffect(()=>{
    let stopped=false;let timer:ReturnType<typeof setTimeout>|undefined;
    async function poll(){
      try{
        const res=await api.get("/company/watch/mention-jobs");
        if(stopped)return;
        setPollError("");
        setQueueLoaded(true);setJobs(res.jobs||[]);setWorker(res.worker||{available:false});
        if(!tracked&&res.jobs?.length){setTracked(res.jobs[0].id_job);return;}
        if(tracked){const next:Job=await api.get(`/company/watch/mention-jobs/${encodeURIComponent(tracked)}`);if(!stopped)setJob(next);}
        if(runId){const next:Run=await api.get(`/company/watch/mentions/${encodeURIComponent(runId)}`);if(!stopped)setRun(next);}
      }catch(e){if(!stopped)setPollError(errorText(e));}
      finally{if(!stopped)timer=setTimeout(poll,4000);}
    }
    poll();return()=>{stopped=true;if(timer)clearTimeout(timer);};
  },[tracked,runId,refresh]);

  async function selectJob(id:string){
    setTracked(id);setJob(null);setRunId("");setRun(null);
    localStorage.setItem("corpo_mentions_job",id);
    window.history.replaceState(null,"",`?job=${encodeURIComponent(id)}`);
  }
  async function enqueue(path:string,body:unknown={}){
    setBusy(true);setError("");setNotice("");
    try{
      const res=await api.post(path,body);
      await selectJob(res.id_job);
      setNotice(res.reused?(res.company_running?"Cette société est déjà en cours de traitement dans le lot affiché.":res.prioritized_company?"Cette société est déjà prévue : elle est prioritaire après la société en cours.":"La collecte globale est déjà en attente ou en cours. Son suivi est affiché."):"Collecte mise en file. Le serveur poursuit le travail même si vous quittez cette page.");
      setRefresh(v=>v+1);
    }catch(e){setError(errorText(e));}finally{setBusy(false);}
  }
  const options={max_pages:pages,search_budget_seconds:budget,max_candidates:1000,excluded_domains:[]};
  const rows=job?.companies||[];
  const finished=rows.filter(r=>terminal(r.status)).length;
  const added=rows.reduce((sum,row)=>sum+(row.progress?.new_mentions||0),0);
  const imported=run?.results.filter(r=>r.status==="IMPORTED")||[];
  const journal=[...(run?.results||[]),...(run?.resolutions||[])].filter(r=>r.status==="JOURNAL"||r.status==="LIMIT");

  return <div className="space-y-6">
    <header><p className="text-sm text-gray-500">Discovery / Mentions</p><h1 className="text-3xl font-semibold text-ratecard-blue mt-1">Mentions</h1><p className="text-sm text-gray-600 mt-2">Recherches Google News des mentions externes des sociétés suivies. Collecte globale ou individuelle, exécutée côté serveur. Vous pouvez quitter cette page pendant le traitement. La couverture reste non exhaustive.</p></header>
    <section className="bg-white border rounded p-4 space-y-4">
      <div className="flex flex-wrap gap-3 items-center"><button type="button" disabled={busy||companiesLoading||!companies.length} onClick={()=>enqueue("/company/watch/mention-jobs/global",options)} className="bg-ratecard-blue text-white rounded px-4 py-2 disabled:opacity-40">Lancer la collecte globale</button><span className="text-sm text-gray-500">{companiesLoading?"Chargement…":`${companies.length} société(s) active(s) éligible(s)`}</span><Link className="underline text-sm" href="/admin/company">Gérer les sociétés suivies</Link></div>
      <div className="flex flex-wrap gap-3 items-center"><select className={`${control} min-w-[240px]`} value={company} disabled={busy||companiesLoading} onChange={e=>setCompany(e.target.value)}><option value="">Choisir une société</option>{companies.map(c=><option key={c.id_company} value={c.id_company}>{c.name}</option>)}</select><button type="button" disabled={busy||!company} onClick={()=>enqueue(`/company/watch/mention-jobs/company/${encodeURIComponent(company)}`,options)} className="border rounded px-4 py-2 disabled:opacity-40">Lancer pour cette société</button></div>
      <p className="text-xs text-gray-500">Un passage par société, avec reconnaissance de l’existant. Une relance globale est possible une fois le lot terminé. Une société déjà prévue est priorisée sans créer de doublon.</p>
      <details><summary>Options de collecte</summary><div className="flex flex-wrap gap-4 mt-3 text-sm"><label>Pages maximum <input className={`${control} w-20`} type="number" min={1} max={5} value={pages} onChange={e=>setPages(Number(e.target.value))}/></label><label>Budget de recherche (secondes) <input className={`${control} w-24`} type="number" min={30} max={300} value={budget} onChange={e=>setBudget(Number(e.target.value))}/></label></div><p className="text-xs text-gray-500 mt-2">Le budget concerne la recherche ; lecture, qualification et enregistrement viennent ensuite.</p></details>
    </section>
    {queueLoaded&&job&&!terminal(job.status)&&<div className="text-sm space-y-2"><p>{worker.available?"Traitement côté serveur en cours. Vous pouvez quitter cette page.":"Collecte enregistrée. Après une interruption du serveur, utilisez Reprendre le traitement."}</p><button disabled={busy} className="underline" onClick={()=>enqueue(`/company/watch/mention-jobs/${encodeURIComponent(job.id_job)}/resume`)}>Reprendre le traitement</button></div>}
    {notice&&<p role="status" className="text-blue-800">{notice}</p>}{error&&<p role="alert" className="text-red-700">{error}</p>}{pollError&&<p role="status" className="text-amber-800">Suivi momentanément indisponible : {pollError}. Le traitement serveur continue indépendamment de cet écran.</p>}
    {job&&<section className="bg-white border rounded p-4 space-y-4"><div><h2 className="font-semibold">{job.kind==="GLOBAL"?"Collecte globale":"Collecte individuelle"} · {label(job.status)}</h2><p className="text-sm mt-1">{finished}/{rows.length} société(s) terminée(s) · {added} nouvelle(s) mention(s) · créée le {dateText(job.created_at)}</p></div>
      <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="text-left border-b"><th className="p-2">Société</th><th className="p-2">État / étape</th><th className="p-2">Nouvelles mentions</th><th className="p-2">URL connues</th><th className="p-2">Suivi</th></tr></thead><tbody>{rows.map(row=><tr key={row.id_company} className="border-b"><td className="p-2">{row.name}{row.priority_requested&&row.status==="PENDING"&&<span className="text-xs ml-2">Prioritaire</span>}</td><td className="p-2">{label(row.status)}{row.status==="RUNNING"&&row.progress?.stage&&` · ${label(row.progress.stage)}`}{row.error&&<p className="text-xs text-amber-800 mt-1">{row.error}{row.retry_after&&` · reprise à partir de ${dateText(row.retry_after)}`}</p>}{row.message&&<p className="text-xs text-gray-500">{row.message}</p>}</td><td className="p-2">{row.progress?.new_mentions??"—"}</td><td className="p-2">{row.progress?.known_urls??"—"}</td><td className="p-2"><button disabled={!row.progress?.stage} className="underline disabled:opacity-30" onClick={()=>{setRun(null);setRunId(row.id_run);}}>Consulter le passage</button></td></tr>)}</tbody></table></div>
    </section>}
    <details className="bg-white border rounded p-4" open={!job}><summary>Historique des collectes ({jobs.length})</summary><div className="space-y-2 mt-3">{jobs.length===0?<p className="text-sm text-gray-500">Aucune collecte serveur pour le moment.</p>:jobs.map(item=><button key={item.id_job} onClick={()=>selectJob(item.id_job)} className="block w-full text-left border rounded p-3 text-sm">{dateText(item.created_at)} · {item.kind==="GLOBAL"?"Globale":"Individuelle"} · {label(item.status)} · {item.finished}/{item.total} sociétés · {item.new_mentions} mentions{item.current_company&&` · ${item.current_company}`}</button>)}</div></details>
    {run&&<section className="space-y-4"><div className="bg-white border rounded p-4"><h2 className="font-semibold">{run.company_name} · {label(run.status)}</h2><p className="text-sm">{imported.length} nouvelle(s) mention(s) · {journal.length} page(s) au journal.</p>{!terminal(run.status)&&<button type="button" disabled={busy} className="underline text-sm mt-2" onClick={()=>enqueue(`/company/watch/mention-jobs/continue/${encodeURIComponent(run.id_run)}`)}>Reprendre ce passage côté serveur</button>}
      <details className="mt-3"><summary>Couverture et durées</summary><ul className="text-sm mt-2">{run.warnings.map((w,i)=><li key={i}>{w}</li>)}</ul><pre className="text-xs whitespace-pre-wrap mt-2">{JSON.stringify(run.timings||{},null,2)}</pre></details>
      {terminal(run.status)&&<details className="mt-3"><summary>Reprise manuelle (facultatif)</summary><div className="flex flex-wrap gap-4 mt-2 text-sm"><button disabled={busy} className="underline" onClick={()=>enqueue(`/company/watch/mentions/${encodeURIComponent(run.id_run)}/retry-searches`,{search_workers:1})}>Compléter les recherches échouées ou laissées de côté</button><button disabled={busy} className="underline" onClick={()=>enqueue(`/company/watch/mentions/${encodeURIComponent(run.id_run)}/recheck`)}>Réexaminer les URL connues</button></div></details>}
    </div><h3 className="font-semibold">Nouvelles mentions du passage</h3>{imported.map((r,i)=><article key={i} className="bg-white border rounded p-4"><strong>{r.title}</strong><p className="text-sm mt-2">{r.explanation}</p><Link className="underline text-sm" href={`/admin/library/corpo?document=${encodeURIComponent(r.id_document||"")}`}>Consulter dans Library</Link></article>)}
      <details className="bg-white border rounded p-4"><summary>Journal ({journal.length})</summary>{journal.map((r,i)=><div key={i} className="border-t py-2 text-sm"><a className="underline" href={safeUrl(r.resolved_url||r.url)} target="_blank" rel="noreferrer">{r.title||r.url}</a><p>{r.reason}</p>{r.technical_detail&&<p>{r.technical_detail}</p>}{r.qualification_reason&&<p>{r.qualification_reason}</p>}</div>)}</details>
      {!!run.search_errors?.length&&<details className="bg-white border rounded p-4"><summary>Diagnostics des recherches</summary><pre className="whitespace-pre-wrap break-all text-xs mt-2">{JSON.stringify(run.search_errors,null,2)}</pre></details>}
    </section>}
    <MentionConnectorTest companyId={company}/>
    <p className="text-sm"><Link className="underline" href="/admin/library/corpo">Ouvrir Library Corpo</Link></p>
  </div>;
}
