"use client";

import { useState } from "react";
import type { FeedItem } from "@/types/feed";

/* ========================================================= */

type Props = {
  selectedItems: FeedItem[]; // 🔥 source unique

  analysis: string;
  loading: boolean;

  onGenerateInsight: () => void;
  onClose: () => void;
};

/* ========================================================= */

export default function SelectionPanel({
  selectedItems,
  analysis,
  loading,
  onGenerateInsight,
  onClose,
}: Props) {

  const [tab, setTab] = useState<"selection" | "analysis">("selection");

  /* =========================================================
     HELPERS
  ========================================================= */

  function formatDate(date?: string | null) {
    if (!date) return "";
    try {
      return new Date(date).toLocaleDateString("fr-FR");
    } catch {
      return "";
    }
  }

  /* =========================================================
     COPY
  ========================================================= */

  function selectAndCopy() {
    const id =
      tab === "selection"
        ? "selection-content"
        : "analysis-content";

    const el = document.getElementById(id);
    if (!el) return;

    const range = document.createRange();
    range.selectNodeContents(el);

    const selection = window.getSelection();
    selection?.removeAllRanges();
    selection?.addRange(range);

    try {
      navigator.clipboard.writeText(el.innerText);
    } catch {
      console.warn("copy failed");
    }
  }

  /* =========================================================
     CLEAN ANALYSIS
  ========================================================= */

  function cleanAnalysis(text: string) {
    if (!text) return "";

    const lines = text.split("\n");

    const startIndex = lines.findIndex((l) =>
      l.toUpperCase().includes("POINT")
    );

    if (startIndex === -1) return text;

    return lines.slice(startIndex).join("\n");
  }

  /* =========================================================
     RENDER ANALYSIS
  ========================================================= */

  function renderAnalysis(text: string) {
    const cleaned = cleanAnalysis(text);
    const lines = cleaned.split("\n").map((l) => l.trim());

    const blocks: any[] = [];

    lines.forEach((line, i) => {
      if (!line) return;

      if (line.includes("POINTS CLÉS")) {
        blocks.push(
          <div key={i} className="mb-4">
            <div className="text-sm font-semibold text-gray-900">
              Points clés
            </div>
          </div>
        );
        return;
      }

      if (line === "TOP 5" || line === "À NOTER") {
        blocks.push(
          <div key={i} className="mt-6 mb-3">
            <div className="text-xs uppercase tracking-wide text-gray-400">
              {line}
            </div>
          </div>
        );
        return;
      }

      if (line.startsWith("-") || line.startsWith("•")) {
        const clean = line.replace(/^[-•]\s*/, "");

        const [rawConcept, rest] = clean.split("→");

        const concept = rawConcept
          ?.replace(/^\[/, "")
          ?.replace(/\]$/, "")
          ?.trim();

        blocks.push(
          <div
            key={i}
            className="mb-3 p-3 rounded-lg border bg-gray-50"
          >
            {concept && (
              <div className="text-xs font-semibold text-gray-900 mb-1 uppercase tracking-wide">
                {concept}
              </div>
            )}

            {rest && (
              <div className="text-sm text-gray-700 leading-relaxed">
                {rest.trim()}
              </div>
            )}
          </div>
        );
        return;
      }

      blocks.push(
        <div key={i} className="text-sm text-gray-700 mb-2">
          {line}
        </div>
      );
    });

    return <div>{blocks}</div>;
  }

  function handleGenerate() {
    setTab("analysis");
    onGenerateInsight();
  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (
    <div className="h-full flex flex-col bg-white border rounded-xl overflow-hidden">

      {/* HEADER */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
        <div>
          <div className="text-sm font-semibold text-gray-900">
            Sélection
          </div>
          <div className="text-xs text-gray-400">
            {selectedItems.length} élément(s)
          </div>
        </div>

        <button
          onClick={onClose}
          className="text-xs text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>

      {/* TABS */}
      <div className="flex border-b">
        <button
          onClick={() => setTab("selection")}
          className={`flex-1 py-2 text-xs font-medium ${
            tab === "selection"
              ? "border-b-2 border-black text-black"
              : "text-gray-400"
          }`}
        >
          Sélection
        </button>

        <button
          onClick={() => setTab("analysis")}
          className={`flex-1 py-2 text-xs font-medium ${
            tab === "analysis"
              ? "border-b-2 border-black text-black"
              : "text-gray-400"
          }`}
        >
          Analyse
        </button>
      </div>

      {/* ACTIONS */}
      <div className="p-3 border-b flex gap-2">
        <button
          onClick={handleGenerate}
          disabled={loading || selectedItems.length === 0}
          className="flex-1 py-2 text-xs rounded-lg bg-black text-white disabled:opacity-50"
        >
          Générer analyse
        </button>

        <button
          onClick={selectAndCopy}
          disabled={selectedItems.length === 0}
          className="px-3 py-2 text-xs rounded-lg bg-gray-100 text-gray-700"
        >
          Sélectionner
        </button>
      </div>

      {/* CONTENT */}
      <div className="flex-1 overflow-auto p-4">

        {selectedItems.length === 0 && (
          <div className="text-xs text-gray-400">
            Sélectionne des contenus pour construire ton email
          </div>
        )}

        {/* SELECTION */}
        {tab === "selection" && (
          <div id="selection-content" className="space-y-8">

            {selectedItems.map((item, index) => (
              <div key={item.id} className="space-y-3">

                <div className="text-xs text-gray-400">
                  {formatDate(item.published_at)}
                </div>

                <div className="text-sm font-semibold text-gray-900">
                  {item.title}
                </div>

                {/* BADGES */}
                <div className="flex flex-wrap gap-1">

                  {item.companies?.map((c: any) => (
                    <span
                      key={c.id_company}
                      className="text-[10px] px-2 py-0.5 bg-blue-50 text-blue-600 rounded"
                    >
                      {c.name}
                    </span>
                  ))}

                  {item.solutions?.map((s: any) => (
                    <span
                      key={s.id_solution}
                      className="text-[10px] px-2 py-0.5 bg-purple-50 text-purple-600 rounded"
                    >
                      {s.name}
                    </span>
                  ))}

                  {item.topics?.map((t: any) => (
                    <span
                      key={t.id_topic}
                      className="text-[10px] px-2 py-0.5 bg-gray-100 text-gray-600 rounded"
                    >
                      {t.label}
                    </span>
                  ))}

                  {item.concepts?.map((c: any) => (
                    <span
                      key={c.id_concept}
                      className="text-[10px] px-2 py-0.5 bg-gray-200 text-gray-800 rounded"
                    >
                      {c.title}
                    </span>
                  ))}

                </div>

                {item.excerpt && (
                  <div className="text-sm text-gray-700 leading-relaxed">
                    {item.excerpt}
                  </div>
                )}

                {index !== selectedItems.length - 1 && (
                  <div className="border-t pt-4" />
                )}

              </div>
            ))}

          </div>
        )}

        {/* ANALYSIS */}
        {tab === "analysis" && (
          <div id="analysis-content">
            {loading && (
              <div className="text-xs text-gray-400">
                Génération en cours...
              </div>
            )}

            {!loading && !analysis && (
              <div className="text-xs text-gray-400">
                Clique sur "Générer analyse"
              </div>
            )}

            {!loading && analysis && renderAnalysis(analysis)}
          </div>
        )}

      </div>
    </div>
  );
}
