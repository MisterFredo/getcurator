"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";

type EvidenceUnit = { page: number | null; fact: string; quote: string; kind: string; geography: string | null; period: string | null; needs_review: boolean; status: "VERIFIED" | "NEEDS_REVIEW" | "REJECTED"; reason: string; match_score: number; candidate_index: number };
type ExtractBatch = { status: string; start_page: number; end_page: number; page_count: number; next_page: number | null; units: EvidenceUnit[]; counts: Record<string, number>; candidate_count: number; rejected_unverified: number; warning: string };
type Source = { source_id: string; name: string; domain?: string | null; universe_id?: string | null; acquisition_mode?: string | null };
type Page = { page: number; char_count: number; image_count: number; needs_visual_review: boolean; preview: string };
type Inspection = { status: string; document_hash: string; filename: string; page_count: number; title: string | null; author: string | null; pages: Page[]; low_text_pages: number[]; visual_review_pages: number[] };
type Topic = { page_count: number; pages: { page: number; mentions: number }[] };
type Mapping = { status: string; document: { document_hash: string; filename: string; page_count: number; title: string | null; author: string | null }; quality: { low_text_pages: number[]; visual_review_pages: number[] }; sections: { page: number; heading_candidate: string }[]; topics: Record<string, Topic>; note: string };
const TOPIC_NAMES: Record<string, string> = { artificial_intelligence: "Intelligence artificielle", marketplaces: "Marketplaces", payments: "Paiements", logistics: "Logistique", regulation: "Réglementation", sustainability: "Développement durable", ecommerce_market: "Marché e-commerce" };
const normalize = (s: string) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase().replace(/\s+/g, " ");

export default function PDFStudio() {
  const [file, setFile] = useState<File | null>(null);
  const [units, setUnits] = useState<EvidenceUnit[]>([]);
  const [nextPage, setNextPage] = useState<number | null>(1);
  const [extracting, setExtracting] = useState(false);
  const [filterStatus, setFilterStatus] = useState<"ALL" | EvidenceUnit["status"]>("ALL");
  const [rejected, setRejected] = useState(0);
  const counts = useMemo(() => ({
    VERIFIED: units.filter(u => u.status === "VERIFIED").length,
    NEEDS_REVIEW: units.filter(u => u.status === "NEEDS_REVIEW").length,
    REJECTED: units.filter(u => u.status === "REJECTED").length,
  }), [units]);
  const visibleUnits = useMemo(() => units.filter(u => filterStatus === "ALL" || u.status === filterStatus), [units, filterStatus]);
  const stopRef = useRef(false);
  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [mapping, setMapping] = useState<Mapping | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(true);
  const [sourceMode, setSourceMode] = useState<"existing" | "new">("existing");
  const [sourceId, setSourceId] = useState("");
  const [sourceName, setSourceName] = useState("");
  const [sourceDomain, setSourceDomain] = useState("");
  const [sourceUniverse, setSourceUniverse] = useState("");
  const [documentTitle, setDocumentTitle] = useState("");
  const [documentYear, setDocumentYear] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState<"inspect" | "map" | "create" | null>(null);
  const [error, setError] = useState("");
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);
  const [showPages, setShowPages] = useState(false);
  const topics = useMemo(() => Object.entries(mapping?.topics || {}).sort((a, b) => b[1].page_count - a[1].page_count), [mapping]);
  const duplicate = useMemo(() => sources.find(s => normalize(s.name) === normalize(sourceName)), [sources, sourceName]);
  const selectedSource = sources.find(s => s.source_id === sourceId);

  useEffect(() => {
    let active = true;
    api.get("/source/list").then((res: { sources?: Source[] }) => {
      if (active) setSources(res.sources || []);
    }).catch((e: unknown) => { if (active) setError(e instanceof Error ? e.message : "Impossible de charger les sources."); })
      .finally(() => { if (active) setSourcesLoading(false); });
    return () => { active = false; };
  }, []);

  function changeFile(next: File | null) {
    stopRef.current = true; setUnits([]); setNextPage(1); setRejected(0); setFilterStatus("ALL");
    setFile(next); setInspection(null); setMapping(null); setConfirmed(false);
    setDocumentTitle(""); setDocumentYear(""); setError(""); setShowPages(false);
  }

  async function upload(action: "inspect" | "map"): Promise<Inspection | Mapping> {
    if (!file) throw new Error("Sélectionne un PDF.");
    const data = new FormData(); data.append("file", file);
    return api.postForm(`/discovery/pdf-studio/${action}`, data);
  }

  async function inspect() {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf") || file.size > 30 * 1024 * 1024) { setError("PDF requis, 30 Mo maximum."); return; }
    setBusy("inspect"); setError("");
    try {
      const result = await upload("inspect") as Inspection;
      setInspection(result); setMapping(null); setConfirmed(false); setUnits([]); setNextPage(1); setRejected(0); setFilterStatus("ALL");
      setDocumentTitle(result.title?.trim() || file.name.replace(/\.pdf$/i, "").replace(/[_-]+/g, " "));
      const year = (result.title || file.name).match(/\b20\d{2}\b/);
      setDocumentYear(year?.[0] || "");
    } catch (e) { setError(e instanceof Error ? e.message : "Erreur d'inspection."); }
    finally { setBusy(null); }
  }

  async function createSource() {
    if (!sourceName.trim()) { setError("Indique le nom de l'éditeur."); return; }
    if (duplicate) { setError(`La source « ${duplicate.name} » existe déjà. Sélectionne-la.`); return; }
    setBusy("create"); setError("");
    try {
      const res = await api.post("/source/create", {
        name: sourceName.trim(), type_source: "PUBLISHER", domain: sourceDomain.trim() || null,
        universe_id: sourceUniverse.trim() || null, acquisition_mode: "PDF_MANUAL",
      });
      if (!res.source_id) throw new Error("Identifiant de source absent de la réponse.");
      const source: Source = { source_id: res.source_id, name: sourceName.trim(), domain: sourceDomain.trim() || null, universe_id: sourceUniverse.trim() || null, acquisition_mode: "PDF_MANUAL" };
      setSources(prev => [...prev, source].sort((a, b) => a.name.localeCompare(b.name)));
      setSourceId(res.source_id); setSourceMode("existing"); setConfirmed(false);
    } catch (e) { setError(e instanceof Error ? e.message : "Erreur de création de source."); }
    finally { setBusy(null); }
  }

  async function map() {
    if (!inspection || !confirmed || !sourceId || !documentTitle.trim()) { setError("Valide le document et sa source avant la cartographie."); return; }
    setBusy("map"); setError("");
    try { setMapping(await upload("map") as Mapping); }
    catch (e) { setError(e instanceof Error ? e.message : "Erreur de cartographie."); }
    finally { setBusy(null); }
  }

  async function extractAll() {
    if (!file || !mapping || nextPage === null || extracting) return;
    stopRef.current = false;
    setExtracting(true);
    setError("");
    let page: number | null = nextPage;
    try {
      while (page !== null && !stopRef.current) {
        const form = new FormData();
        form.append("file", file);
        form.append("start_page", String(page));
        const batch = await api.postForm("/discovery/pdf-studio/extract", form) as ExtractBatch;
        setUnits(prev => [...prev, ...batch.units]);
        setRejected(prev => prev + batch.rejected_unverified);
        page = batch.next_page;
        setNextPage(page);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur pendant l'extraction.");
    } finally {
      setExtracting(false);
    }
  }

  function exportUnits() {
    const payload = {
      document_hash: inspection?.document_hash,
      document_title: documentTitle,
      source_id: sourceId,
      next_page: nextPage,
      rejected_unverified: rejected,
      counts,
      units,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `pdf-extract-${inspection?.document_hash.slice(0, 12) || "document"}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div><h1 className="text-2xl font-semibold">PDF Studio</h1><p className="mt-1 text-sm text-gray-500">Inspection, identification de l'éditeur et cartographie. Aucun article n'est créé à ce stade.</p></div>
      <section className="rounded-xl border p-5 space-y-4">
        <h2 className="font-semibold">1. Importer un document</h2>
        <input type="file" accept=".pdf,application/pdf" disabled={busy !== null} onChange={e => changeFile(e.target.files?.[0] || null)} className="block w-full text-sm" />
        {file && <p className="text-sm text-gray-500">{file.name} · {(file.size / 1048576).toFixed(2)} Mo</p>}
        <button type="button" onClick={() => void inspect()} disabled={!file || busy !== null} className="rounded bg-ratecard-blue px-4 py-2 text-white disabled:opacity-40">{busy === "inspect" ? "Inspection…" : "Inspecter le PDF"}</button>
      </section>
      {inspection && <>
        <section className="rounded-xl border p-5 space-y-4">
          <h2 className="font-semibold">2. Document et source</h2>
          <p className="text-sm text-gray-500">{inspection.page_count} pages · {inspection.low_text_pages.length} pages avec peu de texte · {inspection.visual_review_pages.length} pages à revoir visuellement</p>
          <div className="grid gap-4 md:grid-cols-3">
            <label className="block text-sm md:col-span-2">Titre du document<input value={documentTitle} onChange={e => { setDocumentTitle(e.target.value); setConfirmed(false); }} className="mt-1 w-full rounded border p-2" /></label>
            <label className="block text-sm">Année (facultative)<input value={documentYear} onChange={e => { setDocumentYear(e.target.value); setConfirmed(false); }} placeholder="2026" className="mt-1 w-full rounded border p-2" /></label>
          </div>
          <div className="flex gap-4 text-sm"><label><input type="radio" checked={sourceMode === "existing"} onChange={() => { setSourceMode("existing"); setConfirmed(false); }} /> Source existante</label><label><input type="radio" checked={sourceMode === "new"} onChange={() => { setSourceMode("new"); setConfirmed(false); }} /> Nouvelle source</label></div>
          {sourceMode === "existing" ? <label className="block text-sm">Éditeur<select value={sourceId} disabled={sourcesLoading} onChange={e => { setSourceId(e.target.value); setConfirmed(false); }} className="mt-1 w-full rounded border p-2"><option value="">{sourcesLoading ? "Chargement…" : "Sélectionner une source"}</option>{sources.map(s => <option key={s.source_id} value={s.source_id}>{s.name}</option>)}</select></label> : <div className="space-y-3">
            <label className="block text-sm">Nom de l'éditeur<input value={sourceName} onChange={e => setSourceName(e.target.value)} className="mt-1 w-full rounded border p-2" /></label>
            {duplicate && <p className="text-sm text-amber-700">Cette source existe déjà : {duplicate.name}. Utilise la source existante.</p>}
            <div className="grid gap-3 md:grid-cols-2"><label className="block text-sm">Domaine (facultatif)<input value={sourceDomain} onChange={e => setSourceDomain(e.target.value)} placeholder="example.org" className="mt-1 w-full rounded border p-2" /></label><label className="block text-sm">ID univers (facultatif)<input value={sourceUniverse} onChange={e => setSourceUniverse(e.target.value)} className="mt-1 w-full rounded border p-2" /></label></div>
            <button type="button" disabled={busy !== null || !sourceName.trim() || Boolean(duplicate)} onClick={() => void createSource()} className="rounded border px-4 py-2 text-sm disabled:opacity-40">{busy === "create" ? "Création…" : "Créer la source"}</button>
          </div>}
          {sourceMode === "existing" && selectedSource && <p className="text-sm text-gray-600">Source sélectionnée : <strong>{selectedSource.name}</strong> · {selectedSource.source_id}</p>}
          <p className="break-all text-xs text-gray-500">Empreinte SHA-256 : {inspection.document_hash}. Détection des doublons de PDF non encore persistée.</p>
          <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={confirmed} disabled={!sourceId || !documentTitle.trim() || sourceMode !== "existing"} onChange={e => setConfirmed(e.target.checked)} /> Je confirme le titre du document et son éditeur.</label>
          <button type="button" disabled={!confirmed || !sourceId || busy !== null} onClick={() => void map()} className="rounded bg-ratecard-blue px-4 py-2 text-white disabled:opacity-40">{busy === "map" ? "Cartographie…" : "3. Cartographier"}</button>
          <button type="button" className="ml-3 text-sm underline" onClick={() => setShowPages(!showPages)}>{showPages ? "Masquer" : "Afficher"} le détail des pages</button>
          {showPages && <div className="max-h-80 overflow-y-auto divide-y rounded border">{inspection.pages.map(p => <div key={p.page} className="p-3 text-sm">Page {p.page} · {p.char_count} caractères {p.needs_visual_review ? "· revue visuelle conseillée" : ""}<p className="text-gray-500">{p.preview}</p></div>)}</div>}
        </section>
      </>}
      {mapping && <section className="rounded-xl border p-5 space-y-4">
        <h2 className="text-lg font-semibold">4. Extraire les unités d'information</h2>
        <p className="text-sm text-gray-600">Extraction par lots de 5 pages, sans quota d'articles. Toutes les unités sont conservées, avec leur statut de vérification. Les tableaux, chiffres et interprétations nécessitent une revue humaine.</p>
        <div className="flex flex-wrap items-center gap-3">
          <button type="button" onClick={() => void extractAll()} disabled={extracting || nextPage === null || busy !== null} className="rounded bg-ratecard-blue px-4 py-2 text-white disabled:opacity-40">{extracting ? "Extraction en cours…" : nextPage === null ? "Extraction terminée" : units.length ? "Reprendre l'extraction" : "Démarrer l'extraction"}</button>
          {extracting && <button type="button" onClick={() => { stopRef.current = true; }} className="rounded border px-4 py-2 text-sm">Arrêter après ce lot</button>}
          <button type="button" onClick={exportUnits} disabled={!units.length} className="rounded border px-4 py-2 text-sm disabled:opacity-40">Exporter toutes les unités JSON</button>
        </div>
        <p className="text-sm">{units.length} candidates · {counts.VERIFIED} citations exactes · {counts.NEEDS_REVIEW} à vérifier · {counts.REJECTED} rejetées · {nextPage === null ? `${mapping.document.page_count}/${mapping.document.page_count}` : `${nextPage - 1}/${mapping.document.page_count}`} pages traitées</p>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <label htmlFor="pdf-unit-status">Afficher :</label>
          <select id="pdf-unit-status" value={filterStatus} onChange={e => setFilterStatus(e.target.value as typeof filterStatus)} className="rounded border px-2 py-1">
            <option value="ALL">Toutes ({units.length})</option>
            <option value="VERIFIED">Citation exacte ({counts.VERIFIED})</option>
            <option value="NEEDS_REVIEW">À vérifier ({counts.NEEDS_REVIEW})</option>
            <option value="REJECTED">Rejetées ({counts.REJECTED})</option>
          </select>
        </div>
        <div className="max-h-[500px] space-y-2 overflow-y-auto">
          {visibleUnits.map((u, i) => <details key={`${u.page}-${u.candidate_index}-${i}`} className="rounded border p-3 text-sm"><summary className="cursor-pointer"><span className="text-gray-500">p. {u.page ?? "?"} · {u.kind} · {u.status} · </span>{u.fact || "Unité invalide"}</summary><blockquote className="mt-2 border-l-2 pl-3 text-gray-600">{u.quote || "Citation absente"}</blockquote><p className="mt-2 text-xs text-gray-500">Contrôle : {u.reason} · score {u.match_score}</p></details>)}
        </div>
        <p className="text-xs text-amber-700">Résultats en mémoire navigateur uniquement. Exporter le JSON avant de quitter la page : aucune persistance serveur ni reprise après rechargement n'est encore implémentée.</p>
      </section>}
      {error && <p role="alert" className="rounded border border-red-200 p-3 text-sm text-red-700">{error}</p>}
      {mapping && <section className="rounded-xl border p-5 space-y-4"><h2 className="text-lg font-semibold">Cartographie — {documentTitle}</h2><p className="text-sm text-gray-500">Éditeur : {selectedSource?.name} · {mapping.document.page_count} pages · {topics.length} thèmes · {mapping.sections.length} titres candidats</p><p className="text-sm">{mapping.note}</p><div className="space-y-2">{topics.map(([key, topic]) => <div key={key} className="rounded border"><button type="button" className="flex w-full justify-between p-3 text-left text-sm" onClick={() => setExpandedTopic(expandedTopic === key ? null : key)}><span>{TOPIC_NAMES[key] || key}</span><span>{topic.page_count} pages</span></button>{expandedTopic === key && <p className="border-t p-3 text-sm text-gray-600">Pages : {topic.pages.map(p => p.page).join(", ")}</p>}</div>)}</div><details className="rounded border p-3"><summary className="cursor-pointer text-sm">Titres candidats</summary><div className="mt-3 max-h-80 overflow-auto text-sm">{mapping.sections.map((s, i) => <p key={i}>p. {s.page} — {s.heading_candidate}</p>)}</div></details><p className="text-sm text-gray-500">La cartographie est heuristique. Le PDF et ses métadonnées ne sont pas encore enregistrés en base ; aucun contenu n'a été généré.</p></section>}
    </div>
  );
}
