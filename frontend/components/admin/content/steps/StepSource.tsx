"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import DiscoveryQueue from "./DiscoveryQueue";

type Source = {
  source_id: string;
  name: string;
};

type Props = {
  // 🔥 NEW
  contentType: "ANALYSIS" | "NEWS";

  // 🔥 NEW
  primaryCompanyId?: string | null;

  onCreate: (data: {
    source_id: string;
    text: string;
    date_source?: string | null;
  }) => void;
};

export default function StepSource({
  onCreate,

  // 🔥 NEW
  contentType,

  // 🔥 NEW
  primaryCompanyId,
}: Props) {

  const [sources, setSources] = useState<Source[]>([]);
  const [sourceId, setSourceId] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [sourcePublishedAt, setSourcePublishedAt] = useState("");
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");

  const [storing, setStoring] = useState(false);

  const charCount = sourceText.length;

  // ==========================================================
  // LOAD SOURCES
  // ==========================================================

  useEffect(() => {

    async function loadSources() {
      try {
        const res = await api.get("/source/list");
        const list = res.sources || [];

        setSources(list);

        if (list.length) {
          setSourceId(list[0].source_id);

          onCreate({
            source_id: list[0].source_id,
            text: "",
          });
        }

      } catch (e) {
        console.error(e);
        alert("Impossible de charger les sources");
      }
    }

    loadSources();

  }, []);

  // ==========================================================
  // PROPAGATION AUTO AU PARENT
  // ==========================================================

  useEffect(() => {

    onCreate({
      source_id: sourceId,
      text: sourceText,
      date_source: sourcePublishedAt || null,
    });

  }, [sourceId, sourceText]); // eslint-disable-line

  // ==========================================================
  // STORE RAW
  // ==========================================================

  async function handleStore() {

    if (!sourceId) {
      alert("Source obligatoire");
      return;
    }

    if (!sourceTitle.trim()) {
      alert("Titre de la source obligatoire");
      return;
    }

    if (!sourceText.trim()) {
      alert("Texte vide");
      return;
    }

    setStoring(true);

    try {

      await api.post("/content/store-raw", {
        source_id: sourceId,
        source_title: sourceTitle,
        source_url: sourceUrl,
        raw_text: sourceText,
        date_source: sourcePublishedAt || null,

        // 🔥 NEW
        content_type: contentType,

        // 🔥 NEW
        id_primary_company: primaryCompanyId,
      });

      alert("Source stockée avec succès");

      // Reset après stockage
      setSourceText("");
      setSourcePublishedAt("");
      setSourceTitle("");
      setSourceUrl("");

    } catch (e) {
      console.error(e);
      alert("Erreur lors du stockage");
    }

    setStoring(false);
  }

  // ==========================================================
  // RENDER
  // ==========================================================

  return (

    <div className="bg-white border rounded p-5 shadow-sm space-y-4">

      <div className="flex justify-between items-center">
        <h2 className="text-base font-semibold">
          Source
        </h2>

        <div className="text-xs text-gray-500">
          {charCount} caractères
        </div>
      </div>

      <DiscoveryQueue
        onSelect={(item) => {

          setSourceId(
            item.source_id
          );

          setSourceTitle(
            item.title || ""
          );

          setSourceUrl(
            item.url || ""
          );

          setSourcePublishedAt(
            item.date_found
              ? item.date_found.slice(0, 10)
              : ""
          );
        }}
      />

      {/* SELECT SOURCE */}

      <div className="space-y-1">
        <label className="text-sm font-medium">
          Source
        </label>

        <select
          value={sourceId}
          onChange={(e) => setSourceId(e.target.value)}
          className="border rounded p-2 w-full text-sm"
        >
          {sources.map((s) => (
            <option
              key={s.source_id}
              value={s.source_id}
            >
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {/* DATE SOURCE */}

      <div className="space-y-1">
        <label className="text-sm font-medium">
          Date de publication de la source
        </label>

        <input
          type="date"
          value={sourcePublishedAt}
          onChange={(e) => setSourcePublishedAt(e.target.value)}
          className="border rounded p-2 w-full text-sm"
        />
      </div>

      {/* TITLE SOURCE */}

      <div className="space-y-1">
        <label className="text-sm font-medium">
          Titre de la source
        </label>

        <input
          type="text"
          value={sourceTitle}
          onChange={(e) => setSourceTitle(e.target.value)}
          className="border rounded p-2 w-full text-sm"
          placeholder="Ex : Amazon expands retail media strategy"
        />
      </div>

      {/* URL SOURCE */}

      <div className="space-y-1">
        <label className="text-sm font-medium">
          URL de la source
        </label>

        <input
          type="url"
          value={sourceUrl}
          onChange={(e) => setSourceUrl(e.target.value)}
          className="border rounded p-2 w-full text-sm"
          placeholder="https://..."
        />
      </div>

      {/* TEXT AREA */}

      <div className="space-y-1">
        <label className="text-sm font-medium">
          Texte brut
        </label>

        <textarea
          value={sourceText}
          onChange={(e) => setSourceText(e.target.value)}
          className="border rounded p-3 w-full h-44 text-sm"
          placeholder="Collez ici la source à analyser..."
        />

        <p className="text-xs text-gray-500">
          Minimum recommandé : 80 caractères
        </p>
      </div>

      {/* STORE BUTTON */}

      <div className="pt-2">
        <button
          onClick={handleStore}
          disabled={storing}
          className="px-4 py-2 bg-gray-800 text-white rounded text-sm"
        >
          {storing ? "Stockage..." : "Stocker"}
        </button>
      </div>

    </div>

  );

}
