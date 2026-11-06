"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { listWatchCompanies } from "@/lib/companyWatch";
import type { WatchCompany } from "@/lib/companyWatch";

type Result = {url:string; title:string; status:string; reason?:string; id_document?:string; explanation?:string};
type Run = {id_run:string; company_name:string; start:string; end:string; status:string; tasks:unknown[]; candidates:unknown[]; results:Result[]; warnings:string[]};
const control="border rounded px-3 py-2 w-full bg-white";
const errorText=(e:unknown)=>e instanceof Error?e.message:"Erreur de collecte";
function safeUrl(value:string) {try{const u=new URL(value);return ["http:","https:"].includes(u.protocol)?u.href:undefined;}catch{return undefined;}}

export default function MentionsPage() {
  const [companies,setCompanies]=useState<WatchCompany[]>([]);
  const [company,setCompany]=useState("");
  const [start,setStart]=useState("");const [end,setEnd]=useState("");
  const [domains,setDomains]=useState("");const [pages,setPages]=useState(2);
  const [run,setRun]=useState<Run|null>(null);const [running,setRunning]=useState(false);
  const [error,setError]=useState("");const [loading,setLoading]=useState(false);
  const inFlight=useRef(false);
  const alive=useRef(true);
  const [busy,setBusy]=useState(false);
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
  useEffect(()=>{
    let stopped=false;
    listWatchCompanies().then(rows=>{if(!stopped)setCompanies(rows);}).catch(e=>{if(!stopped)setError(errorText(e));});
    const id=new URLSearchParams(window.location.search).get("run")||localStorage.getItem("corpo_mentions_run");
    if(id)api.get(`/company/watch/mentions/${encodeURIComponent(id)}`).then((r:Run)=>{if(!stopped){setRun(r);setRunning(!["COMPLETE","PARTIAL"].includes(r.status));}}).catch(e=>{if(!stopped)setError(errorText(e));});
    return ()=>{stopped=true;};
  },[]);
  useEffect(()=>{
    if(!running||!run||["COMPLETE","PARTIAL"].includes(run.status))return;
    const timer=window.setTimeout(async()=>{
      if(inFlight.current)return;
      inFlight.current=true;setBusy(true);
      try{const next:Run=await api.post(`/company/watch/mentions/${encodeURIComponent(run.id_run)}/step`,{});
        if(alive.current){setRun(next);if(["COMPLETE","PARTIAL"].includes(next.status))setRunning(false);}
      }catch(e){if(alive.current){setError(errorText(e));setRunning(false);}}
      finally{inFlight.current=false;if(alive.current)setBusy(false);}
    },600);
    return ()=>{window.clearTimeout(timer);};
  },[running,run]);
  async function launch() {
    setLoading(true);setError("");
    try{const r:Run=await api.post("/company/watch/mentions/create",{id_company:company,period_start:start,period_end:end,
      excluded_domains:domains.split(/[\s,;]+/).filter(Boolean),max_pages:pages,max_candidates:100});
      setRun(r);localStorage.setItem("corpo_mentions_run",r.id_run);window.history.replaceState(null,"",`?run=${encodeURIComponent(r.id_run)}`);setRunning(true);
    }catch(e){setError(errorText(e));}finally{setLoading(false);}
  }
  const imported=run?.results.filter(r=>r.status==="IMPORTED")||[];
  const journal=run?.results.filter(r=>r.status==="JOURNAL")||[];
  return <div className="space-y-6">
    <header><Link href="/admin/discovery/corpo" className="underline">← Discovery Corpo</Link><h1 className="text-2xl font-semibold mt-4">Mentions externes → Library</h1>
      <p className="text-sm text-gray-600 mt-2">Web et News · US / anglais et France / français · résultats qualifiés automatiquement. Ces localisations ne garantissent pas une couverture mondiale exhaustive.</p></header>
    <form onSubmit={e=>{e.preventDefault();launch();}} className="bg-white border rounded p-4 space-y-4">
      <div className="grid md:grid-cols-3 gap-4">
        <label>Société<select required disabled={running||loading} className={control} value={company} onChange={e=>setCompany(e.target.value)}><option value="">Choisir</option>{companies.map(c=><option key={c.id_company} value={c.id_company}>{c.name}</option>)}</select></label>
        <label>Du<input required disabled={running||loading} className={control} type="date" value={start} onChange={e=>setStart(e.target.value)}/></label>
        <label>Au (inclus)<input required disabled={running||loading} className={control} type="date" min={start} value={end} onChange={e=>setEnd(e.target.value)}/></label>
        <label>Autres domaines à exclure<input disabled={running||loading} className={control} value={domains} placeholder="axeptio.eu" onChange={e=>setDomains(e.target.value)}/></label>
        <label>Pages par recherche<input disabled={running||loading} className={control} type="number" min={1} max={5} value={pages} onChange={e=>setPages(Number(e.target.value))}/></label>
      </div>
      <p className="text-xs text-gray-500">Le domaine du site de la société est exclu automatiquement. Huit recherches initiales ; pagination plafonnée. La collecte avance tant que cette page est ouverte et reprend à sa réouverture. Aucun tri manuel requis.</p>
      <button disabled={loading||running||busy} className="bg-ratecard-blue text-white rounded px-4 py-2 disabled:opacity-40">{loading?"Création…":"Lancer la collecte"}</button>
    </form>
    {error&&<p role="alert" className="text-red-700">{error}</p>}
    {run&&<section className="space-y-4">
      <div className="bg-white border rounded p-4"><strong>{run.company_name} · {run.start} → {run.end}</strong>
        <p>{run.status} · {run.tasks.length} recherche(s) restante(s) · {run.results.length}/{run.candidates.length} URL traitée(s) · {imported.length} vers Library · {journal.length} dans le journal</p>
        {!["COMPLETE","PARTIAL"].includes(run.status)&&<button type="button" className="border rounded px-3 py-2 mt-2" onClick={()=>{setError("");setRunning(v=>!v);}}>{running?"Suspendre après l’étape en cours":"Continuer la collecte"}</button>}
        {!!run.warnings.length&&<details className="mt-3"><summary>Couverture et avertissements ({run.warnings.length})</summary><ul>{run.warnings.map((w,i)=><li key={i}>{w}</li>)}</ul></details>}
      </div>
      <h2 className="font-semibold">Mentions ajoutées</h2>
      {imported.map((r,i)=><article key={i} className="bg-white border rounded p-4"><strong>{r.title}</strong><p>{r.explanation}</p><Link className="underline" href={`/admin/library/corpo?document=${encodeURIComponent(r.id_document||"")}`}>Consulter dans la Library</Link></article>)}
      <details className="bg-white border rounded p-4"><summary>Journal technique ({journal.length}) — éléments exclus</summary><p className="text-sm text-gray-600 my-2">Ce journal explique les exclusions. Il ne constitue pas une liste à valider manuellement.</p>
        {journal.map((r,i)=><div key={i} className="border-t py-2 break-all"><a className="underline" href={safeUrl(r.url)} target="_blank" rel="noreferrer">{r.title||r.url}</a><p className="text-sm">{r.reason}</p></div>)}
      </details>
    </section>}
  </div>;
}
