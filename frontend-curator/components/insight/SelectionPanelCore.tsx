"use client";

import { useState } from "react";

/* ========================================================= */

type Props = {
  selectedCount: number;

  renderSelection: () => React.ReactNode;
  renderAnalysis: () => React.ReactNode;

  onGenerate: () => void;
  onClose: () => void;

  loading: boolean;

  labels?: {
    title?: string;
    generate?: string;
    empty?: string;
  };
};

/* ========================================================= */

export default function SelectionPanelCore({
  selectedCount,
  renderSelection,
  renderAnalysis,
  onGenerate,
  onClose,
  loading,
  labels,
}: Props) {

  const [tab, setTab] =
    useState<"selection" | "analysis">("selection");

  return (
    <div className="h-full flex flex-col bg-white border rounded-xl overflow-hidden">

      {/* HEADER */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
        <div>
          <div className="text-sm font-semibold text-gray-900">
            {labels?.title || "Sélection"}
          </div>
          <div className="text-xs text-gray-400">
            {selectedCount} élément(s)
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
          className={`flex-1 py-2 text-xs ${
            tab === "selection"
              ? "border-b-2 border-black text-black"
              : "text-gray-400"
          }`}
        >
          Sélection
        </button>

        <button
          onClick={() => setTab("analysis")}
          className={`flex-1 py-2 text-xs ${
            tab === "analysis"
              ? "border-b-2 border-black text-black"
              : "text-gray-400"
          }`}
        >
          Analyse
        </button>
      </div>

      {/* ACTION */}
      <div className="p-3 border-b">
        <button
          onClick={() => {
            setTab("analysis");
            onGenerate();
          }}
          disabled={loading || selectedCount === 0}
          className="w-full py-2 text-xs rounded bg-black text-white disabled:opacity-50"
        >
          {labels?.generate || "Generate Analysis"}
        </button>
      </div>

      {/* CONTENT */}
      <div className="flex-1 overflow-auto p-4">

        {selectedCount === 0 && (
          <div className="text-xs text-gray-400">
            {labels?.empty || "Aucune sélection"}
          </div>
        )}

        {tab === "selection" && renderSelection()}
        {tab === "analysis" && renderAnalysis()}

      </div>
    </div>
  );
}
