"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";

type DocumentRow = { ID_DOCUMENT: string; TITLE: string; PAGE_COUNT: number | null; UNIT_COUNT: number; TOPIC_COUNT: number };
type TopicRow = {
  ID_DOCUMENT: string; DOCUMENT_TITLE: string; TOPIC_ID: string; TITLE: string;
  ANGLE: string | null; EDITORIAL_RATIONALE: string | null;
  EVIDENCE_COUNT: number; REVIEW_COUNT: number; EDITORIAL_STATUS: string;
  QUALITY_STATUS: string | null; QUALITY_REASON: string | null; QUALITY_VALIDATED_AT: string | null;
};
type UnitRow = {
  ID_DOCUMENT: string; DOCUMENT_TITLE: string; UNIT_ID: string; PDF_PAGE: number;
  FACT: string; QUOTE: string | null; VERIFICATION_STATUS: string;
  KIND: string | null; GEOGRAPHY: string | null; PERIOD: string | null; TOPIC_COUNT: number;
};
type TopicDetail = TopicRow & { evidence: UnitRow[] };
type SearchTopics = { topics: TopicRow[]; total: number };
type SearchUnits = { units: UnitRow[]; total: number };
type Mode = "topics" | "units" | "quality";

const base = "/library";
const field = "rounded-md border border-gray-300 bg-white px-3 py-2 text-sm";
const button = "rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50 disabled:opacity-40";
const errText = (e: unknown) => e instanceof Error ? e.message : String(e);
const PAGE_SIZE = 50;

function qualityLabel(topic: TopicRow) {
  if (!topic.QUALITY_VALIDATED_AT) return "Qualité non validée";
  return topic.QUALITY_STATUS === "REJECTED" ? "Écarté (qualité)" : "Accepté (qualité)";
}

export default function DocumentLibraryPage() {
  const [mode, setMode] = useState<Mode>("topics");
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [documentId, setDocumentId] = useState("");
  const [input, setInput] = useState("");
  const [query, setQuery] = useState("");
  const [quality, setQuality] = useState("");
  const [editorial, setEditorial] = useState("");
  const [offset, setOffset] = useState(0);
  const [topics, setTopics] = useState<TopicRow[]>([]);
  const [units, setUnits] = useState<UnitRow[]>([]);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState<TopicRow | UnitRow | null>(null);
  const [detail, setDetail] = useState<TopicDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");
  const [qualityTopics, setQualityTopics] = useState<TopicRow[]>([]);
  const [qualityEdits, setQualityEdits] = useState<Record<string, { status: "ACCEPTED" | "REJECTED"; reason: string }>>({});
  const [qualityLoading, setQualityLoading] = useState(false);
  const [qualitySaving, setQualitySaving] = useState(false);
  const [qualityMessage, setQualityMessage] = useState("");
  const [qualityError, setQualityError] = useState("");
  const [editorialSaving, setEditorialSaving] = useState(false);
  const [editorialError, setEditorialError] = useState("");

  useEffect(() => {
    let alive = true;
    api.get(`${base}/documents?limit=200&offset=0`)
      .then((r: { documents: DocumentRow[] }) => { if (alive) setDocuments(r.documents || []); })
      .catch((e: unknown) => { if (alive) setError(`Documents : ${errText(e)}`); });
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    if (mode !== "quality" || !documentId) { setQualityTopics([]); setQualityEdits({}); return; }
    let alive = true;
    setQualityLoading(true);
    setQualityError("");
    setQualityMessage("");
    (async () => {
      const all: TopicRow[] = [];
      let total = Infinity;
      while (all.length < total) {
        const params = new URLSearchParams({ document_id: documentId, limit: "100", offset: String(all.length) });
        const result = await api.get(`${base}/search/topics?${params}`) as SearchTopics;
        total = result.total;
        if (!result.topics.length) break;
        all.push(...result.topics);
        if (all.length > 2000) throw new Error("Ce document dépasse la limite de 2 000 sujets pour la validation globale.");
      }
      if (all.length !== total) throw new Error("Chargement incomplet : impossible de valider globalement.");
      if (alive) {
        setQualityTopics(all);
        setQualityEdits(Object.fromEntries(all.map(t => [t.TOPIC_ID, {
          status: t.QUALITY_VALIDATED_AT && t.QUALITY_STATUS === "REJECTED" ? "REJECTED" : "ACCEPTED",
          reason: t.QUALITY_REASON || "",
        }])));
      }
    })().catch((e: unknown) => { if (alive) setQualityError(errText(e)); })
      .finally(() => { if (alive) setQualityLoading(false); });
    return () => { alive = false; };
  }, [mode, documentId]);

  const validateQuality = async () => {
    if (!documentId || !qualityTopics.length || qualitySaving) return;
    if (!window.confirm(`Valider le contrôle qualité des ${qualityTopics.length} sujets de ce document ?`)) return;
    setQualitySaving(true);
    setQualityError(""); setQualityMessage("");
    try {
      const decisions = qualityTopics.map(t => ({
        topic_id: t.TOPIC_ID,
        quality_status: qualityEdits[t.TOPIC_ID]?.status || "ACCEPTED",
        quality_reason: qualityEdits[t.TOPIC_ID]?.status === "REJECTED" ? (qualityEdits[t.TOPIC_ID]?.reason || "").trim() || null : null,
      }));
      await api.post(`${base}/documents/${encodeURIComponent(documentId)}/quality`, { decisions });
      setQualityMessage(`${decisions.length} sujets validés dans BigQuery.`);
      setQualityTopics(previous => previous.map(t => ({ ...t,
        QUALITY_STATUS: qualityEdits[t.TOPIC_ID]?.status || "ACCEPTED",
        QUALITY_REASON: qualityEdits[t.TOPIC_ID]?.status === "REJECTED" ? qualityEdits[t.TOPIC_ID]?.reason || null : null,
        QUALITY_VALIDATED_AT: new Date().toISOString(),
      })));
    } catch (e) { setQualityError(errText(e)); }
    finally { setQualitySaving(false); }
  };

  const search = useCallback(async () => {
    const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
    if (query.trim()) params.set("query", query.trim());
    if (documentId) params.set("document_id", documentId);
    if (mode === "topics") {
      if (quality) params.set("quality_status", quality);
      if (editorial) params.set("editorial_status", editorial);
    }
    return mode === "topics"
      ? await api.get(`${base}/search/topics?${params}`) as SearchTopics
      : await api.get(`${base}/search/units?${params}`) as SearchUnits;
  }, [mode, query, documentId, quality, editorial, offset]);

  useEffect(() => {
    if (mode === "quality") return;
    let alive = true;
    setLoading(true);
    setError("");
    setSelected(null);
    setDetail(null);
    search().then(result => {
      if (!alive) return;
      setTotal(result.total || 0);
      if ("topics" in result) { setTopics(result.topics || []); setUnits([]); }
      else { setUnits(result.units || []); setTopics([]); }
    }).catch((e: unknown) => {
      if (!alive) return;
      setError(`Recherche : ${errText(e)}`);
      setTopics([]); setUnits([]); setTotal(0);
    }).finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [search]);

  useEffect(() => {
    if (!selected || mode !== "topics" || !("TOPIC_ID" in selected)) {
      setDetail(null); return;
    }
    let alive = true;
    setLoadingDetail(true);
    api.get(`${base}/documents/${encodeURIComponent(selected.ID_DOCUMENT)}/topics/${encodeURIComponent(selected.TOPIC_ID)}`)
      .then((r: TopicDetail) => { if (alive) setDetail(r); })
      .catch((e: unknown) => { if (alive) setError(`Preuves : ${errText(e)}`); })
      .finally(() => { if (alive) setLoadingDetail(false); });
    return () => { alive = false; };
  }, [selected, mode]);

  const updateEditorial = async (topic: TopicRow, status: "REVIEW" | "SELECTED" | "IGNORED") => {
    if (editorialSaving) return;
    setEditorialSaving(true);
    setEditorialError("");
    try {
      await api.patch(`${base}/documents/${encodeURIComponent(topic.ID_DOCUMENT)}/topics/${encodeURIComponent(topic.TOPIC_ID)}/editorial`, { editorial_status: status });
      const apply = (t: TopicRow) => t.ID_DOCUMENT === topic.ID_DOCUMENT && t.TOPIC_ID === topic.TOPIC_ID
        ? { ...t, EDITORIAL_STATUS: status } : t;
      setTopics(prev => prev.map(apply));
      setSelected(prev => prev && "TOPIC_ID" in prev ? apply(prev) : prev);
      setDetail(prev =>
        prev
          ? {
              ...prev,
              EDITORIAL_STATUS:
                prev.ID_DOCUMENT === topic.ID_DOCUMENT &&
                prev.TOPIC_ID === topic.TOPIC_ID
                  ? status
                  : prev.EDITORIAL_STATUS,
            }
          : prev
      );
      // If the current filter excludes the new status, remove it from the visible list.
      if (editorial && editorial !== status) {
        setTopics(prev => prev.filter(t => !(t.ID_DOCUMENT === topic.ID_DOCUMENT && t.TOPIC_ID === topic.TOPIC_ID)));
        setSelected(null);
        setDetail(null);
        setTotal(prev => Math.max(0, prev - 1));
      }
    } catch (e) { setEditorialError(errText(e)); }
    finally { setEditorialSaving(false); }
  };

  const topicSelected = selected && "TOPIC_ID" in selected ? selected : null;
  const unitSelected = selected && "UNIT_ID" in selected ? selected : null;
  const entries = mode === "topics" ? topics : units;
  const qualityRejected = qualityTopics.filter(t => qualityEdits[t.TOPIC_ID]?.status === "REJECTED").length;

  return (
    <main className="mx-auto max-w-7xl space-y-5 p-6">
      <header>
        <h1 className="text-2xl font-semibold">Bibliothèque documentaire</h1>
        <p className="mt-1 text-sm text-gray-600">Recherche sur l'ensemble des PDF importés. Consultation uniquement : aucun contenu RAW créé.</p>
      </header>

      <div className="flex gap-2 border-b pb-2">
        <button type="button" className={`${button} ${mode === "topics" ? "border-blue-500 bg-blue-50 font-semibold" : ""}`}
          onClick={() => { setMode("topics"); setOffset(0); }}>Sujets</button>
        <button type="button" className={`${button} ${mode === "units" ? "border-blue-500 bg-blue-50 font-semibold" : ""}`}
          onClick={() => { setMode("units"); setOffset(0); }}>Informations</button>
        <button type="button" className={`${button} ${mode === "quality" ? "border-blue-500 bg-blue-50 font-semibold" : ""}`}
          onClick={() => { setMode("quality"); setOffset(0); }}>Contrôle qualité</button>
      </div>

      {mode === "quality" ? (
        <section className="space-y-4">
          <div className="rounded-lg border bg-gray-50 p-4 space-y-2">
            <h2 className="font-semibold">Reprendre le contrôle qualité d’un document</h2>
            <p className="text-sm text-gray-600">Les sujets sont rechargés depuis BigQuery, sans réextraction. Le motif de rejet est facultatif. La validation est globale et remplace les décisions précédentes.</p>
            <select className={field} aria-label="Document à contrôler" value={documentId} onChange={e => setDocumentId(e.target.value)}>
              <option value="">Choisir un document</option>
              {documents.map(d => <option key={d.ID_DOCUMENT} value={d.ID_DOCUMENT}>{d.TITLE || d.ID_DOCUMENT} ({d.TOPIC_COUNT} sujets)</option>)}
            </select>
            {qualityLoading && <p className="text-sm">Chargement de tous les sujets…</p>}
            {documentId && !qualityLoading && !qualityError && <p className="text-sm">{qualityTopics.length} sujets · {qualityRejected} écartés · {qualityTopics.length - qualityRejected} conservés</p>}
          </div>
          {qualityError && <p role="alert" className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800">{qualityError}</p>}
          {qualityMessage && <p role="status" className="rounded-md border border-green-300 bg-green-50 p-3 text-sm text-green-800">{qualityMessage}</p>}
          <div className="max-h-[650px] space-y-2 overflow-y-auto">
            {qualityTopics.map(t => {
              const edit = qualityEdits[t.TOPIC_ID];
              const rejected = edit?.status === "REJECTED";
              return <article key={t.TOPIC_ID} className={`rounded-lg border p-3 ${rejected ? "border-red-300 bg-red-50" : "bg-white"}`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0 flex-1"><p className="font-semibold text-sm">{t.TITLE}</p><p className="text-xs text-gray-500">{t.EVIDENCE_COUNT} preuves · {t.EDITORIAL_STATUS}{t.QUALITY_VALIDATED_AT ? " · déjà validé" : " · non validé"}</p></div>
                  <select className={field} aria-label={`Qualité : ${t.TITLE}`} value={edit?.status || "ACCEPTED"} onChange={e => {
                    const status = e.target.value as "ACCEPTED" | "REJECTED";
                    setQualityEdits(prev => ({ ...prev, [t.TOPIC_ID]: { status, reason: prev[t.TOPIC_ID]?.reason || "" } }));
                    setQualityMessage("");
                  }}><option value="ACCEPTED">Conserver</option><option value="REJECTED">Écarter</option></select>
                </div>
                {rejected && <input className={`${field} mt-2 w-full`} maxLength={500} placeholder="Motif facultatif" value={edit?.reason || ""} onChange={e => {
                  const reason = e.target.value;
                  setQualityEdits(prev => ({ ...prev, [t.TOPIC_ID]: { status: "REJECTED", reason } }));
                  setQualityMessage("");
                }} />}
              </article>;
            })}
          </div>
          {qualityTopics.length > 0 && <div className="sticky bottom-3 rounded-lg border bg-white p-3 shadow-sm flex flex-wrap items-center justify-between gap-3">
            <span className="text-sm">{qualityRejected} sujet(s) écarté(s) sur {qualityTopics.length}</span>
            <button type="button" className={button} disabled={qualityLoading || qualitySaving || Boolean(qualityError)} onClick={validateQuality}>{qualitySaving ? "Enregistrement…" : "Valider globalement le contrôle qualité"}</button>
          </div>}
        </section>
      ) : <>
      <form className="flex flex-wrap items-center gap-2" onSubmit={e => { e.preventDefault(); setOffset(0); setQuery(input); }}>
        <input className={`${field} min-w-[220px] flex-1`} value={input} onChange={e => setInput(e.target.value)}
          placeholder={mode === "topics" ? "Rechercher titres, angles et justifications" : "Rechercher faits et citations"} />
        <select className={field} aria-label="Filtre document" value={documentId} onChange={e => { setDocumentId(e.target.value); setOffset(0); }}>
          <option value="">Tous les documents</option>
          {documents.map(d => <option key={d.ID_DOCUMENT} value={d.ID_DOCUMENT}>{d.TITLE || d.ID_DOCUMENT}</option>)}
        </select>
        {mode === "topics" && <>
          <select className={field} aria-label="Filtre qualité" value={quality} onChange={e => { setQuality(e.target.value); setOffset(0); }}>
            <option value="">Toute qualité</option>
            <option value="PENDING">Non validés</option>
            <option value="ACCEPTED">Acceptés</option>
            <option value="REJECTED">Écartés (qualité)</option>
          </select>
          <select className={field} aria-label="Filtre éditorial" value={editorial} onChange={e => { setEditorial(e.target.value); setOffset(0); }}>
            <option value="">Tout statut éditorial</option>
            <option value="REVIEW">À examiner</option>
            <option value="SELECTED">Sélectionnés</option>
            <option value="IGNORED">Ignorés</option>
          </select>
        </>}
        <button type="submit" className={button}>Rechercher</button>
        <button type="button" className={button} onClick={() => {
          setInput(""); setQuery(""); setDocumentId(""); setQuality(""); setEditorial(""); setOffset(0);
        }}>Réinitialiser</button>
      </form>

      {editorialError && <div role="alert" className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800">{editorialError}</div>}
      {error && <div role="alert" className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
      <p className="text-sm text-gray-600">{loading ? "Recherche en cours…" : `${total.toLocaleString("fr-FR")} résultat(s)`}</p>

      <div className="grid gap-4 lg:grid-cols-[minmax(300px,1fr)_minmax(0,1.4fr)]">
        <section className="space-y-2">
          <div className="max-h-[720px] space-y-2 overflow-y-auto pr-1">
            {!loading && entries.length === 0 && <p className="text-sm text-gray-500">Aucun résultat pour ces critères.</p>}
            {mode === "topics" && topics.map(t => (
              <button key={`${t.ID_DOCUMENT}:${t.TOPIC_ID}`} type="button" onClick={() => setSelected(t)}
                className={`w-full rounded-lg border p-3 text-left text-sm ${t.QUALITY_VALIDATED_AT && t.QUALITY_STATUS === "REJECTED" ? "border-red-300 bg-red-50" : "hover:bg-gray-50"} ${topicSelected?.ID_DOCUMENT === t.ID_DOCUMENT && topicSelected?.TOPIC_ID === t.TOPIC_ID ? "ring-2 ring-blue-400" : ""}`}>
                <span className="block font-semibold">{t.TITLE}</span>
                <span className="mt-1 block text-xs text-gray-600">{t.DOCUMENT_TITLE} · {t.EVIDENCE_COUNT} preuves</span>
                <span className="mt-1 block text-xs text-gray-500">{qualityLabel(t)} · {t.EDITORIAL_STATUS}</span>
              </button>
            ))}
            {mode === "units" && units.map(u => (
              <button key={`${u.ID_DOCUMENT}:${u.UNIT_ID}`} type="button" onClick={() => setSelected(u)}
                className={`w-full rounded-lg border p-3 text-left text-sm hover:bg-gray-50 ${unitSelected?.ID_DOCUMENT === u.ID_DOCUMENT && unitSelected?.UNIT_ID === u.UNIT_ID ? "ring-2 ring-blue-400" : ""}`}>
                <span className="block font-medium">{u.FACT}</span>
                <span className="mt-1 block text-xs text-gray-600">{u.DOCUMENT_TITLE} · p. {u.PDF_PAGE} · {u.TOPIC_COUNT} sujet(s)</span>
              </button>
            ))}
          </div>
          <div className="flex items-center justify-between gap-2 pt-2">
            <button type="button" className={button} disabled={loading || offset === 0} onClick={() => setOffset(v => Math.max(0, v - PAGE_SIZE))}>Précédent</button>
            <span className="text-xs text-gray-500">{total ? `${offset + 1}–${Math.min(offset + entries.length, total)} / ${total}` : "0 résultat"}</span>
            <button type="button" className={button} disabled={loading || offset + PAGE_SIZE >= total} onClick={() => setOffset(v => v + PAGE_SIZE)}>Suivant</button>
          </div>
        </section>

        <section className="min-h-[280px] rounded-lg border p-4">
          {!selected ? <p className="text-sm text-gray-500">Sélectionne un résultat pour afficher ses détails.</p> : topicSelected ? (
            <div className="space-y-4 text-sm">
              <div>
                <h2 className="text-lg font-semibold">{topicSelected.TITLE}</h2>
                <p className="text-xs text-gray-500">{topicSelected.DOCUMENT_TITLE} · {topicSelected.TOPIC_ID}</p>
              </div>
              <p><strong>Qualité :</strong> {qualityLabel(topicSelected)}</p>
              {topicSelected.QUALITY_REASON && <p><strong>Motif :</strong> {topicSelected.QUALITY_REASON}</p>}
              <div className="space-y-2">
                <p><strong>Éditorial :</strong> {topicSelected.EDITORIAL_STATUS}</p>
                <div className="flex flex-wrap gap-2">
                  <button type="button" className={button} disabled={editorialSaving || topicSelected.EDITORIAL_STATUS === "REVIEW"} onClick={() => updateEditorial(topicSelected, "REVIEW")}>À examiner</button>
                  <button type="button" className={`${button} ${topicSelected.EDITORIAL_STATUS === "SELECTED" ? "border-green-500 bg-green-50" : ""}`} disabled={editorialSaving || topicSelected.EDITORIAL_STATUS === "SELECTED" || !topicSelected.QUALITY_VALIDATED_AT || topicSelected.QUALITY_STATUS !== "ACCEPTED"} onClick={() => updateEditorial(topicSelected, "SELECTED")}>Sélectionner</button>
                  <button type="button" className={`${button} ${topicSelected.EDITORIAL_STATUS === "IGNORED" ? "border-gray-500 bg-gray-100" : ""}`} disabled={editorialSaving || topicSelected.EDITORIAL_STATUS === "IGNORED"} onClick={() => updateEditorial(topicSelected, "IGNORED")}>Ignorer</button>
                </div>
                {(!topicSelected.QUALITY_VALIDATED_AT || topicSelected.QUALITY_STATUS !== "ACCEPTED") && <p className="text-xs text-amber-700">La sélection nécessite un contrôle qualité validé et accepté.</p>}
                <p className="text-xs text-gray-500">La sélection n'active pas encore de contenu RAW.</p>
              </div>
              <p><strong>Angle :</strong> {topicSelected.ANGLE || "Non renseigné"}</p>
              <p><strong>Justification :</strong> {topicSelected.EDITORIAL_RATIONALE || "Non renseignée"}</p>
              <h3 className="border-t pt-3 font-semibold">Preuves ({topicSelected.EVIDENCE_COUNT})</h3>
              {loadingDetail ? <p>Chargement des preuves…</p> : !detail ? <p className="text-gray-500">Détails indisponibles.</p> : (
                <div className="max-h-[500px] space-y-3 overflow-y-auto">
                  {detail.evidence.map(u => <article key={u.UNIT_ID} className="rounded-md border p-3">
                    <p className="mb-1 text-xs text-gray-500">Page {u.PDF_PAGE} · {u.UNIT_ID} · {u.VERIFICATION_STATUS}</p>
                    <p className="font-medium">{u.FACT}</p>
                    {u.QUOTE && <p className="mt-2 border-l-2 pl-3 text-gray-600">« {u.QUOTE} »</p>}
                  </article>)}
                </div>
              )}
            </div>
          ) : unitSelected ? (
            <div className="space-y-3 text-sm">
              <h2 className="text-lg font-semibold">Information documentaire</h2>
              <p className="text-xs text-gray-500">{unitSelected.DOCUMENT_TITLE} · page {unitSelected.PDF_PAGE} · {unitSelected.UNIT_ID}</p>
              <p className="font-medium">{unitSelected.FACT}</p>
              {unitSelected.QUOTE && <p className="border-l-2 pl-3 text-gray-600">« {unitSelected.QUOTE} »</p>}
              <p><strong>Vérification :</strong> {unitSelected.VERIFICATION_STATUS}</p>
              <p><strong>Sujets associés :</strong> {unitSelected.TOPIC_COUNT}</p>
              <p className="text-gray-600">{[unitSelected.KIND, unitSelected.GEOGRAPHY, unitSelected.PERIOD].filter(Boolean).join(" · ")}</p>
            </div>
          ) : null}
        </section>
      </div>
      </>}
    </main>
  );
}
