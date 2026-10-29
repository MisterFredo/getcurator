"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { SourceOption } from "@/types/source";

type NewsletterItem = {
  title: string;
  raw_text: string;
  original_source: string | null;
  date_source: string | null;
  source_url: string | null;
  content_hash: string;
  is_existing: boolean;
  exists_in_raw: boolean;
  duplicate_in_paste: boolean;
  selected: boolean;
};

type AnalyzeResponse = {
  status: string;
  detected: number;
  existing: number;
  new: number;
  items: NewsletterItem[];
};

type StoreResponse = {
  status: string;
  requested: number;
  stored: number;
  skipped: number;
};

export default function NewsletterStudio() {
  const [sources, setSources] = useState<SourceOption[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(true);
  const [sourceId, setSourceId] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [items, setItems] = useState<NewsletterItem[]>([]);
  const [selectedHashes, setSelectedHashes] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [storing, setStoring] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function loadSources() {
      try {
        const res = await api.get("/source/list");
        if (!cancelled) setSources((res.sources || []) as SourceOption[]);
      } catch (e) {
        console.error("Newsletter sources error", e);
        if (!cancelled) setError("Impossible de charger les sources.");
      } finally {
        if (!cancelled) setSourcesLoading(false);
      }
    }
    void loadSources();
    return () => { cancelled = true; };
  }, []);

  const newItems = useMemo(() => items.filter(item => !item.is_existing && !item.duplicate_in_paste), [items]);
  const existingItems = useMemo(() => items.filter(item => item.exists_in_raw), [items]);
  const duplicateItems = useMemo(() => items.filter(item => item.duplicate_in_paste), [items]);
  const selectedItems = useMemo(() => newItems.filter(item => selectedHashes.has(item.content_hash)), [newItems, selectedHashes]);

  function resetAnalysis() {
    setItems([]);
    setSelectedHashes(new Set());
    setAnalyzed(false);
    setError("");
    setNotice("");
  }

  async function analyze() {
    if (!sourceId || !sourceText.trim()) {
      setError("Sélectionne une source et colle une newsletter.");
      return;
    }
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const res = await api.postText(
        `/discovery/newsletter-studio/analyze/${sourceId}`,
        sourceText,
      ) as AnalyzeResponse;
      const nextItems = res.items || [];
      setItems(nextItems);
      setSelectedHashes(new Set(nextItems.filter(item => !item.is_existing && !item.duplicate_in_paste).map(item => item.content_hash)));
      setAnalyzed(true);
    } catch (e) {
      console.error("Newsletter analyze error", e);
      setError("Erreur pendant l'analyse de la newsletter.");
    } finally {
      setLoading(false);
    }
  }

  function toggleItem(hash: string) {
    setSelectedHashes(current => {
      const next = new Set(current);
      if (next.has(hash)) next.delete(hash);
      else next.add(hash);
      return next;
    });
  }

  async function storeSelected() {
    if (!sourceId || !selectedItems.length) return;
    setStoring(true);
    setError("");
    setNotice("");
    try {
      const res = await api.post(
        `/discovery/newsletter-studio/store/${sourceId}`,
        { items: selectedItems.map(item => ({
          title: item.title,
          raw_text: item.raw_text,
          date_source: item.date_source,
          source_url: item.source_url,
          original_source: item.original_source,
        })) },
      ) as StoreResponse;
      // Re-analysis refreshes existing status and clears imported selections.
      const refreshed = await api.postText(
        `/discovery/newsletter-studio/analyze/${sourceId}`,
        sourceText,
      ) as AnalyzeResponse;
      const nextItems = refreshed.items || [];
      setItems(nextItems);
      setSelectedHashes(new Set(nextItems.filter(item => !item.is_existing && !item.duplicate_in_paste).map(item => item.content_hash)));
      setAnalyzed(true);
      setNotice(`${res.stored} article(s) importé(s).${res.skipped ? ` ${res.skipped} ignoré(s).` : ""}`);
    } catch (e) {
      console.error("Newsletter store error", e);
      setError("Erreur pendant l'import ou la vérification des articles.");
    } finally {
      setStoring(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded border bg-white p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium mb-2">Newsletter source</label>
          <select className="w-full rounded border px-3 py-2 text-sm bg-white" value={sourceId}
            disabled={sourcesLoading || loading || storing}
            onChange={e => { setSourceId(e.target.value); resetAnalysis(); }}>
            <option value="">{sourcesLoading ? "Loading sources..." : "Select a source"}</option>
            {sources.map(source => <option key={source.source_id} value={source.source_id}>{source.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Newsletter text</label>
          <textarea className="w-full rounded border p-3 text-sm min-h-56" value={sourceText}
            disabled={loading || storing}
            placeholder="Colle ici la newsletter complète de Mark Brown…"
            onChange={e => { setSourceText(e.target.value); if (analyzed) resetAnalysis(); }}/>
        </div>
        <button type="button" className="rounded bg-gray-900 px-5 py-2 text-white text-sm disabled:opacity-40"
          disabled={!sourceId || !sourceText.trim() || loading || storing} onClick={() => void analyze()}>
          {loading ? "Analyse en cours..." : "Analyze newsletter"}
        </button>
      </div>

      {error && <div role="alert" className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {notice && <div role="status" className="rounded border p-3 text-sm">{notice}</div>}

      {analyzed && <div className="rounded border bg-white p-6 space-y-5">
        <div className="flex flex-wrap justify-between gap-3 items-center">
          <div>
            <h3 className="font-semibold">Articles détectés : {items.length}</h3>
            <p className="text-sm text-gray-500">{newItems.length} nouveaux · {existingItems.length} déjà importés · {duplicateItems.length} doublons dans le collage</p>
          </div>
          <div className="flex gap-2">
            <button type="button" className="border rounded px-3 py-2 text-sm" disabled={storing}
              onClick={() => setSelectedHashes(new Set(newItems.map(item => item.content_hash)))}>Select all new</button>
            <button type="button" className="border rounded px-3 py-2 text-sm" disabled={storing}
              onClick={() => setSelectedHashes(new Set())}>Unselect all</button>
          </div>
        </div>
        <div className="space-y-3">
          {items.map((item, index) => {
            const disabled = item.is_existing || item.duplicate_in_paste;
            return <div key={`${item.content_hash}-${index}`} className={`rounded border p-4 ${disabled ? "opacity-50" : ""}`}>
              <div className="flex gap-3 items-start">
                <input type="checkbox" className="mt-1" disabled={disabled || storing}
                  checked={!disabled && selectedHashes.has(item.content_hash)}
                  onChange={() => toggleItem(item.content_hash)}/>
                <div className="min-w-0 flex-1 space-y-2">
                  <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                    <span>{item.original_source || "Source non précisée"}</span>
                    {item.date_source && <span>· {item.date_source}</span>}
                    {item.exists_in_raw && <span>· Already imported</span>}
                    {item.duplicate_in_paste && <span>· Duplicate in paste</span>}
                  </div>
                  <div className="font-medium">{item.title}</div>
                  {item.source_url && <a className="text-sm underline break-all" href={item.source_url} target="_blank" rel="noopener noreferrer">Original URL</a>}
                  <details className="text-sm">
                    <summary className="cursor-pointer text-gray-600">Voir le texte extrait</summary>
                    <div className="mt-3 whitespace-pre-wrap break-words text-gray-700">{item.raw_text}</div>
                  </details>
                </div>
              </div>
            </div>;
          })}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="text-sm">{selectedItems.length} article(s) sélectionné(s)</span>
          <button type="button" className="rounded bg-gray-900 px-5 py-2 text-sm text-white disabled:opacity-40"
            disabled={!selectedItems.length || storing || loading} onClick={() => void storeSelected()}>
            {storing ? "Import en cours..." : `Import ${selectedItems.length} article(s)`}
          </button>
        </div>
      </div>}
    </div>
  );
}
