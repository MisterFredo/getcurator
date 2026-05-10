"use client";

import { useState } from "react";
import { api } from "@/lib/api";

type SourceItem = {
  id_source: string;
  label: string;
};

export default function StockImportPanel({
  sources,
  onImported,
}: {
  sources: SourceItem[];
  onImported: () => void;
}) {

  const [file, setFile] = useState<File | null>(null);
  const [urlsText, setUrlsText] = useState("");
  const [sourceId, setSourceId] = useState("");

  // 🔥 NEW
  const [contentType, setContentType] =
    useState<"ANALYSIS" | "NEWS">("ANALYSIS");

  const [loadingFile, setLoadingFile] = useState(false);
  const [loadingUrl, setLoadingUrl] = useState(false);

  const [previewCount, setPreviewCount] = useState<number | null>(null);
  const [urlCount, setUrlCount] = useState<number | null>(null);

  const [message, setMessage] = useState("");

  // =========================
  // FILE CHANGE
  // =========================

  async function handleFileChange(f: File | null) {
    setFile(f);
    setPreviewCount(null);
    setMessage("");

    if (!f) return;

    const text = await f.text();
    const matches = text.match(/TITLE\s*:/g);
    setPreviewCount(matches ? matches.length : 0);
  }

  // =========================
  // URL CHANGE
  // =========================

  function handleUrlChange(value: string) {
    setUrlsText(value);
    setMessage("");

    const lines = value
      .split("\n")
      .map(l => l.trim())
      .filter(Boolean);

    setUrlCount(lines.length);
  }

  // =========================
  // FILE IMPORT
  // =========================

  async function handleFileImport() {
    if (!file) return alert("Choisissez un fichier");
    if (!sourceId) return alert("Choisissez une source");

    setLoadingFile(true);
    setMessage("");

    try {
      const text = await file.text();

      const res = await api.post("/content/raw/import", {
        id_source: sourceId,
        text,

        // 🔥 NEW
        content_type: contentType,
      });

      setMessage(`✅ ${res.imported} contenu(s) importé(s)`);
      setFile(null);
      setPreviewCount(null);
      onImported();

    } catch (e) {
      console.error(e);
      setMessage("❌ Erreur import fichier");
    }

    setLoadingFile(false);
  }

  // =========================
  // URL IMPORT
  // =========================

  async function handleUrlImport() {
    if (!urlsText.trim()) return alert("URLs manquantes");
    if (!sourceId) return alert("Choisissez une source");

    setLoadingUrl(true);
    setMessage("");

    try {
      const res = await api.post("/content/raw/import-urls", {
        id_source: sourceId,
        urls_text: urlsText,

        // 🔥 NEW
        content_type: contentType,
      });

      setMessage(`✅ ${res.inserted} importé(s) sur ${res.total}`);
      setUrlsText("");
      setUrlCount(null);
      onImported();

    } catch (e) {
      console.error(e);
      setMessage("❌ Erreur import URLs");
    }

    setLoadingUrl(false);
  }

  return (
    <div className="border rounded-lg p-6 bg-gray-50 space-y-6">

      <h2 className="text-lg font-semibold">
        Importer des contenus
      </h2>

      {/* SOURCE */}
      <select
        value={sourceId}
        onChange={(e) => setSourceId(e.target.value)}
        className="border rounded px-3 py-2"
      >
        <option value="">Source</option>
        {sources.map((s) => (
          <option key={s.id_source} value={s.id_source}>
            {s.label}
          </option>
        ))}
      </select>

      {/* 🔥 CONTENT TYPE */}
      <select
        value={contentType}
        onChange={(e) =>
          setContentType(
            e.target.value as "ANALYSIS" | "NEWS"
          )
        }
        className="border rounded px-3 py-2"
      >
        <option value="ANALYSIS">Analysis</option>
        <option value="NEWS">News</option>
      </select>

      {/* FILE IMPORT */}
      <div className="flex flex-wrap gap-4 items-center">
        <input
          type="file"
          accept=".txt"
          onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
        />

        {previewCount !== null && (
          <span className="text-xs text-gray-600">
            {previewCount} bloc(s) détecté(s)
          </span>
        )}

        <button
          onClick={handleFileImport}
          disabled={loadingFile}
          className="bg-black text-white px-4 py-2 rounded"
        >
          {loadingFile ? "Import..." : "Importer fichier"}
        </button>
      </div>

      {/* URL IMPORT */}
      <div className="space-y-2">
        <textarea
          value={urlsText}
          onChange={(e) => handleUrlChange(e.target.value)}
          placeholder="Une URL par ligne"
          rows={4}
          className="w-full border rounded p-2 text-sm"
        />

        {urlCount !== null && (
          <div className="text-xs text-gray-600">
            {urlCount} URL(s) détectée(s)
          </div>
        )}

        <button
          onClick={handleUrlImport}
          disabled={loadingUrl}
          className="bg-ratecard-blue text-white px-4 py-2 rounded"
        >
          {loadingUrl ? "Import..." : "Importer URLs"}
        </button>
      </div>

      {message && (
        <div className="text-sm font-medium">
          {message}
        </div>
      )}

    </div>
  );
}
