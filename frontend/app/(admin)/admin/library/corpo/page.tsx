"use client";

import { useEffect, useRef, useState } from "react";
import { listCorpoLibrary, getCorpoLibraryDocument } from "@/lib/companyWatch";
import type { CorpoLibraryDocument, CorpoLibraryDetail } from "@/lib/companyWatch";

const button = "border rounded px-3 py-2 text-sm disabled:opacity-50";
const message = (error: unknown) => error instanceof Error ? error.message : "Erreur de chargement";
const date = (value?: string) => value ? new Date(value).toLocaleString("fr-FR", {timeZone:"Europe/Paris"}) : "—";
function safeUrl(value?: string) {
  try { const url = new URL(value || ""); return ["http:","https:"].includes(url.protocol) ? url.href : undefined; }
  catch { return undefined; }
}

export default function CorpoLibraryPage() {
  const [rows,setRows] = useState<CorpoLibraryDocument[]>([]);
  const [offset,setOffset] = useState(0);
  const [hasMore,setHasMore] = useState(false);
  const [revision,setRevision] = useState(0);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState("");
  const [documentId,setDocumentId] = useState("");
  const [unitOffset,setUnitOffset] = useState(0);
  const [detail,setDetail] = useState<CorpoLibraryDetail | null>(null);
  const [detailLoading,setDetailLoading] = useState(false);
  const [detailError,setDetailError] = useState("");
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
    let cancelled=false; setLoading(true); setError("");
    listCorpoLibrary(offset).then(result => {
      if (!cancelled) {setRows(result.items);setHasMore(result.has_more);}
    }).catch(e=>{if(!cancelled)setError(message(e));}).finally(()=>{if(!cancelled)setLoading(false);});
    return ()=>{cancelled=true;};
  },[offset,revision]);
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
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {loading ? <p>Chargement…</p> : !rows.length && !error ? <p>Aucune publication importée.</p> : <div className="border rounded bg-white overflow-x-auto">
      <table className="w-full text-sm text-left"><thead className="bg-gray-50"><tr>
        {['Société / point','Publication','Parution','État','Informations',''].map((label,i)=><th key={i} className="p-3">{label}</th>)}
      </tr></thead><tbody>{rows.map(row=><tr key={row.id_document} className="border-t align-top">
        <td className="p-3">{row.company_name}<div className="text-gray-500">{row.watch_label}</div></td>
        <td className="p-3 max-w-xl"><p className="font-medium">{row.title}</p><p>{row.author_name}</p>
          <a className="underline break-all text-ratecard-blue" href={safeUrl(row.source_url)} target="_blank" rel="noopener noreferrer">Source originale</a></td>
        <td className="p-3 whitespace-nowrap">{date(row.published_at)}</td>
        <td className="p-3">{row.extraction_status==='COMPLETE'?'Importé':row.extraction_status==='ERROR'?'Erreur':'En cours'}
          {row.extraction_error && <p className="text-red-700">{row.extraction_error}</p>}</td>
        <td className="p-3">{row.unit_count}</td><td className="p-3"><button className={button} onClick={()=>{setUnitOffset(0);setDocumentId(row.id_document);}}>Consulter</button></td>
      </tr>)}</tbody></table>
    </div>}
    <div className="flex justify-end gap-2"><button className={button} disabled={loading||offset===0} onClick={()=>setOffset(v=>Math.max(0,v-50))}>Précédent</button>
      <button className={button} disabled={loading||!hasMore} onClick={()=>setOffset(v=>v+50)}>Suivant</button></div>
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
