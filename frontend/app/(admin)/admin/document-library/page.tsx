"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";

type DocumentRow = {
  ID_DOCUMENT: string;
  ID_SOURCE: string;
  TITLE: string;
  PAGE_COUNT: number | null;
  UNIT_COUNT: number;
  TOPIC_COUNT: number;
};
type TopicRow = {
  TOPIC_ID: string;
  TITLE: string;
  ANGLE: string | null;
  EDITORIAL_RATIONALE: string | null;
  EVIDENCE_COUNT: number;
  REVIEW_COUNT: number;
  EDITORIAL_STATUS: string;
  ID_RAW: string | null;
  ID_CONTENT: string | null;
};
type EvidenceRow = {
  UNIT_ID: string;
  PDF_PAGE: number;
  FACT: string;
  QUOTE: string | null;
  VERIFICATION_STATUS: string;
  KIND: string | null;
  GEOGRAPHY: string | null;
  PERIOD: string | null;
};
type TopicDetail = TopicRow & { id_document: string; evidence: EvidenceRow[] };

type DocumentsResponse = { documents: DocumentRow[] };
type TopicsResponse = { topics: TopicRow[] };

const base = "/discovery/pdf-studio/v8/library";
const field = "rounded-md border border-gray-300 bg-white px-3 py-2 text-sm";
const action = "rounded-md border border-gray-300 px-3 py-2 text-sm disabled:opacity-40";
const errorMessage = (e: unknown) => e instanceof Error ? e.message : String(e);

export default function DocumentLibraryPage() {
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [documentId, setDocumentId] = useState("");
  const [topics, setTopics] = useState<TopicRow[]>([]);
  const [topicId, setTopicId] = useState("");
  const [detail, setDetail] = useState<TopicDetail | null>(null);
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [loadingTopics, setLoadingTopics] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");
  const pageSize = 50;

  const loadDocuments = useCallback(async () => {
    setLoadingDocuments(true);
    setError("");
    try {
      const result = await api.get(`${base}/documents?limit=200&offset=0`) as DocumentsResponse;
      setDocuments(result.documents || []);
      setDocumentId(previous => previous && result.documents.some(d => d.ID_DOCUMENT === previous)
        ? previous : (result.documents[0]?.ID_DOCUMENT || ""));
    } catch (e) {
      setError(`Chargement des documents : ${errorMessage(e)}`);
    } finally {
      setLoadingDocuments(false);
    }
  }, []);

  useEffect(() => { void loadDocuments(); }, [loadDocuments]);

  useEffect(() => {
    if (!documentId) { setTopics([]); setTopicId(""); setDetail(null); return; }
    let active = true;
    setLoadingTopics(true);
    setError("");
    setTopicId("");
    setDetail(null);
    const params = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
    if (search.trim()) params.set("query", search.trim());
    if (status) params.set("editorial_status", status);
    api.get(`${base}/documents/${encodeURIComponent(documentId)}/topics?${params.toString()}`)
      .then((result: TopicsResponse) => { if (active) setTopics(result.topics || []); })
      .catch((e: unknown) => { if (active) { setTopics([]); setError(`Chargement des sujets : ${errorMessage(e)}`); } })
      .finally(() => { if (active) setLoadingTopics(false); });
    return () => { active = false; };
  }, [documentId, search, status, offset]);

  useEffect(() => {
    if (!documentId || !topicId) { setDetail(null); return; }
    let active = true;
    setLoadingDetail(true);
    setDetail(null);
    api.get(`${base}/documents/${encodeURIComponent(documentId)}/topics/${encodeURIComponent(topicId)}`)
      .then((result: TopicDetail) => { if (active) setDetail(result); })
      .catch((e: unknown) => { if (active) setError(`Chargement des preuves : ${errorMessage(e)}`); })
      .finally(() => { if (active) setLoadingDetail(false); });
    return () => { active = false; };
  }, [documentId, topicId]);

  const selectedDocument = documents.find(d => d.ID_DOCUMENT === documentId);

  return (
    <main className="mx-auto max-w-7xl space-y-6 p-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Bibliothèque documentaire</h1>
        <p className="text-sm text-gray-600">Documents, sujets et preuves importés depuis PDF Studio V8. Consultation uniquement : aucun article RAW n’est créé.</p>
      </header>

      {error && <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</div>}

      <section className="space-y-3 rounded-xl border p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-semibold">1. Documents</h2>
          <button type="button" className={action} disabled={loadingDocuments} onClick={() => void loadDocuments()}>Actualiser</button>
        </div>
        {loadingDocuments ? <p className="text-sm text-gray-500">Chargement…</p> : documents.length === 0 ? (
          <p className="text-sm text-gray-500">Aucun document importé.</p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {documents.map(document => (
              <button key={document.ID_DOCUMENT} type="button" onClick={() => { setDocumentId(document.ID_DOCUMENT); setOffset(0); }}
                className={`rounded-lg border p-4 text-left ${documentId === document.ID_DOCUMENT ? "border-blue-500 bg-blue-50" : "hover:bg-gray-50"}`}>
                <span className="block font-medium">{document.TITLE || document.ID_DOCUMENT}</span>
                <span className="mt-2 block text-xs text-gray-600">{document.TOPIC_COUNT} sujets · {document.UNIT_COUNT} informations · {document.PAGE_COUNT ?? "?"} pages</span>
              </button>
            ))}
          </div>
        )}
      </section>

      {selectedDocument && <section className="space-y-4 rounded-xl border p-5">
        <h2 className="font-semibold">2. Sujets — {selectedDocument.TITLE}</h2>
        <form className="flex flex-wrap gap-2" onSubmit={e => { e.preventDefault(); setOffset(0); setSearch(query); }}>
          <input className={`${field} min-w-[220px] flex-1`} value={query} onChange={e => setQuery(e.target.value)} placeholder="Rechercher dans les titres, angles et justifications" aria-label="Rechercher des sujets" />
          <select className={field} value={status} onChange={e => { setStatus(e.target.value); setOffset(0); }} aria-label="Statut éditorial">
            <option value="">Tous les statuts</option>
            <option value="REVIEW">À examiner (REVIEW)</option>
            <option value="SELECTED">Sélectionnés</option>
            <option value="IGNORED">Écartés</option>
          </select>
          <button className={action} type="submit">Rechercher</button>
          {(search || status) && <button type="button" className={action} onClick={() => { setQuery(""); setSearch(""); setStatus(""); setOffset(0); }}>Effacer</button>}
        </form>
        <div className="grid gap-4 lg:grid-cols-[minmax(260px,1fr)_minmax(0,1.5fr)]">
          <div className="space-y-2">
            {loadingTopics ? <p className="text-sm text-gray-500">Chargement des sujets…</p> : topics.length === 0 ? <p className="text-sm text-gray-500">Aucun sujet pour ces critères.</p> : (
              <div className="max-h-[650px] space-y-2 overflow-y-auto pr-1">
                {topics.map(topic => <button key={topic.TOPIC_ID} type="button" onClick={() => setTopicId(topic.TOPIC_ID)}
                  className={`w-full rounded-lg border p-3 text-left text-sm ${topicId === topic.TOPIC_ID ? "border-blue-500 bg-blue-50" : "hover:bg-gray-50"}`}>
                  <span className="block font-medium">{topic.TITLE}</span>
                  <span className="mt-1 block text-xs text-gray-500">{topic.TOPIC_ID} · {topic.EVIDENCE_COUNT} preuves · {topic.EDITORIAL_STATUS}</span>
                </button>)}
              </div>
            )}
            <div className="flex items-center justify-between gap-2 pt-2">
              <button type="button" className={action} disabled={loadingTopics || offset === 0} onClick={() => setOffset(v => Math.max(0, v - pageSize))}>Précédent</button>
              <span className="text-xs text-gray-500">{offset + 1}–{offset + topics.length}</span>
              <button type="button" className={action} disabled={loadingTopics || topics.length < pageSize} onClick={() => setOffset(v => v + pageSize)}>Suivant</button>
            </div>
          </div>
          <div className="min-h-[250px] rounded-lg border p-4">
            {loadingDetail ? <p className="text-sm text-gray-500">Chargement des preuves…</p> : !detail ? (
              <p className="text-sm text-gray-500">Sélectionne un sujet pour consulter son angle et ses preuves.</p>
            ) : <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold">{detail.TITLE}</h3>
                <p className="mt-1 text-xs text-gray-500">{detail.TOPIC_ID} · {detail.EDITORIAL_STATUS} · {detail.EVIDENCE_COUNT} preuves · {detail.REVIEW_COUNT} à vérifier</p>
              </div>
              <div className="space-y-2 text-sm">
                <p><strong>Angle :</strong> {detail.ANGLE || "Non renseigné"}</p>
                <p><strong>Justification éditoriale :</strong> {detail.EDITORIAL_RATIONALE || "Non renseignée"}</p>
              </div>
              <div className="border-t pt-3">
                <h4 className="mb-3 font-semibold">Preuves documentaires ({detail.evidence.length})</h4>
                <div className="max-h-[560px] space-y-3 overflow-y-auto">
                  {detail.evidence.map(unit => <article key={unit.UNIT_ID} className="space-y-2 rounded-md border p-3 text-sm">
                    <div className="flex flex-wrap justify-between gap-2 text-xs text-gray-500">
                      <span>{unit.UNIT_ID} · page {unit.PDF_PAGE}</span><span>{unit.VERIFICATION_STATUS}</span>
                    </div>
                    <p className="font-medium">{unit.FACT}</p>
                    {unit.QUOTE && <p className="border-l-2 pl-3 text-gray-600">« {unit.QUOTE} »</p>}
                    {(unit.GEOGRAPHY || unit.PERIOD || unit.KIND) && <p className="text-xs text-gray-500">{[unit.GEOGRAPHY, unit.PERIOD, unit.KIND].filter(Boolean).join(" · ")}</p>}
                  </article>)}
                </div>
              </div>
            </div>}
          </div>
        </div>
      </section>}
    </main>
  );
}
