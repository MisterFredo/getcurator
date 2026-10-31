"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

type Source = { source_id: string; name: string };
type Page = { page: number; text: string };
type Candidate = {
  id: string; title: string; kind: string; parent?: string | null;
  start_page: number; end_page: number; pages: Page[];
  visual_review_pages?: number[]; review_status: "NEEDS_REVIEW" | "APPROVED";
};
type Segmentation = {
  version: string;
  document: { document_hash: string; filename: string; page_count: number; title?: string | null };
  summary: { candidates: number; excluded_pages: number[]; candidate_pages: number };
  candidates: Candidate[]; warnings: string[];
};
type Draft = {
  version: string; status: "DRAFT_REVIEW_REQUIRED" | "GENERATION_REJECTED" | "APPROVED";
  proposal_id: string; document_hash: string; document_title: string; source_id: string;
  title: string; excerpt: string; body: string; key_points: string[];
  cited_pages: number[]; source_pages: Page[];
  warnings: string[]; refusal_reason?: string | null; model: string;
};
type RegisterResponse = { id_document?: string; document_id?: string; status?: string };
type ImportResponse = {
  status: string; count: number;
  articles: { proposal_id: string; id_raw: string; already_exists: boolean }[];
};

const button = "rounded-md border px-3 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-40";
const primary = `${button} bg-ratecard-blue text-white`;
const field = "mt-1 w-full rounded-md border p-2 text-sm";
const normalize = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();
const message = (error: unknown) => error instanceof Error ? error.message : String(error);
const citedPages = (value: string): number[] => {
  const pages: number[] = [];
  const regex = /\[p\.\s*(\d+)\]/gi;
  let match: RegExpExecArray | null;
  while ((match = regex.exec(value)) !== null) pages.push(Number(match[1]));
  return pages;
};

function downloadJson(filename: string, data: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function PDFStudio() {
  const [file, setFile] = useState<File | null>(null);
  const [segmentation, setSegmentation] = useState<Segmentation | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [documentTitle, setDocumentTitle] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [sourceId, setSourceId] = useState("");
  const [sourceMode, setSourceMode] = useState<"existing" | "new">("existing");
  const [sourceName, setSourceName] = useState("");
  const [sourceDomain, setSourceDomain] = useState("");
  const [sourceUniverse, setSourceUniverse] = useState("");
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [approvedDraftIds, setApprovedDraftIds] = useState<string[]>([]);
  const [documentId, setDocumentId] = useState("");
  const [importResult, setImportResult] = useState<ImportResponse | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [filter, setFilter] = useState("");
  const [showSource, setShowSource] = useState(false);

  useEffect(() => {
    let active = true;
    api.get("/source/list")
      .then((result: { sources?: Source[] }) => { if (active) setSources(result.sources || []); })
      .catch((e: unknown) => { if (active) setError(`Chargement des sources : ${message(e)}`); });
    return () => { active = false; };
  }, []);

  const selected = candidates.find(candidate => candidate.id === selectedId) || null;
  const visible = useMemo(() => candidates.filter(candidate => normalize(candidate.title).includes(normalize(filter))), [candidates, filter]);
  const approvedDrafts = approvedDraftIds.map(id => drafts[id]).filter((draft): draft is Draft => Boolean(draft));
  const duplicate = sources.find(source => normalize(source.name) === normalize(sourceName));
  const locked = Boolean(documentId) || Boolean(importResult);

  function reset(next: File | null) {
    setFile(next); setSegmentation(null); setCandidates([]); setSelectedId(null);
    setDrafts({}); setApprovedDraftIds([]); setDocumentId(""); setImportResult(null);
    setDocumentTitle(""); setError(""); setNotice(""); setFilter("");
  }

  async function segment() {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf") || file.size > 30 * 1024 * 1024) {
      setError("Fichier PDF requis (30 Mo maximum)."); return;
    }
    setBusy("segment"); setError(""); setNotice("");
    try {
      const form = new FormData(); form.append("file", file);
      const result = await api.postForm("/discovery/pdf-studio/segment", form) as Segmentation;
      if (result.version !== "7.0" || !Array.isArray(result.candidates)) throw new Error("Réponse de segmentation V7 invalide.");
      setSegmentation(result);
      setCandidates(result.candidates);
      setSelectedId(result.candidates[0]?.id || null);
      setDocumentTitle(result.document.title?.trim() || file.name.replace(/\.pdf$/i, "").replace(/[_-]+/g, " "));
      setDrafts({}); setApprovedDraftIds([]); setDocumentId(""); setImportResult(null);
      setNotice(`${result.candidates.length} candidats détectés. Vérifie les unités éditoriales avant génération.`);
    } catch (e) { setError(message(e)); }
    finally { setBusy(""); }
  }

  async function createSource() {
    if (!sourceName.trim() || duplicate) { setError("Source vide ou déjà existante."); return; }
    setBusy("source"); setError("");
    try {
      const result = await api.post("/source/create", {
        name: sourceName.trim(), type_source: "PUBLISHER",
        domain: sourceDomain.trim() || null,
        universe_id: sourceUniverse.trim() || null,
        acquisition_mode: "PDF_MANUAL",
      }) as { source_id: string };
      if (!result.source_id) throw new Error("Identifiant de source absent.");
      setSources(previous => [...previous, { source_id: result.source_id, name: sourceName.trim() }].sort((a, b) => a.name.localeCompare(b.name)));
      setSourceId(result.source_id); setSourceMode("existing");
    } catch (e) { setError(message(e)); }
    finally { setBusy(""); }
  }

  function invalidate(id: string) {
    setDrafts(previous => { const next = { ...previous }; delete next[id]; return next; });
    setApprovedDraftIds(previous => previous.filter(item => item !== id));
    setImportResult(null);
  }

  function updateCandidate(id: string, patch: Partial<Candidate>) {
    if (locked) return;
    setCandidates(previous => previous.map(candidate => candidate.id === id ? { ...candidate, ...patch, review_status: patch.review_status ?? "NEEDS_REVIEW" } : candidate));
    invalidate(id);
  }

  function splitCandidate() {
    if (!selected || locked) return;
    const input = window.prompt(`Scinder « ${selected.title} » avant quelle page ?`, String(selected.start_page + 1));
    if (input === null) return;
    const boundary = Number(input);
    const left = selected.pages.filter(page => page.page < boundary);
    const right = selected.pages.filter(page => page.page >= boundary);
    if (!Number.isInteger(boundary) || !left.length || !right.length) { setError("Page de coupure invalide."); return; }
    const first = { ...selected, id: `${selected.id}-A`, title: `${selected.title} — partie 1`, pages: left, end_page: left[left.length - 1].page, review_status: "NEEDS_REVIEW" as const };
    const second = { ...selected, id: `${selected.id}-B`, title: `${selected.title} — partie 2`, pages: right, start_page: right[0].page, review_status: "NEEDS_REVIEW" as const };
    if (candidates.some(candidate => candidate.id === first.id || candidate.id === second.id)) { setError("Identifiant de découpage déjà utilisé."); return; }
    setCandidates(previous => previous.flatMap(candidate => candidate.id === selected.id ? [first, second] : [candidate]));
    invalidate(selected.id); setSelectedId(first.id); setError("");
  }

  function removeCandidate() {
    if (!selected || locked || !window.confirm(`Écarter « ${selected.title} » ?`)) return;
    setCandidates(previous => previous.filter(candidate => candidate.id !== selected.id));
    invalidate(selected.id);
    setSelectedId(candidates.find(candidate => candidate.id !== selected.id)?.id || null);
  }

  async function generate() {
    if (!selected || !segmentation || !sourceId || !documentTitle.trim()) { setError("Titre du document et source obligatoires."); return; }
    if (selected.review_status !== "APPROVED") { setError("Approuve d'abord le candidat."); return; }
    setBusy("generate"); setError(""); setNotice("");
    try {
      const draft = await api.post("/discovery/pdf-studio/generate", {
        document_hash: segmentation.document.document_hash,
        document_title: documentTitle.trim(), source_id: sourceId, candidate: selected,
      }) as Draft;
      if (draft.version !== "7.0" || draft.proposal_id !== selected.id) throw new Error("Réponse du générateur incompatible.");
      setDrafts(previous => ({ ...previous, [selected.id]: draft }));
      setApprovedDraftIds(previous => previous.filter(id => id !== selected.id));
      setNotice(draft.status === "GENERATION_REJECTED" ? draft.refusal_reason || "Génération rejetée." : "Fiche générée : vérifie les faits et les citations avant validation.");
    } catch (e) { setError(message(e)); }
    finally { setBusy(""); }
  }

  function editDraft(id: string, patch: Partial<Draft>) {
    if (locked) return;
    setDrafts(previous => ({ ...previous, [id]: { ...previous[id], ...patch } }));
    setApprovedDraftIds(previous => previous.filter(item => item !== id));
  }

  function validateDraft(id: string, checked: boolean) {
    const draft = drafts[id];
    if (!draft || draft.status === "GENERATION_REJECTED") return;
    if (checked) {
      const source = new Set(draft.source_pages.map(page => page.page));
      const all = [draft.body, ...draft.key_points].reduce<number[]>((acc, value) => acc.concat(citedPages(value)), []);
      const facts = draft.body.split("\n").map(line => line.trim()).filter(line => /^[-*•]\s/.test(line));
      if (!draft.title.trim() || !draft.excerpt.trim() || !draft.body.trim() || !citedPages(draft.body).length ||
          draft.key_points.some(point => !citedPages(point).length) || !facts.length || facts.some(line => !citedPages(line).length) || all.some(page => !source.has(page))) {
        setError("Titre, description, lignes factuelles et références de pages valides sont obligatoires."); return;
      }
    }
    setApprovedDraftIds(previous => checked ? (previous.includes(id) ? previous : [...previous, id]) : previous.filter(item => item !== id));
    setError("");
  }

  async function importApproved() {
    if (!file || !segmentation || !sourceId || !documentTitle.trim() || !approvedDrafts.length) return;
    setBusy("import"); setError(""); setNotice("");
    try {
      let id = documentId;
      if (!id) {
        const form = new FormData();
        form.append("file", file); form.append("source_id", sourceId); form.append("title", documentTitle.trim());
        const registered = await api.postForm("/discovery/pdf-studio/document/register", form) as RegisterResponse;
        id = registered.id_document || registered.document_id || "";
        if (!id) throw new Error("Document enregistré mais id_document absent de la réponse.");
        setDocumentId(id);
      }
      const articles = approvedDrafts.map(draft => ({ ...draft, status: "APPROVED" as const }));
      const result = await api.post("/discovery/pdf-studio/import-approved", { id_document: id, articles }) as ImportResponse;
      setImportResult(result);
      setNotice(`${result.count} fiche(s) documentaire(s) importée(s) dans RATECARD_CONTENT_RAW.`);
    } catch (e) { setError(message(e)); }
    finally { setBusy(""); }
  }

  const draft = selected ? drafts[selected.id] : undefined;
  const canEdit = !locked && !busy;

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold">PDF Studio <span className="text-sm font-normal text-gray-500">V7.1 — DEV</span></h1>
        <p className="mt-1 text-sm text-gray-600">PDF → unités documentaires → fiches factuelles sourcées → GetCurator RAW.</p>
      </header>

      {error && <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
      {notice && <div className="rounded-lg border p-3 text-sm">{notice}</div>}

      <section className="space-y-4 rounded-xl border p-5">
        <h2 className="font-semibold">1. Importer le PDF</h2>
        <input type="file" accept=".pdf,application/pdf" disabled={Boolean(busy)} onChange={event => reset(event.target.files?.[0] || null)} className="block w-full text-sm" />
        {file && <p className="text-sm text-gray-500">{file.name} · {(file.size / 1048576).toFixed(2)} Mo</p>}
        <button className={primary} type="button" disabled={!file || Boolean(busy)} onClick={() => void segment()}>{busy === "segment" ? "Analyse en cours…" : "Analyser et proposer les unités"}</button>
        {segmentation && <p className="text-sm">{segmentation.document.page_count} pages · {candidates.length} candidats · {segmentation.summary.candidate_pages} pages attribuées</p>}
        {segmentation?.warnings.map((warning, index) => <p key={index} className="text-xs text-amber-700">{warning}</p>)}
      </section>

      {segmentation && <section className="space-y-4 rounded-xl border p-5">
        <h2 className="font-semibold">2. Document et source</h2>
        <label className="block text-sm">Titre du document<input className={field} value={documentTitle} disabled={locked} onChange={event => { setDocumentTitle(event.target.value); setDrafts({}); setApprovedDraftIds([]); }} /></label>
        <div className="flex gap-4 text-sm">
          <label><input type="radio" checked={sourceMode === "existing"} disabled={locked} onChange={() => setSourceMode("existing")} /> Source existante</label>
          <label><input type="radio" checked={sourceMode === "new"} disabled={locked} onChange={() => setSourceMode("new")} /> Nouvelle source</label>
        </div>
        {sourceMode === "existing" ? <label className="block text-sm">Éditeur
          <select className={field} value={sourceId} disabled={locked} onChange={event => { setSourceId(event.target.value); setDrafts({}); setApprovedDraftIds([]); }}>
            <option value="">Sélectionner une source</option>
            {sources.map(source => <option key={source.source_id} value={source.source_id}>{source.name}</option>)}
          </select>
        </label> : <div className="grid gap-3 md:grid-cols-2">
          <label className="text-sm">Nom<input className={field} value={sourceName} onChange={event => setSourceName(event.target.value)} /></label>
          <label className="text-sm">Domaine<input className={field} value={sourceDomain} onChange={event => setSourceDomain(event.target.value)} /></label>
          <label className="text-sm">ID univers (facultatif)<input className={field} value={sourceUniverse} onChange={event => setSourceUniverse(event.target.value)} /></label>
          <div className="flex items-end"><button className={button} type="button" disabled={Boolean(busy) || !sourceName.trim() || Boolean(duplicate)} onClick={() => void createSource()}>Créer la source</button></div>
          {duplicate && <p className="text-sm text-amber-700">Source existante : {duplicate.name}</p>}
        </div>}
      </section>}

      {segmentation && <section className="space-y-4 rounded-xl border p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><h2 className="font-semibold">3. Candidats et extractions factuelles</h2><p className="text-sm text-gray-500">{candidates.length} candidats · {Object.keys(drafts).length} brouillons · {approvedDraftIds.length} fiches validées</p></div>
          <button className={button} type="button" onClick={() => downloadJson(`pdf-studio-v72-${segmentation.document.document_hash.slice(0, 12)}.json`, { version: "7.0", document: segmentation.document, document_title: documentTitle, source_id: sourceId, candidates, drafts, approved_draft_ids: approvedDraftIds })}>Exporter le travail JSON</button>
        </div>
        <div className="grid gap-4 lg:grid-cols-[minmax(240px,1fr)_minmax(0,2fr)]">
          <aside className="space-y-2">
            <input className={field} placeholder="Filtrer les candidats…" value={filter} onChange={event => setFilter(event.target.value)} />
            <div className="max-h-[700px] space-y-1 overflow-y-auto">
              {visible.map(candidate => <button key={candidate.id} type="button" className={`w-full rounded-md border p-3 text-left text-sm ${candidate.id === selectedId ? "border-blue-500 bg-blue-50" : "hover:bg-gray-50"}`} onClick={() => { setSelectedId(candidate.id); setShowSource(false); }}>
                <span className="block font-medium">{candidate.title}</span>
                <span className="text-xs text-gray-500">p. {candidate.start_page}–{candidate.end_page} · {approvedDraftIds.includes(candidate.id) ? "Fiche validée" : drafts[candidate.id] ? "Brouillon" : candidate.review_status === "APPROVED" ? "Prêt à générer" : "À revoir"}</span>
              </button>)}
            </div>
          </aside>
          <div className="min-w-0 space-y-4">
            {!selected ? <p className="text-sm text-gray-500">Sélectionne un candidat.</p> : <>
              <div className="space-y-3 rounded-lg border p-4">
                <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold">Candidat {selected.id}</h3><span className="text-xs text-gray-500">{selected.kind} · p. {selected.start_page}–{selected.end_page}</span></div>
                <label className="block text-sm">Titre de l'unité<input className={field} value={selected.title} disabled={!canEdit} onChange={event => updateCandidate(selected.id, { title: event.target.value })} /></label>
                {selected.parent && <p className="text-xs text-gray-500">Section parente : {selected.parent}</p>}
                {!!selected.visual_review_pages?.length && <p className="text-xs text-amber-700">Pages avec peu de texte : {selected.visual_review_pages.join(", ")}. Vérifier les tableaux et graphiques dans le PDF.</p>}
                <div className="flex flex-wrap gap-2">
                  <button className={button} type="button" disabled={!canEdit || selected.pages.length < 2} onClick={splitCandidate}>Scinder par page</button>
                  <button className={button} type="button" disabled={!canEdit} onClick={removeCandidate}>Écarter</button>
                  <button className={button} type="button" onClick={() => setShowSource(value => !value)}>{showSource ? "Masquer" : "Afficher"} les pages sources</button>
                </div>
                {showSource && <div className="max-h-[550px] space-y-3 overflow-y-auto">{selected.pages.map(page => <label key={page.page} className="block text-sm">Page {page.page}<textarea className={`${field} font-mono text-xs`} rows={8} disabled={!canEdit} value={page.text} onChange={event => updateCandidate(selected.id, { pages: selected.pages.map(item => item.page === page.page ? { ...item, text: event.target.value } : item) })} /></label>)}</div>}
                <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={selected.review_status === "APPROVED"} disabled={!canEdit || !selected.pages.some(page => page.text.trim())} onChange={event => updateCandidate(selected.id, { review_status: event.target.checked ? "APPROVED" : "NEEDS_REVIEW" })} /> J'ai vérifié le périmètre et les pages de ce candidat.</label>
                <button className={primary} type="button" disabled={Boolean(busy) || locked || !sourceId || !documentTitle.trim() || selected.review_status !== "APPROVED"} onClick={() => void generate()}>{busy === "generate" ? "Génération…" : draft ? "Régénérer la fiche" : "Générer la fiche"}</button>
              </div>
              {draft && <div className="space-y-3 rounded-lg border p-4">
                <h3 className="font-semibold">Fiche factuelle — revue documentaire</h3>
                <p className="text-xs text-gray-500">{draft.status} · {draft.model} · pages citées : {draft.cited_pages.join(", ") || "aucune"}</p>
                {draft.refusal_reason && <p className="text-sm text-red-700">{draft.refusal_reason}</p>}
                {draft.warnings.map((warning, index) => <p key={index} className="text-xs text-amber-700">{warning}</p>)}
                {draft.status !== "GENERATION_REJECTED" && <>
                  <label className="block text-sm">Titre<input className={field} disabled={!canEdit} value={draft.title} onChange={event => editDraft(selected.id, { title: event.target.value })} /></label>
                  <label className="block text-sm">Extrait<textarea className={field} rows={3} disabled={!canEdit} value={draft.excerpt} onChange={event => editDraft(selected.id, { excerpt: event.target.value })} /></label>
                  <label className="block text-sm">Repères majeurs (non utilisés en V7.2)<textarea className={field} rows={6} disabled={!canEdit} value={draft.key_points.join("\n")} onChange={event => editDraft(selected.id, { key_points: event.target.value.split("\n").map(point => point.trim()).filter(Boolean) })} /></label>
                  <label className="block text-sm">Extraction exhaustive en bullet points (par rubrique)<textarea className={`${field} font-mono text-xs`} rows={20} disabled={!canEdit} value={draft.body} onChange={event => editDraft(selected.id, { body: event.target.value })} /></label>
                  <label className="flex items-start gap-2 text-sm"><input type="checkbox" disabled={!canEdit} checked={approvedDraftIds.includes(selected.id)} onChange={event => validateDraft(selected.id, event.target.checked)} /> J'ai vérifié les faits, chiffres et références dans le PDF original ; je valide cette fiche.</label>
                </>}
              </div>}
            </>}
          </div>
        </div>
      </section>}

      {segmentation && <section className="space-y-3 rounded-xl border p-5">
        <h2 className="font-semibold">4. Importer dans GetCurator</h2>
        <p className="text-sm">{approvedDrafts.length} fiche(s) approuvée(s) · import dans RATECARD_CONTENT_RAW après enregistrement du PDF original.</p>
        <div className="flex flex-wrap gap-2">
          <button className={button} type="button" disabled={!approvedDrafts.length} onClick={() => downloadJson(`pdf-approved-v72-${segmentation.document.document_hash.slice(0, 12)}.json`, { version: "7.0", document_hash: segmentation.document.document_hash, document_title: documentTitle, source_id: sourceId, articles: approvedDrafts.map(draft => ({ ...draft, status: "APPROVED" })) })}>Exporter les fiches validées</button>
          <button className={primary} type="button" disabled={!approvedDrafts.length || Boolean(busy) || Boolean(importResult)} onClick={() => void importApproved()}>{busy === "import" ? "Import en cours…" : "Enregistrer le PDF et importer les fiches"}</button>
        </div>
        {documentId && <p className="text-xs text-gray-500">Document enregistré : {documentId}</p>}
        {importResult && <div className="space-y-1 text-sm">{importResult.articles.map(item => <p key={item.proposal_id}>{item.proposal_id} → {item.id_raw}{item.already_exists ? " (déjà importé)" : ""}</p>)}</div>}
      </section>}
    </div>
  );
}
