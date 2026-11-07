"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { WatchCompany } from "@/lib/companyWatch";

type Origin={country?:string;language?:string;precision?:string;page?:number;search_date_hint?:string};
type Result = {origins?:Origin[]; reader_selector?:string; text_length?:number; qualification_reason?:string; search_date_hint?:string;resolved_url?:string; publisher?:string; page_nature?:string; date_sources?:{locator:string;value:string}[]; url:string; title:string; status:string; reason?:string; id_document?:string; explanation?:string};
type Run = {engine_version?:string; max_candidates?:number; coverage?:Record<string,{requests:number;occurrences:number;errors:number}>; resolved_candidates?:Result[]; resolutions?:Result[]; id_company:string;search_profile?:string; search_locales?:{country:string;language:string}[]; search_scope?:string;id_run:string; company_name:string; start:string|null; end:string|null; status:string; tasks:unknown[]; candidates:unknown[]; results:Result[]; warnings:string[]};
const control="border rounded px-3 py-2 w-full bg-white";
const errorText=(e:unknown)=>e instanceof Error?e.message:"Erreur de collecte";
function safeUrl(value:string) {try{const u=new URL(value);return ["http:","https:"].includes(u.protocol)?u.href:undefined;}catch{return undefined;}}

function reasonLabel(reason?:string) {
  const labels:Record<string,string>={PUBLICATION_DATE_UNKNOWN:"Article ou page pertinente, mais date de publication non vérifiable",PUBLICATION_DATE_CONFLICT:"Dates de publication contradictoires",OUTSIDE_PUBLICATION_PERIOD:"Publication hors période",EDITORIAL_REGION_UNKNOWN:"Zone éditoriale introuvable — problème de lecture",EDITORIAL_TEXT_TOO_SHORT:"Texte récupéré trop court — problème de lecture",EDITORIAL_TEXT_TOO_LONG:"Texte récupéré trop long — lecture à adapter",CANDIDATE_LIMIT:"Plafond de pages distinctes atteint",REFERENCE_PAGE_NOT_NEWS:"Page de référence ou fiche outil — pas une publication d’actualité identifiée",NO_EDITORIAL_MENTION:"Aucune mention dans le texte éditorial",EDITORIAL_RELEVANCE_UNCERTAIN:"Pertinence éditoriale non confirmée",CORPORATE_DOMAIN:"Publication corporate exclue des mentions externes",DUPLICATE_FINAL_URL:"Même URL finale déjà examinée",QUOTE_NOT_VERIFIED:"Citation non vérifiée"};
  return labels[reason||""]||reason;
}

function warningLabel(value:string) {
  if(value==="CANDIDATE_LIMIT")return "Plafond de pages distinctes atteint après résolution : couverture partielle. Augmenter le plafond de sécurité si nécessaire.";
  if(value==="RAW_URL_SAFETY_LIMIT")return "Limite technique de 5 000 liens intermédiaires atteinte : couverture partielle.";
  if(value==="SEARCH_PAGE_LIMIT")return "Limite de pages de recherche atteinte : des résultats supplémentaires peuvent exister.";
  if(value==="PAGINATION_INFERRED")return "Page suivante demandée explicitement car le fournisseur ne précise pas la pagination.";
  if(value.startsWith("HISTORICAL_SEARCH_MAY_BE_TRUNCATED"))return "Cet historique peut avoir perdu des résultats à cause de l’ancien plafond. Une nouvelle collecte est nécessaire pour compléter la couverture.";
  return value;
}

function category(reason?:string) {
  if(reason==="OUTSIDE_PUBLICATION_PERIOD")return "Hors période";
  if(reason?.startsWith("TECHNICAL_")||reason?.startsWith("EDITORIAL_TEXT_")||reason==="EDITORIAL_REGION_UNKNOWN"||reason==="UNRESOLVED_SEARCH_REDIRECT"||["QUOTE_NOT_VERIFIED","EXPLANATION_INVALID","INVALID_QUALIFICATION"].includes(reason||""))return "Technique / lecture / preuve";
  if(reason?.startsWith("PUBLICATION_DATE_"))return "Date non vérifiable";
  if(reason==="CANDIDATE_LIMIT")return "Limite";
  return "Éditorial";
}
function originsLabel(origins?:Origin[]) {
  const labels=(origins||[]).map(o=>`${o.country||"?"}/${o.language||"?"}`);
  return labels.filter((value,index)=>labels.indexOf(value)===index).join(" · ")||"Provenance non enregistrée dans cet historique";
}

export default function MentionsPage() {
  const [companies,setCompanies]=useState<WatchCompany[]>([]);
  const [company,setCompany]=useState("");
  const [companiesLoading,setCompaniesLoading]=useState(true);
  const companiesSequence=useRef(0);
  
  const [domains,setDomains]=useState("");const [pages,setPages]=useState(3);
  const [run,setRun]=useState<Run|null>(null);const [running,setRunning]=useState(false);
  const [error,setError]=useState("");const [loading,setLoading]=useState(false);
  const inFlight=useRef(false);
  const alive=useRef(true);
  const [busy,setBusy]=useState(false);
  const [journalFilter,setJournalFilter]=useState("Tous");
  async function refreshCompanies() {
    const sequence=++companiesSequence.current;
    setCompaniesLoading(true);
    try {
      const response=await api.get("/company/mention-watch/companies");
      if(!Array.isArray(response.companies))throw new Error("Liste des sociétés éligibles invalide");
      const rows:WatchCompany[]=response.companies;
      if(alive.current&&sequence===companiesSequence.current) {
        setCompanies(rows);
        setCompany(current=>{
          const wanted=current||new URLSearchParams(window.location.search).get("id_company")||"";
          return rows.some(c=>c.id_company===wanted)?wanted:"";
        });
      }
    } catch(e) {
      if(alive.current&&sequence===companiesSequence.current){setCompanies([]);setCompany("");setError(errorText(e));}
    } finally {if(alive.current&&sequence===companiesSequence.current)setCompaniesLoading(false);}
  }
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
  useEffect(()=>{
    let stopped=false;
    refreshCompanies();
    const onFocus=()=>{refreshCompanies();};
    window.addEventListener("focus",onFocus);
    const id=new URLSearchParams(window.location.search).get("run")||localStorage.getItem("corpo_mentions_run");
    if(id)api.get(`/company/watch/mentions/${encodeURIComponent(id)}`).then((r:Run)=>{if(!stopped){setRun(r);setRunning(r.search_scope==="NEWS"&&r.engine_version==="MENTIONS_1_7"&&!["COMPLETE","PARTIAL"].includes(r.status));}}).catch(e=>{if(!stopped)setError(errorText(e));});
    return ()=>{stopped=true;window.removeEventListener("focus",onFocus);};
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
    try{const r:Run=await api.post("/company/watch/mentions/create",{id_company:company,
      excluded_domains:domains.split(/[\s,;]+/).filter(Boolean),max_pages:pages,max_candidates:1000});
      setRun(r);localStorage.setItem("corpo_mentions_run",r.id_run);window.history.replaceState(null,"",`?run=${encodeURIComponent(r.id_run)}`);setRunning(true);
    }catch(e){setError(errorText(e));}finally{setLoading(false);}
  }
  async function recheck() {
    if(!run)return;
    setLoading(true);setError("");
    try {const next:Run=await api.post(`/company/watch/mentions/${encodeURIComponent(run.id_run)}/recheck`,{});setRun(next);setRunning(true);}
    catch(e){setError(errorText(e));}finally{setLoading(false);}
  }
  const imported=run?.results.filter(r=>r.status==="IMPORTED")||[];
  const duplicates=[...(run?.resolutions||[]),...(run?.results||[])].filter(r=>r.reason==="DUPLICATE_FINAL_URL");
  const journal=[...(run?.results||[]).filter(r=>r.status==="JOURNAL"&&r.reason!=="DUPLICATE_FINAL_URL"),
    ...(run?.resolutions||[]).filter(r=>r.status==="JOURNAL"||r.status==="LIMIT")];
  const filteredJournal=journal.filter(r=>journalFilter==="Tous"||category(r.reason)===journalFilter);
  const modern=run?.engine_version==="MENTIONS_1_7";
  const locales=run?.search_locales||[];
  const known=(run?.resolutions||[]).filter(r=>r.status==="KNOWN");
  return <div className="space-y-6">
    <header><Link href="/admin/discovery/corpo" className="underline">← Discovery Corpo</Link><h1 className="text-2xl font-semibold mt-4">Mentions externes → Library</h1>
      <p className="text-sm text-gray-600 mt-2">Google Actualités uniquement · socle commun de 18 couples pays / langue pour les nouvelles collectes · résultats qualifiés automatiquement. La couverture internationale reste non exhaustive.</p></header>
    <div className="flex flex-wrap gap-3 items-center text-sm"><Link className="underline" href="/admin/company">Gérer l’éligibilité dans Companies</Link><button type="button" disabled={companiesLoading} onClick={()=>refreshCompanies()} className="border rounded px-3 py-2 disabled:opacity-40">Actualiser les sociétés</button><span>{companiesLoading?"Chargement des sociétés éligibles…":`${companies.length} société(s) éligible(s)`}</span></div>
    {!companiesLoading&&companies.length===0&&<p className="text-amber-800">Aucune société éligible. Activez la veille Mentions dans Companies pour lancer une nouvelle collecte. Les historiques restent consultables ci-dessous.</p>}
    <form onSubmit={e=>{e.preventDefault();launch();}} className="bg-white border rounded p-4 space-y-4">
      <div className="grid md:grid-cols-3 gap-4">
        <label>Société suivie<select required disabled={running||loading||companiesLoading} className={control} value={company} onChange={e=>setCompany(e.target.value)}><option value="">{companiesLoading?"Chargement…":"Choisir une société éligible"}</option>{companies.map(c=><option key={c.id_company} value={c.id_company}>{c.name}</option>)}</select></label>
        <label>Autres domaines à exclure<input disabled={running||loading} className={control} value={domains} placeholder="autre-domaine.com" onChange={e=>setDomains(e.target.value)}/></label>
        <label>Pages par recherche<input disabled={running||loading} className={control} type="number" min={1} max={5} value={pages} onChange={e=>setPages(Number(e.target.value))}/></label>
      </div>
      <p className="text-xs text-gray-500">Une recherche simple par pays / langue, sans filtre de dates : 18 recherches initiales, jusqu’à 54 pages avec le réglage de trois pages. Les domaines corporate sont exclus après collecte. Les URL déjà intégrées ou définitivement exclues sont reconnues avant lecture. Les erreurs temporaires restent réessayables. Plafond de sécurité : 1 000 nouvelles pages distinctes. La collecte avance tant que cette page est ouverte et reprend à sa réouverture. Aucun tri manuel requis.</p>
      <button disabled={loading||running||busy||companiesLoading||!company} className="bg-ratecard-blue text-white rounded px-4 py-2 disabled:opacity-40">{loading?"Création…":"Lancer la collecte"}</button>
    </form>
    {error&&<p role="alert" className="text-red-700">{error}</p>}
    {run&&<section className="space-y-4">
      <div className="bg-white border rounded p-4"><strong>{run.company_name} · {modern ? "Collecte sans filtre de dates" : `${run.start || "?"} → ${run.end || "?"}`}</strong>
        {!modern&&<p className="text-amber-800 mt-2">Historique du moteur précédent : lancer une nouvelle collecte pour retrouver les résultats éventuellement perdus par l’ancien plafond. Un réexamen améliore la lecture des seules URL déjà conservées.</p>}
        {run.search_scope!=="NEWS"&&<p className="text-amber-800 mt-2">Collecte historique Web + News : résultats conservés. Lancez une nouvelle collecte pour appliquer le périmètre News uniquement.</p>}
        <p className="text-xs text-gray-500 mt-2">Périmètre de cette collecte : {run.search_locales ? `${run.search_locales.length} couples pays / langue` : run.search_scope === "NEWS" ? "historique US / France" : "historique Web + News"}.</p>
        <p>{run.status} · {run.tasks.length} recherche(s) restante(s) · {modern ? `${run.resolutions?.length||0}/${run.candidates.length} liens résolus · ${run.results.length}/${run.resolved_candidates?.length||0} pages distinctes examinées` : `${run.results.length}/${run.candidates.length} liens traités`} · {imported.length} vers Library · {journal.length} exclusions · {duplicates.length} doublons regroupés · {known.length} URL déjà traitées</p>
        {modern&&run.search_scope==="NEWS"&&!["COMPLETE","PARTIAL"].includes(run.status)&&<button type="button" className="border rounded px-3 py-2 mt-2" onClick={()=>{setError("");setRunning(v=>!v);}}>{running?"Suspendre après l’étape en cours":"Continuer la collecte"}</button>}
        {!!run.warnings.length&&<details className="mt-3"><summary>Couverture et avertissements ({run.warnings.length})</summary><ul>{run.warnings.map((w,i)=><li key={i}>{warningLabel(w)}</li>)}</ul></details>}
      </div>
      {run.search_scope==="NEWS"&&["COMPLETE","PARTIAL"].includes(run.status)&&<button disabled={loading||busy||companiesLoading||!companies.some(c=>c.id_company===run.id_company)} type="button" className="border rounded px-3 py-2 disabled:opacity-40" onClick={recheck}>Réexaminer les URL (sans nouvelle recherche Google)</button>}
      {modern&&<details className="bg-white border rounded p-4"><summary>Apport des recherches par pays / langue</summary>
        <p className="text-xs text-gray-500 my-2">Un article retrouvé dans plusieurs zones figure dans chacune : ces colonnes ne s’additionnent pas. Pays et langue indiquent la recherche effectuée, pas l’origine de l’article.</p>
        <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr><th className="text-left">Recherche</th><th>Requêtes</th><th>Résultats Google</th><th>Pages retenues</th><th>Vers Library</th><th>Erreurs</th></tr></thead>
        <tbody>{locales.map(locale=>{
          const key=`${locale.country}/${locale.language}`;const stats=run.coverage?.[key];
          const matches=(row:Result)=>(row.origins||[]).some(o=>o.country===locale.country&&o.language===locale.language);
          return <tr key={key} className="border-t"><td>{key}</td><td className="text-center">{stats?.requests??"—"}</td><td className="text-center">{stats?.occurrences??"—"}</td><td className="text-center">{(run.resolved_candidates||[]).filter(matches).length}</td><td className="text-center">{imported.filter(matches).length}</td><td className="text-center">{stats?.errors??"—"}</td></tr>;
        })}</tbody></table></div></details>}
      {!!known.length&&<details className="bg-white border rounded p-4"><summary>URL déjà traitées ({known.length})</summary><p className="text-xs text-gray-500 my-2">Reconnues sans nouvelle qualification IA. Les mentions déjà intégrées restent consultables dans la Library.</p>{known.map((r,i)=><p key={i} className="border-t py-2 text-sm break-all">{r.title||r.url}{r.id_document&&<> · <Link className="underline" href={`/admin/library/corpo?document=${encodeURIComponent(r.id_document)}`}>Consulter</Link></>}</p>)}</details>}
      <h2 className="font-semibold">Nouvelles mentions ajoutées</h2>
      {imported.map((r,i)=><article key={i} className="bg-white border rounded p-4"><strong>{r.title}</strong><p>{r.explanation}</p><p className="text-xs text-gray-500 my-2">Recherches d’origine : {originsLabel(r.origins)}</p><Link className="underline" href={`/admin/library/corpo?document=${encodeURIComponent(r.id_document||"")}`}>Consulter dans la Library</Link></article>)}
      <details className="bg-white border rounded p-4"><summary>Journal des exclusions ({journal.length})</summary><p className="text-sm text-gray-600 my-2">Distinguer les exclusions éditoriales, les dates et les problèmes techniques. Les doublons sont regroupés à part ; aucun tri manuel obligatoire.</p>
        <label className="block mb-3">Afficher <select value={journalFilter} onChange={e=>setJournalFilter(e.target.value)} className="border rounded px-3 py-2">{["Tous","Éditorial","Hors période","Date non vérifiable","Technique / lecture / preuve","Limite"].map(c=><option key={c}>{c}</option>)}</select></label>
        {filteredJournal.map((r,i)=><div key={i} className="border-t py-2 break-all"><a className="underline" href={safeUrl(r.resolved_url||r.url)} target="_blank" rel="noreferrer">{r.title||r.url}</a><p className="text-xs text-gray-500">{r.resolved_url||r.url}</p><p className="text-xs text-gray-500">{category(r.reason)} · Recherches : {originsLabel(r.origins)}</p>{r.search_date_hint&&<p className="text-xs text-gray-500">Date Google News (indice) : {r.search_date_hint}</p>}<p className="text-sm">{reasonLabel(r.reason)}</p>{r.qualification_reason&&<p className="text-sm">Motif proposé par la qualification IA : {r.qualification_reason}</p>}{r.reader_selector&&<p className="text-xs">Lecture : {r.reader_selector} · {r.text_length??0} caractères</p>}{!!r.date_sources?.length&&<p className="text-xs">Dates de parution détectées : {r.date_sources.map(d=>`${d.value} (${d.locator})`).join(" · ")}</p>}</div>)}
      </details>
      <details className="bg-white border rounded p-4"><summary>Doublons regroupés ({duplicates.length})</summary><p className="text-xs text-gray-500 my-2">Ces liens ne consomment pas le plafond des pages distinctes et ne constituent pas des rejets éditoriaux.</p>{duplicates.map((r,i)=><p key={i} className="border-t py-2 text-sm break-all">{r.resolved_url||r.url} · {originsLabel(r.origins)}</p>)}</details>
    </section>}
  </div>;
}
