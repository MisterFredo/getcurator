"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

type Source = { source_id: string; name: string; domain?: string | null; universe_id?: string | null };
type Inspection = { document_hash: string; filename: string; page_count: number; title: string | null; pages: { page: number; char_count: number; needs_visual_review: boolean; preview: string }[]; low_text_pages: number[]; visual_review_pages: number[] };
type SourcePage = { page: number; text: string };
type Segment = { source_segment_id?: string; topic?: string; source_blocks?: { page: number; text: string; x0?: number; y0?: number }[]; warnings?: string[]; id: string; title: string; kind?: string; country_primary?: string | null; region?: string | null; start_page: number; end_page: number; pages: SourcePage[]; subtopic_candidates?: { page: number; heading: string; topic: string }[]; review_status: string; generatable?: boolean; note?: string | null };
type Segmentation = { status: string; document: { document_hash: string; page_count: number }; summary: { segments: number; pages_covered: number; uncovered_pages: number[] }; segments: Segment[] };
type EditorialResponse = { status: string; document: { document_hash: string; page_count: number }; summary: { candidates: number; pages_covered_structurally: number }; candidates: Segment[]; warnings: string[] };
type Draft = { status: string; proposal_id: string; title: string; excerpt: string; body: string; cited_pages: number[]; warnings: string[]; refusal_reason?: string | null; model: string };

const btn = "rounded-md border px-3 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-40";
const primary = `${btn} bg-ratecard-blue text-white`;
const field = "mt-1 w-full rounded-md border p-2 text-sm";
const normalize = (s: string) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();

function downloadJson(filename: string, value: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function renumber(segment: Segment): Segment {
  const pages = [...segment.pages].sort((a, b) => a.page - b.page);
  return { ...segment, pages, start_page: pages[0]?.page ?? segment.start_page, end_page: pages[pages.length - 1]?.page ?? segment.end_page };
}

export default function PDFStudio() {
  const [file, setFile] = useState<File | null>(null);
  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [documentTitle, setDocumentTitle] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(true);
  const [sourceMode, setSourceMode] = useState<"existing" | "new">("existing");
  const [sourceId, setSourceId] = useState("");
  const [sourceName, setSourceName] = useState("");
  const [sourceDomain, setSourceDomain] = useState("");
  const [sourceUniverse, setSourceUniverse] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [segmentation, setSegmentation] = useState<Segmentation | null>(null);
  const [editorial, setEditorial] = useState<EditorialResponse | null>(null);
  const [viewMode, setViewMode] = useState<"STRUCTURE" | "EDITORIAL">("STRUCTURE");
  const [countryFilter, setCountryFilter] = useState("Netherlands");
  const [editorialCandidates, setEditorialCandidates] = useState<Segment[]>([]);
  const [structuralCandidates, setStructuralCandidates] = useState<Segment[]>([]);
  const [candidates, setCandidates] = useState<Segment[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [draftApproved, setDraftApproved] = useState<string[]>([]);
  const [busy, setBusy] = useState<"inspect" | "segment" | "editorial" | "create" | null>(null);
  const [generatingId, setGeneratingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [filter, setFilter] = useState<"ALL" | "NEEDS_REVIEW" | "APPROVED">("ALL");
  const [showPages, setShowPages] = useState(false);
  const [splitPage, setSplitPage] = useState("");

  const duplicate = sources.find(s => normalize(s.name) === normalize(sourceName));
  const selectedSource = sources.find(s => s.source_id === sourceId);
  const selected = candidates.find(s => s.id === selectedId) || null;
  const approvedCount = candidates.filter(s => s.review_status === "APPROVED" && s.generatable).length;
  const visible = useMemo(() => candidates.filter(s => filter === "ALL" || s.review_status === filter), [candidates, filter]);

  useEffect(() => {
    let active = true;
    api.get("/source/list")
      .then((res: { sources?: Source[] }) => { if (active) setSources(res.sources || []); })
      .catch((e: unknown) => { if (active) setError(e instanceof Error ? e.message : "Impossible de charger les sources."); })
      .finally(() => { if (active) setSourcesLoading(false); });
    return () => { active = false; };
  }, []);

  function resetFile(next: File | null) {
    setFile(next); setInspection(null); setSegmentation(null); setEditorial(null); setStructuralCandidates([]); setEditorialCandidates([]); setViewMode("STRUCTURE"); setCandidates([]); setSelectedId(null);
    setDrafts({}); setDraftApproved([]); setDocumentTitle(""); setConfirmed(false); setError(""); setNotice("");
  }

  async function upload(action: "inspect" | "segment") {
    if (!file) throw new Error("Sélectionne un PDF.");
    const form = new FormData(); form.append("file", file);
    return api.postForm(`/discovery/pdf-studio/${action}`, form);
  }

  async function inspect() {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf") || file.size > 30 * 1024 * 1024) {
      setError("PDF requis, 30 Mo maximum."); return;
    }
    setBusy("inspect"); setError(""); setNotice("");
    try {
      const result = await upload("inspect") as Inspection;
      setInspection(result);
      setDocumentTitle(result.title?.trim() || file.name.replace(/\.pdf$/i, "").replace(/[_-]+/g, " "));
      setSegmentation(null); setEditorial(null); setStructuralCandidates([]); setEditorialCandidates([]); setViewMode("STRUCTURE"); setCandidates([]); setSelectedId(null); setDrafts({}); setDraftApproved([]);
    } catch (e) { setError(e instanceof Error ? e.message : "Erreur d'inspection."); }
    finally { setBusy(null); }
  }

  async function createSource() {
    if (!sourceName.trim() || duplicate) { setError("Source vide ou déjà existante."); return; }
    setBusy("create"); setError("");
    try {
      const res = await api.post("/source/create", {
        name: sourceName.trim(), type_source: "PUBLISHER", domain: sourceDomain.trim() || null,
        universe_id: sourceUniverse.trim() || null, acquisition_mode: "PDF_MANUAL",
      }) as { source_id: string };
      if (!res.source_id) throw new Error("ID source absent.");
      setSources(prev => [...prev, { source_id: res.source_id, name: sourceName.trim() }].sort((a, b) => a.name.localeCompare(b.name)));
      setSourceId(res.source_id); setSourceMode("existing"); setConfirmed(false);
    } catch (e) { setError(e instanceof Error ? e.message : "Erreur de création de source."); }
    finally { setBusy(null); }
  }

  async function segment() {
    if (!inspection || !confirmed || !sourceId || !documentTitle.trim()) { setError("Confirme le document et sa source."); return; }
    setBusy("segment"); setError(""); setNotice("");
    try {
      const result = await upload("segment") as Segmentation;
      if (!Array.isArray(result.segments) || result.document.document_hash !== inspection.document_hash) {
        throw new Error("Segmentation invalide ou PDF différent.");
      }
      const normalized = result.segments.map((s, index) => ({
        ...s, id: s.id || `S${index + 1}`, review_status: "NEEDS_REVIEW", generatable: false,
        pages: Array.isArray(s.pages) ? s.pages.map(p => ({ page: Number(p.page), text: String(p.text || "") })) : [],
      }));
      setSegmentation(result); setStructuralCandidates(normalized); setEditorial(null); setEditorialCandidates([]); setViewMode("STRUCTURE"); setCandidates(normalized); setSelectedId(normalized[0]?.id || null);
      setDrafts({}); setDraftApproved([]);
      setNotice("Segmentation terminée. Chaque candidat doit être revu avant génération.");
    } catch (e) { setError(e instanceof Error ? e.message : "Erreur de segmentation."); }
    finally { setBusy(null); }
  }

  async function identifyEditorial() {
    if (!file || !inspection || !segmentation || !confirmed || !sourceId) {
      setError("Inspecte et segmente le document, puis confirme la source."); return;
    }
    setBusy("editorial"); setError(""); setNotice("");
    try {
      const form = new FormData();
      form.append("file", file);
      if (countryFilter.trim()) form.append("country", countryFilter.trim());
      const result = await api.postForm("/discovery/pdf-studio/editorial-candidates", form) as EditorialResponse;
      if (!Array.isArray(result.candidates) || result.document.document_hash !== inspection.document_hash) {
        throw new Error("Réponse éditoriale invalide ou document différent.");
      }
      const normalized = result.candidates.map((s, index) => ({
        ...s, id: s.id || `E${index + 1}`, review_status: "NEEDS_REVIEW", generatable: false,
        pages: s.pages.map(p => ({ page: Number(p.page), text: String(p.text || "") })),
      }));
      setEditorial(result);
      setEditorialCandidates(normalized);
      setViewMode("EDITORIAL"); setCandidates(normalized);
      setSelectedId(normalized[0]?.id || null);
      setDrafts({}); setDraftApproved([]);
      setNotice(`${normalized.length} sujets éditoriaux détectés. Vérifie l'ordre des paragraphes avant d'approuver.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de reconstruction éditoriale.");
    } finally { setBusy(null); }
  }

  function switchMode(mode: "STRUCTURE" | "EDITORIAL") {
    if (mode === viewMode) return;
    if (candidates.some(s => s.review_status === "APPROVED") || Object.keys(drafts).length) {
      if (!window.confirm("Changer de vue efface les approbations et brouillons de la vue active. Exporte ton travail JSON avant de continuer. Continuer ?")) return;
    }
    if (viewMode === "STRUCTURE") setStructuralCandidates(candidates);
    else setEditorialCandidates(candidates);
    const next = mode === "STRUCTURE" ? structuralCandidates : editorialCandidates;
    setCandidates(next.map(s => ({ ...s, review_status: "NEEDS_REVIEW", generatable: false })));
    setSelectedId(next[0]?.id || null);
    setDrafts({}); setDraftApproved([]); setViewMode(mode); setError("");
  }

  function changeCandidate(id: string, patch: Partial<Segment>) {
    setCandidates(prev => prev.map(s => s.id === id ? { ...s, ...patch, review_status: "NEEDS_REVIEW", generatable: false } : s));
    setDrafts(prev => { const next = { ...prev }; delete next[id]; return next; });
    setDraftApproved(prev => prev.filter(x => x !== id));
  }

  function editPage(id: string, page: number, text: string) {
    const s = candidates.find(x => x.id === id);
    if (!s) return;
    changeCandidate(id, { pages: s.pages.map(p => p.page === page ? { ...p, text } : p) });
  }

  function approveCandidate(id: string) {
    const s = candidates.find(x => x.id === id);
    if (!s || !s.title.trim() || !s.pages.some(p => p.text.trim())) {
      setError("Un titre et au moins un passage source sont nécessaires."); return;
    }
    setCandidates(prev => prev.map(x => x.id === id ? { ...x, review_status: "APPROVED", generatable: true } : x));
    setError("");
  }

  function splitCandidate() {
    if (!selected) return;
    const boundary = Number(splitPage);
    if (!Number.isInteger(boundary)) { setError("Indique un numéro de page valide."); return; }
    const left = selected.pages.filter(p => p.page < boundary);
    const right = selected.pages.filter(p => p.page >= boundary);
    if (!left.length || !right.length) { setError("La coupure doit séparer deux groupes de pages non vides."); return; }
    const suffix = Date.now().toString(36);
    const a = renumber({ ...selected, id: `${selected.id}-A-${suffix}`, title: `${selected.title} — partie 1`, pages: left, review_status: "NEEDS_REVIEW", generatable: false });
    const b = renumber({ ...selected, id: `${selected.id}-B-${suffix}`, title: `${selected.title} — partie 2`, pages: right, review_status: "NEEDS_REVIEW", generatable: false });
    setCandidates(prev => prev.flatMap(s => s.id === selected.id ? [a, b] : [s]));
    setSelectedId(a.id); setSplitPage(""); setNotice("Segment scindé. Vérifie et approuve les deux nouveaux candidats."); setError("");
  }

  function removeCandidate(id: string) {
    if (!window.confirm("Écarter ce candidat du parcours de génération ?")) return;
    setCandidates(prev => prev.filter(s => s.id !== id));
    setSelectedId(prev => prev === id ? candidates.find(s => s.id !== id)?.id || null : prev);
    setNotice("Candidat écarté. Les pages du PDF original restent inchangées.");
  }

  async function generate(id: string) {
    const candidate = candidates.find(s => s.id === id);
    if (!candidate || !inspection || !sourceId || generatingId) return;
    if (candidate.review_status !== "APPROVED" || !candidate.generatable) { setError("Approuve le candidat avant génération."); return; }
    setGeneratingId(id); setError(""); setNotice("");
    try {
      const result = await api.post("/discovery/pdf-studio/generate", {
        document_hash: inspection.document_hash, document_title: documentTitle, source_id: sourceId, candidate,
      }) as Draft;
      setDrafts(prev => ({ ...prev, [id]: result }));
      setDraftApproved(prev => prev.filter(x => x !== id));
      if (result.status !== "DRAFT_REVIEW_REQUIRED") setNotice(result.refusal_reason || "La génération a été refusée : vérifie le périmètre du candidat.");
    } catch (e) { setError(e instanceof Error ? e.message : "Erreur de génération."); }
    finally { setGeneratingId(null); }
  }

  function editDraft(id: string, key: "title" | "excerpt" | "body", value: string) {
    setDrafts(prev => ({ ...prev, [id]: { ...prev[id], [key]: value } }));
    setDraftApproved(prev => prev.filter(x => x !== id));
  }

  function exportWorkspace() {
    if (!inspection || !segmentation) return;
    downloadJson(`pdf-studio-v6-${inspection.document_hash.slice(0, 12)}.json`, {
      version: "6.4", mode: viewMode, editorial_summary: editorial?.summary || null, document_hash: inspection.document_hash, document_title: documentTitle,
      source_id: sourceId, segmentation_summary: segmentation.summary, candidates, drafts, draft_approved_ids: draftApproved,
    });
  }

  async function importWorkspace(next: File | null) {
    if (!next || !inspection) return;
    try {
      const data = JSON.parse(await next.text());
      if (data.document_hash !== inspection.document_hash || !Array.isArray(data.candidates)) throw new Error("Export incompatible avec ce PDF.");
      if (data.candidates.some((s: Segment) => !s.id || !Array.isArray(s.pages) || s.pages.some(p => !Number.isInteger(p.page) || typeof p.text !== "string"))) {
        throw new Error("Candidats invalides dans l'export.");
      }
      setCandidates(data.candidates); setSelectedId(data.candidates[0]?.id || null);
      const restoredMode = data.mode === "EDITORIAL" ? "EDITORIAL" : "STRUCTURE";
      setViewMode(restoredMode);
      if (restoredMode === "EDITORIAL") setEditorialCandidates(data.candidates);
      else setStructuralCandidates(data.candidates);
      setDrafts(data.drafts && typeof data.drafts === "object" ? data.drafts : {});
      setDraftApproved(Array.isArray(data.draft_approved_ids) ? data.draft_approved_ids : []);
      setDocumentTitle(data.document_title || documentTitle);
      setSourceId(data.source_id || sourceId);
      setConfirmed(false); setError(""); setNotice("Travail restauré. Reconfirme la source avant toute génération.");
    } catch (e) { setError(e instanceof Error ? e.message : "Import JSON impossible."); }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold">PDF Studio <span className="text-sm font-normal text-gray-500">V6.4 — DEV</span></h1>
        <p className="mt-1 text-sm text-gray-600">Document → segmentation → revue des passages → génération sourcée. Ancienne consolidation désactivée.</p>
      </header>

      {error && <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
      {notice && <div className="rounded-lg border p-3 text-sm text-gray-700">{notice}</div>}

      <section className="space-y-4 rounded-xl border p-5">
        <h2 className="font-semibold">1. Importer et inspecter le document</h2>
        <input type="file" accept=".pdf,application/pdf" onChange={e => resetFile(e.target.files?.[0] || null)} className="block w-full text-sm" />
        {file && <p className="text-sm text-gray-500">{file.name} · {(file.size / 1048576).toFixed(2)} Mo</p>}
        <button type="button" className={primary} disabled={!file || busy !== null} onClick={() => void inspect()}>{busy === "inspect" ? "Inspection…" : "Inspecter le PDF"}</button>
        {inspection && <div className="space-y-2 text-sm">
          <p>{inspection.page_count} pages · {inspection.low_text_pages.length} pages avec peu de texte · {inspection.visual_review_pages.length} à revoir visuellement</p>
          <p className="break-all text-xs text-gray-500">SHA-256 : {inspection.document_hash}</p>
          <button type="button" className="underline" onClick={() => setShowPages(v => !v)}>{showPages ? "Masquer" : "Voir"} le diagnostic des pages</button>
          {showPages && <div className="max-h-60 divide-y overflow-y-auto rounded border">{inspection.pages.map(p => <div key={p.page} className="p-2"><strong>p. {p.page}</strong> · {p.char_count} caractères {p.needs_visual_review ? "· revue visuelle" : ""}<p className="text-gray-500">{p.preview}</p></div>)}</div>}
        </div>}
      </section>

      {inspection && <section className="space-y-4 rounded-xl border p-5">
        <h2 className="font-semibold">2. Document et éditeur</h2>
        <label className="block text-sm">Titre du document<input className={field} value={documentTitle} onChange={e => { setDocumentTitle(e.target.value); setConfirmed(false); }} /></label>
        <div className="flex gap-5 text-sm">
          <label><input type="radio" checked={sourceMode === "existing"} onChange={() => { setSourceMode("existing"); setConfirmed(false); }} /> Source existante</label>
          <label><input type="radio" checked={sourceMode === "new"} onChange={() => { setSourceMode("new"); setConfirmed(false); }} /> Nouvelle source</label>
        </div>
        {sourceMode === "existing" ? <label className="block text-sm">Éditeur
          <select className={field} value={sourceId} disabled={sourcesLoading} onChange={e => { setSourceId(e.target.value); setConfirmed(false); }}>
            <option value="">{sourcesLoading ? "Chargement…" : "Sélectionner une source"}</option>
            {sources.map(s => <option key={s.source_id} value={s.source_id}>{s.name}</option>)}
          </select>
        </label> : <div className="grid gap-3 md:grid-cols-2">
          <label className="text-sm">Nom<input className={field} value={sourceName} onChange={e => setSourceName(e.target.value)} /></label>
          <label className="text-sm">Domaine<input className={field} value={sourceDomain} onChange={e => setSourceDomain(e.target.value)} /></label>
          <label className="text-sm">ID univers (facultatif)<input className={field} value={sourceUniverse} onChange={e => setSourceUniverse(e.target.value)} /></label>
          <div className="flex items-end"><button type="button" className={btn} disabled={busy !== null || !sourceName.trim() || Boolean(duplicate)} onClick={() => void createSource()}>Créer la source</button></div>
          {duplicate && <p className="text-sm text-amber-700">Source déjà existante : {duplicate.name}</p>}
        </div>}
        {selectedSource && <p className="text-xs text-gray-500">Source : {selectedSource.name} · {selectedSource.source_id}</p>}
        <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={confirmed} disabled={!sourceId || !documentTitle.trim() || sourceMode !== "existing"} onChange={e => setConfirmed(e.target.checked)} /> Je confirme le document et l'éditeur.</label>
        <button type="button" className={primary} disabled={!confirmed || busy !== null} onClick={() => void segment()}>{busy === "segment" ? "Segmentation…" : "3. Segmenter le PDF"}</button>
      </section>}

      {segmentation && <section className="space-y-4 rounded-xl border p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><h2 className="font-semibold">3. Structure et candidats éditoriaux</h2><p className="text-sm text-gray-500">{candidates.length} candidats · {approvedCount} approuvés · {segmentation.summary.pages_covered}/{segmentation.document.page_count} pages couvertes initialement</p></div>
          <div className="flex gap-2"><button type="button" className={btn} onClick={exportWorkspace}>Exporter le travail JSON</button><label className={`${btn} cursor-pointer`}>Reprendre un JSON<input className="hidden" type="file" accept=".json" onChange={e => { void importWorkspace(e.target.files?.[0] || null); e.currentTarget.value = ""; }} /></label></div>
        </div>
        <div className="flex flex-wrap items-end gap-3 rounded-lg border p-3">
          <label className="text-sm">Pays à reconstruire (vide = tous les pays)
            <input className={field} value={countryFilter} onChange={e => setCountryFilter(e.target.value)} placeholder="Netherlands" />
          </label>
          <button type="button" className={primary} disabled={busy !== null || !confirmed} onClick={() => void identifyEditorial()}>
            {busy === "editorial" ? "Reconstruction en cours…" : "Identifier les sujets éditoriaux (V6.4)"}
          </button>
          {editorial && <span className="text-sm text-gray-600">{editorial.summary.candidates} sujets · {editorial.summary.pages_covered_structurally} pages couvertes dans le plan</span>}
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className={viewMode === "STRUCTURE" ? primary : btn} onClick={() => switchMode("STRUCTURE")}>Sections documentaires</button>
          <button type="button" className={viewMode === "EDITORIAL" ? primary : btn} disabled={!editorialCandidates.length} onClick={() => switchMode("EDITORIAL")}>Sujets éditoriaux ({editorialCandidates.length})</button>
        </div>
        {viewMode === "EDITORIAL" && editorial?.warnings?.map((warning, i) => <p key={i} className="text-xs text-amber-700">{warning}</p>)}
        {segmentation.summary.uncovered_pages.length > 0 && <p className="text-sm text-amber-700">Pages non couvertes : {segmentation.summary.uncovered_pages.join(", ")}</p>}
        <p className="text-xs text-amber-700">Les candidats restent à vérifier. La V6.4 reconstruit les colonnes de manière heuristique : contrôle les transitions, les tableaux et les données masquées dans le PDF original.</p>
        <div className="grid gap-4 lg:grid-cols-[minmax(250px,1fr)_minmax(0,2fr)]">
          <aside className="space-y-2">
            <label className="block text-xs">Filtre
              <select className={field} value={filter} onChange={e => setFilter(e.target.value as typeof filter)}><option value="ALL">Tous</option><option value="NEEDS_REVIEW">À revoir</option><option value="APPROVED">Approuvés</option></select>
            </label>
            <div className="max-h-[720px] space-y-1 overflow-y-auto">
              {visible.map(s => <button key={s.id} type="button" onClick={() => { setSelectedId(s.id); setSplitPage(""); }} className={`w-full rounded-md border p-3 text-left text-sm ${selectedId === s.id ? "border-blue-500 bg-blue-50" : "hover:bg-gray-50"}`}>
                <span className="block font-medium">{s.title}</span><span className="text-xs text-gray-500">p. {s.start_page}–{s.end_page} · {s.review_status === "APPROVED" ? "Validé" : "À revoir"}</span>
              </button>)}
            </div>
          </aside>
          <div className="min-w-0 space-y-4">
            {!selected ? <p className="text-sm text-gray-500">Sélectionne un candidat.</p> : <>
              <div className="space-y-3 rounded-lg border p-4">
                <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold">Candidat {selected.id}</h3><span className="text-xs text-gray-500">{selected.kind || "section"} · p. {selected.start_page}–{selected.end_page}</span></div>
                <label className="block text-sm">Titre éditorial<input className={field} value={selected.title} onChange={e => changeCandidate(selected.id, { title: e.target.value })} /></label>
                <div className="grid gap-3 md:grid-cols-2">
                  <label className="block text-sm">Pays principal<input className={field} value={selected.country_primary || ""} onChange={e => changeCandidate(selected.id, { country_primary: e.target.value || null })} /></label>
                  <label className="block text-sm">Région<input className={field} value={selected.region || ""} onChange={e => changeCandidate(selected.id, { region: e.target.value || null })} /></label>
                </div>
                {selected.source_segment_id && <p className="text-xs text-gray-500">Section parente : {selected.source_segment_id} · Thème : {selected.topic || "non classé"}</p>}
                {selected.warnings?.map((w, i) => <p key={i} className="text-xs text-amber-700">{w}</p>)}
                {selected.subtopic_candidates?.length ? <details className="rounded border p-3 text-sm"><summary className="cursor-pointer">Rubriques détectées ({selected.subtopic_candidates.length})</summary><div className="mt-2 space-y-1">{selected.subtopic_candidates.map((h, i) => <p key={i}>p. {h.page} — {h.heading} ({h.topic})</p>)}</div></details> : null}
                <p className="text-xs text-gray-500">Les textes ci-dessous constituent la matière exacte envoyée à la génération. Supprime les paragraphes hors sujet et conserve les pages correspondantes. Une modification invalide toute approbation précédente.</p>
                <div className="max-h-[600px] space-y-3 overflow-y-auto pr-1">{selected.pages.map(p => <label key={p.page} className="block text-sm"><span className="font-medium">Page PDF {p.page}</span><textarea className={`${field} font-mono text-xs`} rows={Math.min(16, Math.max(5, Math.ceil(p.text.length / 95)))} value={p.text} onChange={e => editPage(selected.id, p.page, e.target.value)} /></label>)}</div>
                <div className="flex flex-wrap items-end gap-2 border-t pt-3"><label className="text-sm">Scinder avant la page<input className={field} type="number" min={selected.start_page + 1} max={selected.end_page} value={splitPage} onChange={e => setSplitPage(e.target.value)} /></label><button type="button" className={btn} onClick={splitCandidate} disabled={selected.pages.length < 2}>Scinder</button><button type="button" className={btn} onClick={() => removeCandidate(selected.id)}>Écarter</button></div>
                <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={selected.review_status === "APPROVED" && selected.generatable === true} onChange={e => e.target.checked ? approveCandidate(selected.id) : changeCandidate(selected.id, {})} /> J'ai vérifié les passages source et confirmé qu'ils constituent un seul contenu autonome.</label>
                <button type="button" className={primary} disabled={selected.review_status !== "APPROVED" || !selected.generatable || Boolean(generatingId) || !confirmed} onClick={() => void generate(selected.id)}>{generatingId === selected.id ? "Génération en cours…" : drafts[selected.id] ? "Régénérer l'article" : "4. Générer l'article"}</button>
              </div>
              {drafts[selected.id] && <div className="space-y-3 rounded-lg border p-4">
                <h3 className="font-semibold">4. Brouillon généré — revue obligatoire</h3>
                <p className="text-xs text-gray-500">Statut : {drafts[selected.id].status} · Modèle : {drafts[selected.id].model} · Pages citées : {drafts[selected.id].cited_pages?.join(", ") || "aucune"}</p>
                {drafts[selected.id].refusal_reason && <p className="text-sm text-amber-700">{drafts[selected.id].refusal_reason}</p>}
                {(drafts[selected.id].warnings || []).map((w, i) => <p key={i} className="text-sm text-amber-700">{w}</p>)}
                <label className="block text-sm">Titre<input className={field} value={drafts[selected.id].title} onChange={e => editDraft(selected.id, "title", e.target.value)} /></label>
                <label className="block text-sm">Extrait<textarea className={field} rows={3} value={drafts[selected.id].excerpt} onChange={e => editDraft(selected.id, "excerpt", e.target.value)} /></label>
                <label className="block text-sm">Article<textarea className={`${field} font-mono text-xs`} rows={20} value={drafts[selected.id].body} onChange={e => editDraft(selected.id, "body", e.target.value)} /></label>
                <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={draftApproved.includes(selected.id)} disabled={!drafts[selected.id].body.trim() || !drafts[selected.id].title.trim()} onChange={e => setDraftApproved(prev => e.target.checked ? [...prev, selected.id] : prev.filter(id => id !== selected.id))} /> J'ai contrôlé les affirmations et les références dans le PDF original ; je valide ce brouillon.</label>
              </div>}
            </>}
          </div>
        </div>
      </section>}

      {segmentation && <section className="space-y-3 rounded-xl border p-5">
        <h2 className="font-semibold">5. Export et import RAW</h2>
        <p className="text-sm">{draftApproved.length} brouillon(s) validé(s). L'import BigQuery est volontairement désactivé tant que <code>pdf_import.py</code> n'accepte pas la provenance V6.</p>
        <button type="button" className={btn} disabled={!draftApproved.length} onClick={() => downloadJson(`pdf-approved-v6-${inspection?.document_hash.slice(0, 12)}.json`, {
          version: "6.3", document_hash: inspection?.document_hash, document_title: documentTitle, source_id: sourceId,
          articles: draftApproved.map(id => drafts[id]).filter(Boolean),
        })}>Exporter les articles validés JSON</button>
        <button type="button" className={`${primary} ml-2`} disabled>Importer dans RATECARD_CONTENT_RAW — à connecter</button>
      </section>}
    </div>
  );
}
