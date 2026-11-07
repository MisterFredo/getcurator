"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { WatchCompany } from "@/lib/companyWatch";

type Origin={country?:string;language?:string;precision?:string;page?:number;search_date_hint?:string};
type Result = {technical_detail?:string;failure_count?:number;origins?:Origin[]; reader_selector?:string; text_length?:number; qualification_reason?:string; search_date_hint?:string;resolved_url?:string; publisher?:string; page_nature?:string; date_sources?:{locator:string;value:string}[]; url:string; title:string; status:string; reason?:string; id_document?:string; explanation?:string};
type SerpDiagnostics={stage?:string;http_status?:number;content_type?:string;body_bytes?:number;elapsed_seconds?:number;response_excerpt?:string;response_headers?:Record<string,string>;provider_request_id?:string;request_payload?:Record<string,unknown>;upstream_status_code?:number;upstream_headers?:Record<string,string>};
type SearchError={resolved?:boolean;task:{country:string;language:string;page?:number;offset?:number};reason:string;diagnostics?:SerpDiagnostics};
type ProbeResult={country:string;language:string;target_url:string;ok:boolean;count?:number;reason?:string;diagnostics?:SerpDiagnostics;sample?:{title?:string;link?:string;url?:string}[]};
type ProbeReport={company_name?:string;mode:string;workers:number;elapsed_seconds:number;results:ProbeResult[]};
type Run = {deferred_searches?:unknown[];search_budget_seconds?:number;profile_rotation?:number;search_errors?:SearchError[];timings?:Record<string,number>; runtime_version?:string;engine_version?:string; max_candidates?:number; coverage?:Record<string,{requests:number;occurrences:number;errors:number;successes?:number}>; resolved_candidates?:Result[]; resolutions?:Result[]; id_company:string;search_profile?:string; search_locales?:{country:string;language:string}[]; search_scope?:string;id_run:string; company_name:string; start:string|null; end:string|null; status:string; tasks:unknown[]; candidates:unknown[]; results:Result[]; warnings:string[]};
const control="border rounded px-3 py-2 w-full bg-white";
const errorText=(e:unknown)=>e instanceof Error?e.message:"Erreur de collecte";
function safeUrl(value:string) {try{const u=new URL(value);return ["http:","https:"].includes(u.protocol)?u.href:undefined;}catch{return undefined;}}

function reasonLabel(reason?:string) {
  const labels:Record<string,string>={EDITORIAL_TEXT_INSUFFICIENT:"Texte trop court pour conclure à l’absence de mention — lecture à réessayer",DUPLICATE_FAILURE:"Même page en échec — tentative regroupée",TECHNICAL_NON_HTML:"La réponse reçue n’est pas une page HTML",TECHNICAL_REDIRECT_LOOP:"Boucle de redirections HTTP",TECHNICAL_REDIRECT_LIMIT:"Limite de redirections HTTP atteinte",TECHNICAL_HTML_SIZE_LIMIT:"Page reçue supérieure à la limite de 5 Mo",TECHNICAL_URL_OR_RESPONSE_INVALID:"URL ou réponse invalide — consulter le détail",TECHNICAL_READ_TIMEOUT:"Délai de lecture dépassé",TECHNICAL_CONNECT_TIMEOUT:"Délai de connexion dépassé",PUBLICATION_DATE_UNKNOWN:"Article ou page pertinente, mais date de publication non vérifiable",PUBLICATION_DATE_CONFLICT:"Dates de publication contradictoires",OUTSIDE_PUBLICATION_PERIOD:"Publication hors période",EDITORIAL_REGION_UNKNOWN:"Zone éditoriale introuvable — problème de lecture",EDITORIAL_TEXT_TOO_SHORT:"Texte récupéré trop court — problème de lecture",EDITORIAL_TEXT_TOO_LONG:"Texte récupéré trop long — lecture à adapter",CANDIDATE_LIMIT:"Plafond de pages distinctes atteint",REFERENCE_PAGE_NOT_NEWS:"Page de référence ou fiche outil — pas une publication d’actualité identifiée",NO_EDITORIAL_MENTION:"Aucune mention dans le texte éditorial",EDITORIAL_RELEVANCE_UNCERTAIN:"Pertinence éditoriale non confirmée",CORPORATE_DOMAIN:"Publication corporate exclue des mentions externes",DUPLICATE_FINAL_URL:"Même URL finale déjà examinée",QUOTE_NOT_VERIFIED:"Citation non vérifiée"};
  return labels[reason||""]||reason;
}

function warningLabel(value:string) {
  if(value==="SEARCH_TIME_BUDGET")return "Budget de recherche atteint. Les publications récupérées sont conservées ; les pays changent de priorité au prochain passage.";
  if(value.includes("SERP_CAPTCHA"))return "Une recherche Google a rencontré une protection ; les autres résultats sont conservés.";
  if(value.includes("SERP_RATE_LIMIT"))return "Une recherche a été limitée par le fournisseur ; pas de relance automatique.";
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

function SerpDetails({details}:{details?:SerpDiagnostics}) {
  if(!details)return null;
  return <div className="text-xs space-y-2 mt-2"><p>Étape : {details.stage||"inconnue"} · HTTP : {details.http_status??"inconnu"} · Type : {details.content_type||"absent"} · Corps reçu : {details.body_bytes??"?"} octets · Durée : {details.elapsed_seconds??"?"} s</p>
    {details.provider_request_id&&<p>Identifiant Bright Data : {details.provider_request_id}</p>}
    {!!Object.keys(details.response_headers||{}).length&&<pre className="whitespace-pre-wrap break-all">{JSON.stringify(details.response_headers,null,2)}</pre>}
    {details.upstream_status_code!=null&&<p>HTTP cible dans l’enveloppe : {details.upstream_status_code}</p>}
    {!!Object.keys(details.upstream_headers||{}).length&&<pre className="whitespace-pre-wrap break-all">{JSON.stringify(details.upstream_headers,null,2)}</pre>}
    {details.response_excerpt&&<pre className="whitespace-pre-wrap break-all">{details.response_excerpt}</pre>}
    {details.request_payload&&<details><summary>Requête JSON envoyée — sans clé API</summary><pre className="whitespace-pre-wrap break-all">{JSON.stringify(details.request_payload,null,2)}</pre></details>}
  </div>;
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
  const [retryWorkers,setRetryWorkers]=useState(1);
  const [probeBusy,setProbeBusy]=useState(false);
  const [probeUrl,setProbeUrl]=useState("");
  const [probeFormat,setProbeFormat]=useState("raw");
  const [probeParsed,setProbeParsed]=useState(true);
  const [probeReports,setProbeReports]=useState<ProbeReport[]>([]);
  const [probeReadyAt,setProbeReadyAt]=useState(0);
  const [clock,setClock]=useState(Date.now());
  useEffect(()=>{if(!probeReadyAt)return;const timer=window.setInterval(()=>setClock(Date.now()),1000);return()=>window.clearInterval(timer);},[probeReadyAt]);
  async function testConnector(mode:"SINGLE"|"PARALLEL") {
    const id=company||run?.id_company;if(!id)return;
    setProbeBusy(true);setError("");
    try {
      const result:ProbeReport=await api.post("/company/watch/mentions/probe",{id_company:id,mode,target_url:probeUrl.trim()||null,response_format:probeFormat,parsed_response:probeParsed});
      if(alive.current)setProbeReports(previous=>[...previous,result]);
    }catch(e){if(alive.current)setError(errorText(e));}
    finally{if(alive.current){setProbeBusy(false);setProbeReadyAt(Date.now()+15000);setClock(Date.now());}}
  }
  async function retrySearches() {
    if(!run)return;
    setLoading(true);setError("");
    try{const next:Run=await api.post(`/company/watch/mentions/${encodeURIComponent(run.id_run)}/retry-searches`,{search_workers:retryWorkers});setRun(next);setRunning(true);}
    catch(e){setError(errorText(e));}finally{setLoading(false);}
  }
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
      excluded_domains:domains.split(/[\s,;]+/).filter(Boolean),max_pages:pages,max_candidates:1000,search_budget_seconds:90});
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
  const duplicates=[...(run?.resolutions||[]),...(run?.results||[])].filter(r=>["DUPLICATE_FINAL_URL","DUPLICATE_FAILURE"].includes(r.reason||""));
  const rawJournal=[...(run?.results||[]).filter(r=>r.status==="JOURNAL"&&!["DUPLICATE_FINAL_URL","DUPLICATE_FAILURE"].includes(r.reason||"")),
    ...(run?.resolutions||[]).filter(r=>r.status==="JOURNAL"||r.status==="LIMIT")];
  // Also regroup historical failures that already had a confirmed final URL.
  // Keep unrelated opaque Google URLs separate; a matching title is not proof.
  const journal:Result[]=[];
  const failureGroups=new Map<string,Result>();
  rawJournal.forEach(row=>{
    if(row.reason?.startsWith("TECHNICAL_")&&row.resolved_url){
      const first=failureGroups.get(row.resolved_url);
      if(first){
        first.failure_count=(first.failure_count||1)+(row.failure_count||1);
        first.origins=[...(first.origins||[]),...(row.origins||[])];
        duplicates.push({...row,status:"DUPLICATE",reason:"DUPLICATE_FAILURE"});return;
      }
      const copy={...row,origins:[...(row.origins||[])]};
      failureGroups.set(row.resolved_url,copy);journal.push(copy);
    }else journal.push(row);
  });
  const filteredJournal=journal.filter(r=>journalFilter==="Tous"||category(r.reason)===journalFilter);
  const modern=run?.engine_version==="MENTIONS_1_7";
  const locales=run?.search_locales||[];
  const known=(run?.resolutions||[]).filter(r=>r.status==="KNOWN");
  const requestCount=Object.values(run?.coverage||{}).reduce((sum,stats)=>sum+stats.requests,0);
  const successCount=Object.values(run?.coverage||{}).reduce((sum,stats)=>sum+(stats.successes??Math.max(0,stats.requests-stats.errors)),0);
  const statusLabel=({SEARCHING:"Recherche des publications",RESOLVING:"Lecture des nouvelles pages",QUALIFYING:"Qualification et enregistrement",COMPLETE:"Passage terminé",PARTIAL:"Passage terminé — couverture partielle"} as Record<string,string>)[run?.status||""]||run?.status;
  const duration=(seconds:number)=>`${Math.floor(seconds/60)} min ${Math.round(seconds%60)} s`;
  return <div className="space-y-6">
    <header><Link href="/admin/discovery/corpo" className="underline">← Discovery Corpo</Link><h1 className="text-2xl font-semibold mt-4">Mentions externes → Library</h1>
      <p className="text-sm text-gray-600 mt-2">Une veille internationale utile, sans exigence d’exhaustivité : les résultats disponibles alimentent Library et les nouveautés sont recherchées au passage suivant.</p></header>
    <div className="flex flex-wrap gap-3 items-center text-sm"><Link className="underline" href="/admin/company">Gérer l’éligibilité dans Companies</Link><button type="button" disabled={companiesLoading} onClick={()=>refreshCompanies()} className="border rounded px-3 py-2 disabled:opacity-40">Actualiser les sociétés</button><span>{companiesLoading?"Chargement des sociétés éligibles…":`${companies.length} société(s) éligible(s)`}</span></div>
    {!companiesLoading&&companies.length===0&&<p className="text-amber-800">Aucune société éligible. Activez la veille Mentions dans Companies pour lancer une nouvelle collecte. Les historiques restent consultables ci-dessous.</p>}
    <form onSubmit={e=>{e.preventDefault();launch();}} className="bg-white border rounded p-4 space-y-4">
      <div className="max-w-xl">        <label>Société suivie<select required disabled={running||loading||probeBusy||companiesLoading} className={control} value={company} onChange={e=>setCompany(e.target.value)}><option value="">{companiesLoading?"Chargement…":"Choisir une société éligible"}</option>{companies.map(c=><option key={c.id_company} value={c.id_company}>{c.name}</option>)}</select></label></div>
      <p className="text-sm text-gray-600">18 pays / langues · {pages} page(s) maximum par recherche · budget de recherche de 90 secondes. Toutes les URL récupérées sont ensuite traitées. Les publications déjà connues sont reconnues sans nouvelle qualification.</p>
      <p className="text-xs text-gray-500">Gardez cette page ouverte pendant le passage. Vous pouvez suspendre puis reprendre. Le prochain passage effectuera de nouvelles recherches et reconnaîtra les URL connues.</p>
      <details><summary className="text-sm cursor-pointer">Options de collecte</summary><div className="grid md:grid-cols-2 gap-4 mt-3">        <label>Autres domaines à exclure<input disabled={running||loading} className={control} value={domains} placeholder="autre-domaine.com" onChange={e=>setDomains(e.target.value)}/></label>        <label>Pages par recherche<input disabled={running||loading} className={control} type="number" min={1} max={5} value={pages} onChange={e=>setPages(Number(e.target.value))}/></label></div></details>
      <button disabled={loading||running||busy||probeBusy||companiesLoading||!company} className="bg-ratecard-blue text-white rounded px-4 py-2 disabled:opacity-40">{loading?"Création…":run?"Lancer un nouveau passage":"Lancer le passage"}</button>
    </form>
    {error&&<p role="alert" className="text-red-700">{error}</p>}
    {run&&<section className="space-y-4">
      <div className="bg-white border rounded p-4"><strong>{run.company_name} · {modern ? "Collecte sans filtre de dates" : `${run.start || "?"} → ${run.end || "?"}`}</strong>
        {!modern&&<p className="text-amber-800 mt-2">Historique du moteur précédent : lancer une nouvelle collecte pour retrouver les résultats éventuellement perdus par l’ancien plafond. Un réexamen améliore la lecture des seules URL déjà conservées.</p>}
        {run.search_scope!=="NEWS"&&<p className="text-amber-800 mt-2">Collecte historique Web + News : résultats conservés. Lancez une nouvelle collecte pour appliquer le périmètre News uniquement.</p>}
        <p className="text-xs text-gray-500 mt-2">Périmètre de cette collecte : {run.search_locales ? `${run.search_locales.length} couples pays / langue` : run.search_scope === "NEWS" ? "historique US / France" : "historique Web + News"}.</p>
        <p className="mt-2 font-medium">{statusLabel}</p>
        <div className="flex flex-wrap gap-5 mt-3 text-sm"><span><strong>{imported.length}</strong> nouvelle(s) mention(s)</span><span><strong>{known.length}</strong> URL déjà traitées</span><span><strong>{journal.length}</strong> page(s) au journal</span></div>
        <p className="text-xs text-gray-500 mt-2">{successCount} appel(s) de recherche réussi(s) sur {requestCount} · {run.deferred_searches?.length||0} appel(s) laissé(s) de côté à la limite de temps.</p>
        {["COMPLETE","PARTIAL"].includes(run.status)&&<p className="text-sm text-gray-600 mt-2">{imported.length?"Les nouvelles mentions sont disponibles dans Library.":"Ce passage n’a ajouté aucune nouvelle mention."} Les résultats réussis sont conservés. Aucune relance manuelle n’est nécessaire pour poursuivre la veille au prochain passage.</p>}
        <details className="mt-3 text-sm"><summary>Détail de progression</summary>        <p>{run.status} · {requestCount} appel(s) de recherche effectué(s) · {run.tasks.length} en attente · {modern ? `${run.resolutions?.length||0}/${run.candidates.length} liens résolus · ${run.results.length}/${run.resolved_candidates?.length||0} pages distinctes examinées` : `${run.results.length}/${run.candidates.length} liens traités`} · {imported.length} vers Library · {journal.length} exclusions · {duplicates.length} doublons regroupés · {known.length} URL déjà traitées</p></details>
        {modern&&run.search_scope==="NEWS"&&!["COMPLETE","PARTIAL"].includes(run.status)&&<button type="button" className="border rounded px-3 py-2 mt-2" onClick={()=>{setError("");setRunning(v=>!v);}}>{running?"Suspendre après l’étape en cours":"Continuer la collecte"}</button>}
        {run.timings&&<details className="mt-3"><summary>Durées mesurées depuis V1.8</summary><ul className="text-sm space-y-1 mt-2">{[
          ["search_seconds","Recherche Google / Bright Data"],
          ["resolution_seconds","Lecture et résolution des liens"],
          ["qualification_upload_seconds","Qualification et préparation des captures (en parallèle)"],
          ["bigquery_seconds","Imports BigQuery par lots"],
          ["registry_seconds","Mise à jour du registre des URL"],
          ["finalization_seconds","Finalisation"],
        ].map(([key,label])=><li key={key}>{label} : {duration(run.timings?.[key]||0)}</li>)}</ul><p className="text-xs text-gray-500 mt-2">Durées de traitement des étapes, hors pauses du navigateur et sauvegardes de progression. Les durées des sauvegardes figurent dans les logs. La préparation inclut le cache, la lecture du texte, l’IA et les uploads.</p></details>}
        {!!run.warnings.length&&<details className="mt-3"><summary>Couverture et avertissements ({run.warnings.length})</summary><ul>{run.warnings.map((w,i)=><li key={i}>{warningLabel(w)}</li>)}</ul></details>}
      </div>
      <details className="bg-white border rounded p-4"><summary>Diagnostics et reprise manuelle (facultatif)</summary><div className="space-y-4 mt-3">      {run.search_scope==="NEWS"&&["COMPLETE","PARTIAL"].includes(run.status)&&<button disabled={loading||busy||probeBusy||companiesLoading||!companies.some(c=>c.id_company===run.id_company)} type="button" className="border rounded px-3 py-2 disabled:opacity-40" onClick={recheck}>Réexaminer les URL (sans nouvelle recherche Google)</button>}
      {["COMPLETE","PARTIAL"].includes(run.status)&&(!!run.search_errors?.some(entry=>!entry.resolved)||!!run.deferred_searches?.length)&&<div className="bg-white border rounded p-4 flex flex-wrap gap-3 items-center"><label>Appels simultanés pour la reprise <select className="border rounded px-3 py-2" value={retryWorkers} disabled={loading||busy||probeBusy} onChange={e=>setRetryWorkers(Number(e.target.value))}><option value={1}>1 — diagnostic isolé</option><option value={4}>4 — traitement parallèle</option></select></label><button type="button" className="border rounded px-3 py-2 disabled:opacity-40" disabled={loading||busy||probeBusy||!companies.some(c=>c.id_company===run.id_company)} onClick={retrySearches}>Compléter manuellement les recherches</button><p className="text-xs text-gray-500">Facultatif : reprend les appels échoués ou laissés de côté, avec un nouveau budget de {run.search_budget_seconds||90} secondes. Les résultats acquis sont conservés.</p></div>}
      {!!run.search_errors?.length&&<details className="bg-white border rounded p-4"><summary>Diagnostics des recherches ({run.search_errors.filter(entry=>!entry.resolved).length} non résolues / {run.search_errors.length} erreurs historiques)</summary><p className="text-xs text-gray-500 my-2">Une réponse vide n’est jamais assimilée à une recherche sans résultat. Les extraits sont limités et les secrets usuels masqués.</p>{run.search_errors.map((entry,i)=><div key={i} className="border-t py-2 text-sm"><strong>{entry.task.country}/{entry.task.language} · page {entry.task.page||1} · {entry.reason} · {entry.resolved?"Résolue après reprise":"Non résolue"}</strong><SerpDetails details={entry.diagnostics}/></div>)}</details>}
      </div></details>
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
        {filteredJournal.map((r,i)=><div key={i} className="border-t py-2 break-all"><a className="underline" href={safeUrl(r.resolved_url||r.url)} target="_blank" rel="noreferrer">{r.title||r.url}</a><p className="text-xs text-gray-500">{r.resolved_url||r.url}</p><p className="text-xs text-gray-500">{category(r.reason)} · Recherches : {originsLabel(r.origins)}</p>{r.search_date_hint&&<p className="text-xs text-gray-500">Date Google News (indice) : {r.search_date_hint}</p>}<p className="text-sm">{reasonLabel(r.reason)}</p>{r.technical_detail&&<p className="text-sm">Détail technique : {r.technical_detail}</p>}{(r.failure_count||0)>1&&<p className="text-xs text-gray-500">{r.failure_count} liens regroupés vers cette page en échec.</p>}{r.qualification_reason&&<p className="text-sm">Motif proposé par la qualification IA : {r.qualification_reason}</p>}{r.reader_selector&&<p className="text-xs">Lecture : {r.reader_selector} · {r.text_length??0} caractères</p>}{!!r.date_sources?.length&&<p className="text-xs">Dates de parution détectées : {r.date_sources.map(d=>`${d.value} (${d.locator})`).join(" · ")}</p>}</div>)}
      </details>
      <details className="bg-white border rounded p-4"><summary>Doublons regroupés ({duplicates.length})</summary><p className="text-xs text-gray-500 my-2">Ces liens ne consomment pas le plafond des pages distinctes et ne constituent pas des rejets éditoriaux. Les répétitions vers une même page en échec sont également regroupées lorsque son URL finale est connue.</p>{duplicates.map((r,i)=><p key={i} className="border-t py-2 text-sm break-all">{r.resolved_url||r.url} · {originsLabel(r.origins)}</p>)}</details>
    </section>}
    <details className="bg-white border rounded p-4"><summary>Outils techniques — test du connecteur (facultatif)</summary><div className="space-y-3 mt-3"><p className="text-sm text-gray-600">Choisissez une société ci-dessus. Le test utilise le même connecteur que la collecte, sans cache ni import Library. Un test isolé effectue un appel ; le test parallèle en effectue quatre sur des pays/langues distincts.</p>
      <label className="block">URL Google News copiée du Playground (facultatif)<input className={control} value={probeUrl} disabled={probeBusy} onChange={e=>setProbeUrl(e.target.value)} placeholder="Vide : recherche de la société en FR/fr"/></label>
      <div className="flex flex-wrap gap-4 items-center"><label>Format API <select className="border rounded px-3 py-2" value={probeFormat} disabled={probeBusy} onChange={e=>setProbeFormat(e.target.value)}><option value="raw">raw</option><option value="json">json</option></select></label><label><input type="checkbox" checked={probeParsed} disabled={probeBusy} onChange={e=>setProbeParsed(e.target.checked)}/> Envoyer data_format: parsed</label></div>
      <div className="flex flex-wrap gap-3"><button type="button" className="border rounded px-3 py-2 disabled:opacity-40" disabled={probeBusy||running||busy||loading||clock<probeReadyAt||!(company||run?.id_company)} onClick={()=>testConnector("SINGLE")}>{probeBusy?"Test en cours…":"Tester un appel isolé"}</button><button type="button" className="border rounded px-3 py-2 disabled:opacity-40" disabled={probeBusy||running||busy||loading||clock<probeReadyAt||!(company||run?.id_company)} onClick={()=>testConnector("PARALLEL")}>Comparer avec quatre appels simultanés</button></div>
      {clock<probeReadyAt&&<p className="text-xs text-gray-500">Prochain test dans {Math.ceil((probeReadyAt-clock)/1000)} s pour espacer les requêtes répétées.</p>}
      {probeReports.map((report,i)=><div key={i} className="border-t pt-3 space-y-2"><strong>{report.company_name} · {report.mode==="SINGLE"?"Appel isolé":"Quatre appels simultanés"} · {report.elapsed_seconds} s</strong>{report.results.map((result,j)=><div key={j} className="border rounded p-3"><strong>{result.country}/{result.language} · {result.ok?`${result.count||0} résultats`:result.reason}</strong><SerpDetails details={result.diagnostics}/>{result.sample?.map((row,k)=><p key={k} className="text-sm">{row.title}</p>)}</div>)}</div>)}
    </div></details>
  </div>;
}
