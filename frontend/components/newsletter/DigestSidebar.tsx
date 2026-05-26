"use client";

import { useState } from "react";
import NewsletterSelector from "@/components/newsletter/NewsletterSelector";
/* =========================================================
   TYPES
========================================================= */

type DigestModel = {
  id_template: string;
  name: string;
  topics: string[];
  companies: string[];
  news_types: string[];
};

type Props = {
  models: DigestModel[];
  selectedModelId: string;
  setSelectedModelId: (id: string) => void;

  onSearch: () => void;
  loading: boolean;

  news: any[];
  breves: any[];
  analyses: any[];

  selectedNewsIds: string[];
  setSelectedNewsIds: (ids: string[]) => void;

  selectedBriefIds: string[];
  setSelectedBriefIds: (ids: string[]) => void;

  selectedAnalysisIds: string[];
  setSelectedAnalysisIds: (ids: string[]) => void;

  introText: string;
  setIntroText: (v: string) => void;

  hasMore: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
};

/* =========================================================
   COMPONENT
========================================================= */

export default function DigestSidebar({
  models,
  selectedModelId,
  setSelectedModelId,
  onSearch,
  loading,

  news,
  breves,
  analyses,

  selectedNewsIds,
  setSelectedNewsIds,
  selectedBriefIds,
  setSelectedBriefIds,
  selectedAnalysisIds,
  setSelectedAnalysisIds,

  introText,
  setIntroText,

  hasMore,
  loadingMore,
  onLoadMore,
}: Props) {

  const [openNews, setOpenNews] = useState(true);
  const [openBreves, setOpenBreves] = useState(true);
  const [openAnalyses, setOpenAnalyses] = useState(true);

  const totalSelected =
    selectedNewsIds.length +
    selectedBriefIds.length +
    selectedAnalysisIds.length;

  return (
    <div className="h-full flex flex-col border rounded bg-white overflow-hidden">

      {/* =========================
          STICKY SELECTION PANEL
      ========================== */}
      <div className="sticky top-0 bg-white z-10 border-b p-4 space-y-4">

        <div className="space-y-1">
          <h2 className="text-sm font-semibold">
            Sélection
          </h2>
          <div className="text-xs text-gray-500">
            {selectedNewsIds.length} News ·{" "}
            {selectedBriefIds.length} Brèves ·{" "}
            {selectedAnalysisIds.length} Analyses
          </div>
        </div>

        <textarea
          value={introText}
          onChange={(e) => setIntroText(e.target.value)}
          placeholder="Introduction de la newsletter..."
          className="w-full border rounded p-2 text-sm min-h-[80px]"
        />

        <div className="flex gap-2 items-center">

          <select
            value={selectedModelId}
            onChange={(e) =>
              setSelectedModelId(e.target.value)
            }
            className="border rounded px-2 py-1 text-xs"
          >
            <option value="">
              Flux global
            </option>
            {models.map((m) => (
              <option
                key={m.id_template}
                value={m.id_template}
              >
                {m.name}
              </option>
            ))}
          </select>

          <button
            onClick={onSearch}
            disabled={loading}
            className="px-3 py-1.5 rounded bg-black text-white text-xs"
          >
            {loading ? "Recherche…" : "Rechercher"}
          </button>
        </div>

      </div>

      {/* =========================
          RESULTS (SCROLLABLE)
      ========================== */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">

        {/* NEWS */}
        <div>
          <button
            onClick={() => setOpenNews(!openNews)}
            className="text-sm font-semibold mb-2"
          >
            {openNews ? "▼" : "▶"} News ({news.length})
          </button>

          {openNews && (
            <NewsletterSelector
              title=""
              items={news}
              selectedIds={selectedNewsIds}
              onChange={setSelectedNewsIds}
              labelKey="title"
            />
          )}
        </div>

        {/* BRÈVES */}
        <div>
          <button
            onClick={() => setOpenBreves(!openBreves)}
            className="text-sm font-semibold mb-2"
          >
            {openBreves ? "▼" : "▶"} Brèves ({breves.length})
          </button>

          {openBreves && (
            <NewsletterSelector
              title=""
              items={breves}
              selectedIds={selectedBriefIds}
              onChange={setSelectedBriefIds}
              labelKey="title"
            />
          )}
        </div>

        {/* ANALYSES */}
        <div>
          <button
            onClick={() => setOpenAnalyses(!openAnalyses)}
            className="text-sm font-semibold mb-2"
          >
            {openAnalyses ? "▼" : "▶"} Analyses ({analyses.length})
          </button>

          {openAnalyses && (
            <NewsletterSelector
              title=""
              items={analyses}
              selectedIds={selectedAnalysisIds}
              onChange={setSelectedAnalysisIds}
              labelKey="title"
            />
          )}
        </div>

        {/* LOAD MORE */}
        {hasMore && (
          <div className="text-center pt-4">
            <button
              onClick={onLoadMore}
              disabled={loadingMore}
              className="px-3 py-1.5 border rounded text-xs"
            >
              {loadingMore
                ? "Chargement…"
                : "Charger plus"}
            </button>
          </div>
        )}

      </div>

    </div>
  );
}
