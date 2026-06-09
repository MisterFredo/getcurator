"use client";

import { useState } from "react";
import { api } from "@/lib/api";

type SourceItem = {
  id_source: string;
  label: string;
};

type Props = {
  sources: SourceItem[];
  onImported: () => void;
};

export default function StockImportPanel({
  sources,
  onImported,
}: Props) {

  const [csvFile, setCsvFile] =
    useState<File | null>(null);

  const [urlsText, setUrlsText] =
    useState("");

  const [sourceId, setSourceId] =
    useState("");

  const [contentType, setContentType] =
    useState<"ANALYSIS" | "NEWS">(
      "ANALYSIS"
    );

  const [loadingCsv, setLoadingCsv] =
    useState(false);

  const [loadingUrl, setLoadingUrl] =
    useState(false);

  const [urlCount, setUrlCount] =
    useState<number | null>(null);

  const [message, setMessage] =
    useState("");

  // =========================
  // URL CHANGE
  // =========================

  function handleUrlChange(
    value: string
  ) {

    setUrlsText(value);
    setMessage("");

    const lines = value
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);

    setUrlCount(lines.length);
  }

  // =========================
  // CSV IMPORT
  // =========================

  async function handleCsvImport() {

    if (!csvFile) {
      return alert(
        "Choisissez un fichier CSV"
      );
    }

    if (!sourceId) {
      return alert(
        "Choisissez une source"
      );
    }

    setLoadingCsv(true);
    setMessage("");

    try {

      const csvText =
        await csvFile.text();

      const res = await api.post(
        "/content/raw/import-csv",
        {
          id_source: sourceId,

          content_type:
            contentType,

          csv_text:
            csvText,
        }
      );

      setMessage(
        `✅ ${res.inserted} importé(s) sur ${res.total}`
      );

      setCsvFile(null);

      onImported();

    } catch (e) {

      console.error(e);

      setMessage(
        "❌ Erreur import CSV"
      );
    }

    setLoadingCsv(false);
  }

  // =========================
  // URL IMPORT
  // =========================

  async function handleUrlImport() {

    if (!urlsText.trim()) {
      return alert(
        "URLs manquantes"
      );
    }

    if (!sourceId) {
      return alert(
        "Choisissez une source"
      );
    }

    setLoadingUrl(true);
    setMessage("");

    try {

      const res = await api.post(
        "/content/raw/import-urls",
        {
          id_source:
            sourceId,

          urls_text:
            urlsText,

          content_type:
            contentType,
        }
      );

      setMessage(
        `✅ ${res.inserted} importé(s) sur ${res.total}`
      );

      setUrlsText("");
      setUrlCount(null);

      onImported();

    } catch (e) {

      console.error(e);

      setMessage(
        "❌ Erreur import URLs"
      );
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
        onChange={(e) =>
          setSourceId(
            e.target.value
          )
        }
        className="border rounded px-3 py-2"
      >
        <option value="">
          Source
        </option>

        {sources.map((s) => (
          <option
            key={s.id_source}
            value={s.id_source}
          >
            {s.label}
          </option>
        ))}
      </select>

      {/* CONTENT TYPE */}

      <select
        value={contentType}
        onChange={(e) =>
          setContentType(
            e.target
              .value as
              | "ANALYSIS"
              | "NEWS"
          )
        }
        className="border rounded px-3 py-2"
      >
        <option value="ANALYSIS">
          Analysis
        </option>

        <option value="NEWS">
          News
        </option>
      </select>

      {/* CSV IMPORT */}

      <div className="space-y-3 border rounded p-4 bg-white">

        <h3 className="font-medium">
          Import CSV
        </h3>

        <div className="text-xs text-gray-500">
          Format attendu :
          <br />
          URL,ID_PRIMARY_COMPANY
        </div>

        <input
          type="file"
          accept=".csv"
          onChange={(e) =>
            setCsvFile(
              e.target.files?.[0]
                || null
            )
          }
        />

        {csvFile && (
          <div className="text-xs text-gray-600">
            {csvFile.name}
          </div>
        )}

        <button
          onClick={
            handleCsvImport
          }
          disabled={
            loadingCsv
          }
          className="bg-black text-white px-4 py-2 rounded"
        >
          {loadingCsv
            ? "Import..."
            : "Importer CSV"}
        </button>

      </div>

      {/* URL IMPORT */}

      <div className="space-y-3 border rounded p-4 bg-white">

        <h3 className="font-medium">
          Import URLs
        </h3>

        <textarea
          value={urlsText}
          onChange={(e) =>
            handleUrlChange(
              e.target.value
            )
          }
          placeholder="Une URL par ligne"
          rows={5}
          className="w-full border rounded p-2 text-sm"
        />

        {urlCount !== null && (
          <div className="text-xs text-gray-600">
            {urlCount} URL(s)
            détectée(s)
          </div>
        )}

        <button
          onClick={
            handleUrlImport
          }
          disabled={
            loadingUrl
          }
          className="bg-ratecard-blue text-white px-4 py-2 rounded"
        >
          {loadingUrl
            ? "Import..."
            : "Importer URLs"}
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
