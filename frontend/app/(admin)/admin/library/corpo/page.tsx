"use client";

import { useEffect, useRef, useState } from "react";
import { getCorpoLibraryDocument } from "@/lib/companyWatch";
import type { CorpoLibraryDocument, CorpoLibraryDetail, CorpoLibraryFilters, WatchCompany } from "@/lib/companyWatch";

import {api} from "@/lib/api";
type EditorialFields = {
  document_type?: string;
  editorial_status?: string;
  editorial_reason?: string;
  qualification_verdict?: string | null;
  qualification_type?: string | null;
  qualification_motif?: string | null;
};

type QualificationCount = {
  role: "EMPLOYEE" | "CORPORATE";
  verdict: string | null;
  post_type: string | null;
  total: number;
};

const postTypes: Record<string, string> = {
  EVENEMENT: "Événement",
  THOUGHT_LEADERSHIP: "Thought leadership",
  PRODUIT_OU_PARTENARIAT: "Produit ou partenariat",
  CAS_CLIENT_OU_RETOUR_EXPERIENCE: "Cas client ou retour d’expérience",
  OFFRE_EMPLOI: "Offre d’emploi",
  VIE_ENTREPRISE: "Vie d’entreprise",
  PERSONNEL: "Personnel",
  AUTRE: "Autre",
  INDETERMINE: "Indéterminé",
};

const verdictLabels: Record<string, string> = {
  SIGNAL_SOCIETE: "Go · Signal société",
  PRISE_DE_PAROLE_METIER: "Go · Prise de parole métier",
  BRUIT: "No go",
  A_VERIFIER: "À vérifier",
  CORPORATE: "Qualifié",
};

const isGo = (verdict: string | null) =>
  verdict === "SIGNAL_SOCIETE" || verdict === "PRISE_DE_PAROLE_METIER";

function qualificationLabel(post: EditorialFields) {
  const verdict = post.qualification_verdict;
  const type = post.qualification_type;
  return [
    verdict ? (verdictLabels[verdict] ?? verdict) : "En attente de qualification",
    type ? (postTypes[type] ?? type) : null,
  ].filter(Boolean).join(" · ");
}

function QualificationTypes({ rows }: { rows: QualificationCount[] }) {
  const counts = new Map<string, number>();
  for (const row of rows) {
    const type = row.post_type ?? "INDETERMINE";
    counts.set(type, (counts.get(type) ?? 0) + row.total);
  }
  const types = Array.from(counts.entries());
  types.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  if (types.length === 0) return null;

  const items = types.map(([type, count]) => (
    <li key={type}>{postTypes[type] ?? type} <strong>{count}</strong></li>
  ));
  return <ul className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">{items}</ul>;
}

function QualificationSummary({ rows }: { rows: QualificationCount[] }) {
  if (rows.length === 0) return null;

  const employee = rows.filter(row => row.role === "EMPLOYEE");
  const corporate = rows.filter(row => row.role === "CORPORATE");
  const total = (items: QualificationCount[]) => items.reduce((sum, row) => sum + row.total, 0);
  const go = employee.filter(row => isGo(row.verdict));
  const employeeTotal = total(employee);
  const employeePending = total(employee.filter(row => row.verdict === null));
  const corporateTotal = total(corporate);
  const corporateQualified = corporate.filter(row => row.verdict !== null);
  const corporateDone = total(corporateQualified);

  const employeeCounts = [
    { label: "Go", count: total(go) },
    { label: "No go", count: total(employee.filter(row => row.verdict === "BRUIT")) },
    { label: "À vérifier", count: total(employee.filter(row => row.verdict === "A_VERIFIER")) },
    { label: "En attente", count: employeePending },
  ];
  const cards = employeeCounts.map(({ label, count }) => (
    <div key={label} className="rounded bg-gray-50 p-2">
      <dt>{label}</dt>
      <dd className="font-semibold">{count}</dd>
    </div>
  ));

  const employeeSection = employeeTotal > 0 ? (
    <div>
      <h3 className="font-medium">Salariés</h3>
      <p className="text-sm text-gray-600">{employeeTotal - employeePending} qualifiés sur {employeeTotal}</p>
      <dl className="my-2 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">{cards}</dl>
      {go.length > 0 ? <p className="text-sm font-medium">Types des Go</p> : null}
      <QualificationTypes rows={go} />
    </div>
  ) : null;

  const corporateSection = corporateTotal > 0 ? (
    <div>
      <h3 className="font-medium">Corporate</h3>
      <p className="text-sm text-gray-600">
        {corporateDone} qualifiés sur {corporateTotal} · {corporateTotal - corporateDone} en attente
      </p>
      <QualificationTypes rows={corporateQualified} />
    </div>
  ) : null;

  return (
    <section className="space-y-4 rounded border bg-white p-4" aria-label="Bilan des qualifications LinkedIn">
      <div>
        <h2 className="font-semibold">Qualifications LinkedIn</h2>
        <p className="text-sm text-gray-500">Bilan de la sélection avant les filtres Verdict et Type principal.</p>
      </div>
      {employeeSection}
      {corporateSection}
    </section>
  );
}

type EditorialFilters=CorpoLibraryFilters & {editorialStatus:string; qualification:string; postType:string};
async function listCorpoLibrary(offset:number,filters:EditorialFilters):Promise<{items:(CorpoLibraryDocument & EditorialFields)[];has_more:boolean;total:number;global_total:number;companies:WatchCompany[];qualification_summary?:QualificationCount[]}>{
 const params=new URLSearchParams({offset:String(offset),limit:"50",with_summary:"true",editorial_status:filters.editorialStatus});
 const values={q:filters.q,id_company:filters.companyId,sort:filters.sort,direction:filters.direction,status:filters.status,published_from:filters.publishedFrom,published_to:filters.publishedTo,document_type:filters.documentType,qualification:filters.qualification,post_type:filters.postType};
 Object.entries(values).forEach(([key,value])=>{if(value)params.set(key,value);});
 return api.get(`/company/watch/library/list?${params.toString()}`);
}
const initialFilters: Required<EditorialFilters> = {
  editorialStatus:"ACTIVE",documentType:"",qualification:"",postType:"", q:"", companyId:"", sort:"published_at", direction:"desc", status:"", publishedFrom:"", publishedTo:"",
};
const control="border rounded px-3 py-2 bg-white w-full";
const button = "border rounded px-3 py-2 text-sm disabled:opacity-50";
const message = (error: unknown) => error instanceof Error ? error.message : "Erreur de chargement";
const date = (value?: string) => value ? new Date(value).toLocaleString("fr-FR", {timeZone:"Europe/Paris"}) : "—";
function safeUrl(value?: string) {
  try { const url = new URL(value || ""); return ["http:","https:"].includes(url.protocol) ? url.href : undefined; }
  catch { return undefined; }
}

export default function CorpoLibraryPage() {
  const [draft,setDraft]=useState({...initialFilters});
  const [filters,setFilters]=useState({...initialFilters});
  const [companies,setCompanies]=useState<WatchCompany[]>([]);
  const [qualificationCounts,setQualificationCounts]=useState<QualificationCount[]>([]);
  const [counts,setCounts]=useState<{global:number;selected:number}|null>(null);
  const [rows,setRows] = useState<(CorpoLibraryDocument & EditorialFields)[]>([]);
  const [offset,setOffset] = useState(0);
  const [hasMore,setHasMore] = useState(false);
  const [revision,setRevision] = useState(0);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState("");
  const [documentId,setDocumentId] = useState("");
  const [unitOffset,setUnitOffset] = useState(0);
  const [detail,setDetail] = useState<(CorpoLibraryDetail & EditorialFields) | null>(null);
  const [detailLoading,setDetailLoading] = useState(false);
  const [detailError,setDetailError] = useState("");
  const [editorialBusy,setEditorialBusy]=useState("");
  const [editorialError,setEditorialError]=useState("");
  const [editorialNotice,setEditorialNotice]=useState("");
  const editorialLock=useRef(false);
  async function changeEditorial(id:string,title:string,withdrawn:boolean){
    if(editorialLock.current)return;
    const verb=withdrawn?"Retirer":"Restaurer";
    if(!window.confirm(`${verb} « ${title} » ${withdrawn?"de":"dans"} la Library active ? ${withdrawn?"La décision sera mémorisée pour cette société et cette URL, preuves comprises. Une restauration restera possible.":"La publication et ses preuves redeviendront utilisables."}`))return;
    const reason=window.prompt("Motif éditorial (facultatif) :","");if(reason===null)return;
    editorialLock.current=true;setEditorialBusy(id);setEditorialError("");setEditorialNotice("");
    try{
      const res=await api.post(`/company/watch/library/${encodeURIComponent(id)}/editorial`,{is_withdrawn:withdrawn,reason:reason.trim().slice(0,1000)||null});
      if(res.status!=="ok")throw new Error(res.message||"Décision non confirmée.");
      setEditorialNotice(withdrawn?"Publication retirée de la Library active.":"Publication restaurée.");
      setRevision(v=>v+1);
    }catch(e){setEditorialError(message(e));}finally{editorialLock.current=false;setEditorialBusy("");}
  }
  const sequence=useRef(0);
  const dialogRef=useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog=dialogRef.current;
    if (!dialog) return;
    if (documentId && !dialog.open) dialog.showModal();
    if (!documentId && dialog.open) dialog.close();
    if (!documentId) return;
    const previousOverflow=document.body.style.overflow;
    document.body.style.overflow="hidden";
    return () => { document.body.style.overflow=previousOverflow; };
  }, [documentId]);

  useEffect(() => { setDocumentId(new URLSearchParams(window.location.search).get("document") || ""); },[]);
  useEffect(() => {
    let cancelled=false; setLoading(true); setError(""); setRows([]); setHasMore(false);setCounts(null);setQualificationCounts([]);
    listCorpoLibrary(offset,filters).then(result => {
      if(typeof result.total!=="number"||typeof result.global_total!=="number"||!Array.isArray(result.companies))throw new Error("Compteurs indisponibles : vérifier le déploiement du backend.");
      if(!cancelled){setCompanies(result.companies);setQualificationCounts(result.qualification_summary ?? []);setCounts({global:result.global_total,selected:result.total});}
      if (!cancelled) {if(!result.items.length&&offset>0){setOffset(result.total>0?Math.floor((result.total-1)/50)*50:0);return;}setRows(result.items);setHasMore(result.has_more);}
    }).catch(e=>{if(!cancelled)setError(message(e));}).finally(()=>{if(!cancelled)setLoading(false);});
    return ()=>{cancelled=true;};
  },[offset,revision,filters]);
  useEffect(()=>{
    const request=++sequence.current;
    if (!documentId) {setDetail(null);setDetailLoading(false);return;}
    setDetailLoading(true);setDetailError("");setDetail(null);
    getCorpoLibraryDocument(documentId,unitOffset).then(result=>{
      if(sequence.current===request)setDetail(result);
    }).catch(e=>{if(sequence.current===request)setDetailError(message(e));})
      .finally(()=>{if(sequence.current===request)setDetailLoading(false);});
    return ()=>{sequence.current++;};
  },[documentId,unitOffset,revision]);

  return <div className="space-y-6">
    <header className="flex justify-between items-start gap-4"><div>
      <p className="text-sm text-gray-500">Library / Corpo</p><h1 className="text-3xl font-semibold text-ratecard-blue">Publications documentaires</h1>
      <p className="text-gray-500 mt-2">Publications, informations atomiques et preuves. Aucun sujet documentaire.</p>
    </div><div className="space-x-3"><a className="underline" href="/admin/library">Library</a><a className="underline" href="/admin/discovery/corpo">Discovery Corpo</a>
      <button className={button} onClick={()=>setRevision(v=>v+1)}>Actualiser</button></div></header>
    <form className="bg-white border rounded p-4 space-y-4" onSubmit={event=>{
      event.preventDefault();
      if (draft.publishedFrom && draft.publishedTo && draft.publishedFrom>draft.publishedTo) {
        setError("La date de début doit précéder la date de fin.");return;
      }
      setOffset(0);setFilters({...draft,q:draft.q.trim()});
    }}>
        <label className="block text-sm">Type<select className={control} value={draft.documentType} onChange={e=>setDraft({
          ...draft,documentType:e.target.value,companyId:"",
          ...(e.target.value === "MENTION" ? {qualification:"",postType:""} : {}),
        })}><option value="">Tous</option><option value="CORPORATE">Publications de veille</option><option value="MENTION">Mentions externes</option></select></label>
      <label className="block space-y-1"><span className="text-sm font-medium">Rechercher</span>
        <input className={control} type="search" maxLength={500} placeholder="Titre, auteur, société, information ou citation…"
          value={draft.q} onChange={e=>setDraft(v=>({...v,q:e.target.value}))}/>
        <span className="text-xs text-gray-500">Recherche littérale dans les titres, auteurs, sociétés, points de collecte, URL, informations extraites et citations. Le texte source intégral n’est pas indexé par ce filtre.</span>
      </label>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <label className="space-y-1"><span className="text-sm">État éditorial</span><select className={control} value={draft.editorialStatus} onChange={e=>setDraft(v=>({...v,editorialStatus:e.target.value}))}><option value="ACTIVE">Publications actives</option><option value="WITHDRAWN">Publications retirées</option><option value="ALL">Actives et retirées</option></select></label>
        <label className="space-y-1"><span className="text-sm">Société</span><select className={control} value={draft.companyId} onChange={e=>setDraft(v=>({...v,companyId:e.target.value}))}>
          <option value="">Toutes les sociétés présentes dans ce périmètre</option>{companies.map(c=><option key={c.id_company} value={c.id_company}>{c.name}</option>)}
        </select></label>
        <label className="space-y-1"><span className="text-sm">État</span><select className={control} value={draft.status} onChange={e=>setDraft(v=>({...v,status:e.target.value}))}>
          <option value="">Tous</option><option value="COMPLETE">Importé</option><option value="PENDING">En cours</option><option value="ERROR">Erreur</option>
        </select></label>
        <label className="space-y-1"><span className="text-sm">Trier par</span><select className={control} value={draft.sort} onChange={e=>setDraft(v=>({...v,sort:e.target.value}))}>
          <option value="published_at">Date de parution</option><option value="imported_at">Date d’import</option><option value="company">Société</option><option value="title">Titre</option><option value="units">Nombre d’informations</option>
        </select></label>
        <label className="space-y-1"><span className="text-sm">Parution à partir du</span><input className={control} type="date" value={draft.publishedFrom} onChange={e=>setDraft(v=>({...v,publishedFrom:e.target.value}))}/></label>
        <label className="space-y-1"><span className="text-sm">Parution jusqu’au</span><input className={control} type="date" value={draft.publishedTo} onChange={e=>setDraft(v=>({...v,publishedTo:e.target.value}))}/></label>
        <label className="space-y-1"><span className="text-sm">Ordre</span><select className={control} value={draft.direction} onChange={e=>setDraft(v=>({...v,direction:e.target.value}))}>
          <option value="desc">Décroissant / Z → A</option><option value="asc">Croissant / A → Z</option>
        </select></label>
      </div>
      {draft.documentType !== "MENTION" && <div className="grid gap-3 sm:grid-cols-2">
        <label className="block text-sm">Verdict
          <select className={control} value={draft.qualification} onChange={e=>setDraft(v=>({...v,qualification:e.target.value}))}>
            <option value="">Tous</option>
            <option value="GO">Go · Salariés</option>
            <option value="NO_GO">No go · Salariés</option>
            <option value="REVIEW">À vérifier · Salariés</option>
            <option value="PENDING">En attente de qualification</option>
          </select>
        </label>
        <label className="block text-sm">Type principal
          <select className={control} value={draft.postType} onChange={e=>setDraft(v=>({...v,postType:e.target.value}))}>
            <option value="">Tous</option>
            {Object.entries(postTypes).map(([value,label])=><option key={value} value={value}>{label}</option>)}
          </select>
        </label>
      </div>}
      <div className="flex gap-3 items-center"><button type="submit" className="bg-ratecard-blue text-white rounded px-4 py-2">Rechercher / appliquer</button>
        <button type="button" className={button} onClick={()=>{setDraft({...initialFilters});setFilters({...initialFilters});setOffset(0);}}>Réinitialiser</button>
        <span className="text-sm text-gray-500">Filtres et tri appliqués à l’ensemble de la Library Corpo.</span>
      </div>
    </form>
    <div role="status" aria-live="polite" className="bg-white border rounded p-4 flex flex-wrap gap-x-8 gap-y-2">
      <p><span className="text-gray-500">Total global{filters.documentType==='MENTION'?' des Mentions':filters.documentType==='CORPORATE'?' des publications de veille':''} {filters.editorialStatus==='ACTIVE'?'actives':filters.editorialStatus==='WITHDRAWN'?'retirées':'(actives et retirées)'} : </span><strong>{counts?counts.global.toLocaleString('fr-FR'):loading?'…':'—'}</strong></p>
      <p><span className="text-gray-500">Résultats des filtres appliqués : </span><strong>{counts?counts.selected.toLocaleString('fr-FR'):loading?'…':'—'}</strong></p>
      <p className="w-full text-xs text-gray-500">Comptages sur l’ensemble des résultats, pas seulement les 50 lignes de la page. Le total global conserve le type et l’état éditorial choisis.</p>
    </div>
    <QualificationSummary rows={qualificationCounts} />
    {editorialNotice&&<p role="status" className="text-green-800">{editorialNotice}</p>}
    {editorialError&&<p role="alert" className="text-red-700">{editorialError}</p>}
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {loading ? <p>Chargement…</p> : !rows.length && !error ? <p>Aucune publication ne correspond aux filtres.</p> : <div className="border rounded bg-white overflow-x-auto">
      <table className="w-full text-sm text-left"><thead className="bg-gray-50"><tr>
        {['Société / point','Publication','Parution','État','Informations',''].map((label,i)=><th key={i} className="p-3">{label}</th>)}
      </tr></thead><tbody>{rows.map(row=><tr key={row.id_document} className="border-t align-top">
        <td className="p-3">{row.company_name}<div className="text-gray-500">{row.document_type === "MENTION" ? "Mention externe" : row.watch_label}</div></td>
        <td className="p-3 max-w-xl"><p className="font-medium">{row.title}</p><p>{row.author_name}</p>
          {row.document_type === "LINKEDIN" && <p className="mt-1 text-sm font-medium text-ratecard-blue">{qualificationLabel(row)}</p>}
          <a className="underline break-all text-ratecard-blue" href={safeUrl(row.source_url)} target="_blank" rel="noopener noreferrer">Source originale</a></td>
        <td className="p-3 whitespace-nowrap">{date(row.published_at)}</td>
        <td className="p-3">{row.editorial_status==='WITHDRAWN'?'Retirée · ':''}{row.extraction_status==='COMPLETE'?'Importé':row.extraction_status==='ERROR'?'Erreur':row.extraction_status==='PENDING'?'Disponible · à analyser':'En cours'}
          {row.extraction_error && <p className="text-red-700">{row.extraction_error}</p>}</td>
        <td className="p-3">{row.unit_count}</td><td className="p-3"><button className={button} onClick={()=>{setUnitOffset(0);setDocumentId(row.id_document);}}>Consulter</button>{(row.document_type==='MENTION'||row.document_type==='LINKEDIN')&&<button disabled={!!editorialBusy} className={`${button} ml-2 ${row.editorial_status==='WITHDRAWN'?'':'text-red-700'}`} onClick={()=>void changeEditorial(row.id_document,row.title,row.editorial_status!=='WITHDRAWN')}>{editorialBusy===row.id_document?'Enregistrement…':row.editorial_status==='WITHDRAWN'?'Restaurer':'Retirer de la Library'}</button>}</td>
      </tr>)}</tbody></table>
    </div>}
    <div className="flex justify-end gap-2 items-center"><span className="text-sm text-gray-500">Page {Math.floor(offset/50)+1}</span><button className={button} disabled={loading||!!error||offset===0} onClick={()=>setOffset(v=>Math.max(0,v-50))}>Précédent</button>
      <button className={button} disabled={loading||!!error||!hasMore} onClick={()=>setOffset(v=>v+50)}>Suivant</button></div>
    <dialog ref={dialogRef} aria-labelledby="corpo-document-title"
      onClose={()=>setDocumentId("")}
      className="w-[calc(100%-2rem)] max-w-5xl max-h-[90vh] overflow-y-auto rounded-lg border bg-white p-6 shadow-xl backdrop:bg-black/40">
      <header className="flex justify-between items-start gap-4 border-b pb-4 mb-4">
        <h2 id="corpo-document-title" className="text-xl font-semibold text-ratecard-blue">{detail?.title || "Publication Library"}</h2>
        <button type="button" className={button} onClick={()=>setDocumentId("")}>Fermer</button>
      </header>
    {detailLoading && <p role="status">Chargement de la publication…</p>}
    {detailError && <div role="alert" className="text-red-700 space-y-3"><p>{detailError}</p>
      <button type="button" className={button} onClick={()=>setRevision(v=>v+1)}>Réessayer</button></div>}
    {detail && <section className="border rounded bg-white p-5 space-y-4">
      {(detail.document_type==='MENTION'||detail.document_type==='LINKEDIN')&&<div className="border rounded p-3 space-y-2"><p className="text-sm">{detail.editorial_status==='WITHDRAWN'?'Publication retirée de la Library active.':'Publication active.'}{detail.editorial_reason&&` Motif : ${detail.editorial_reason}`}</p><button disabled={!!editorialBusy} className={button} onClick={()=>void changeEditorial(detail.id_document,detail.title,detail.editorial_status!=='WITHDRAWN')}>{detail.editorial_status==='WITHDRAWN'?'Restaurer':'Retirer de la Library'}</button>{editorialError&&<p role="alert" className="text-red-700">{editorialError}</p>}</div>}
      {detail.document_type === "LINKEDIN" && <div className="rounded border p-3">
        <p className="font-medium">{qualificationLabel(detail)}</p>
        {detail.qualification_motif && <p className="mt-1 text-sm text-gray-700">{detail.qualification_motif}</p>}
      </div>}
      <p className="text-sm">Parution : {date(detail.published_at)} · Auteur : {detail.author_name || detail.author_id || 'Non renseigné'}</p>
      {detail.monitored_account_url && <p className="text-sm">Compte suivi : {detail.monitored_account_url}. La date d’un éventuel relais reste indéterminée.</p>}
      <a className="underline text-ratecard-blue" href={safeUrl(detail.source_url)} target="_blank" rel="noopener noreferrer">Source originale</a>
      <details><summary className="cursor-pointer font-medium">Texte capturé</summary><pre className="whitespace-pre-wrap text-sm mt-3 max-h-96 overflow-auto">{detail.text}</pre></details>
      <h3 className="font-semibold">Informations et preuves</h3><p className="text-sm text-amber-800">{detail.warning}</p>
      {!detail.units.length && <p>Aucune information sur cette page. L’extraction peut être en cours ou ne contenir aucune unité.</p>}
      {detail.units.map(unit=><article key={unit.unit_id} className="border-t pt-3 space-y-2">
        <p>{unit.fact || 'Candidat sans fait exploitable'}</p><blockquote className="border-l-4 pl-3 text-gray-600 whitespace-pre-wrap">{unit.quote || 'Citation absente'}</blockquote>
        <p className="text-xs text-gray-500">{unit.verification_status} · {unit.kind} · {unit.source_locator} · {unit.verification_reason}</p>
      </article>)}
      <div className="flex gap-2"><button className={button} disabled={detailLoading||unitOffset===0} onClick={()=>setUnitOffset(v=>Math.max(0,v-100))}>Informations précédentes</button>
        <button className={button} disabled={detailLoading||!detail.has_more} onClick={()=>setUnitOffset(v=>v+100)}>Informations suivantes</button></div>
    </section>}
    </dialog>
  </div>;
}
