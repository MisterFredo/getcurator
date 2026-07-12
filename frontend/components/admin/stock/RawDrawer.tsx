"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

type RawItem = {
  id_raw: string;
  source_title: string;
  date_source?: string | null;
  import_type?: string | null;

  // 🔥 NEW
  content_type?: string | null;

  // 🔥 NEW
  id_primary_company?: string | null;
};

type CompanyItem = {
  id_company: string;
  name: string;
};

export default function RawDrawer({
  raw,
  onClose,
  onSaved,
}: {
  raw: RawItem | null;
  onClose: () => void;
  onSaved: () => void;
}) {

  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [rawText, setRawText] = useState("");

  // 🔥 NEW
  const [contentType, setContentType] =
    useState<"ANALYSIS" | "NEWS">("ANALYSIS");

  // 🔥 NEW
  const [primaryCompanyId, setPrimaryCompanyId] =
    useState("");

  // 🔥 NEW
  const [companies, setCompanies] = useState<
    CompanyItem[]
  >([]);

  const [loading, setLoading] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");

  // 🔥 NEW
  useEffect(() => {

    async function loadCompanies() {
      try {

        const res = await api.get("/company/list");

        setCompanies(res.companies || []);

      } catch (e) {

        console.error(e);
      }
    }

    loadCompanies();

  }, []);

  useEffect(() => {
    if (!raw) return;

    setTitle(raw.source_title || "");
    setDate(raw.date_source ? raw.date_source.slice(0, 10) : "");
    setRawText("");

    // 🔥 NEW
    setContentType(
      (raw.content_type as "ANALYSIS" | "NEWS") || "ANALYSIS"
    );

    // 🔥 NEW
    setPrimaryCompanyId(
      raw.id_primary_company || ""
    );

    setError("");

    async function loadDetail() {
      try {
        setLoadingDetail(true);

        const res = await api.get(`/content/raw/detail/${raw.id_raw}`);

        setRawText(res.raw_text || "");

        // 🔥 NEW
        setPrimaryCompanyId(
          res.id_primary_company || ""
        );

      } catch (e) {
        console.error(e);
        setError("Erreur chargement détail");
      } finally {
        setLoadingDetail(false);
      }
    }

    loadDetail();
  }, [raw]);

  if (!raw) return null;

  async function handleSave() {
    try {
      setLoading(true);

      await api.put(`/content/raw/update/${raw.id_raw}`, {
        source_title: title,
        date_source: date || null,
        raw_text: rawText,

        // 🔥 NEW
        content_type: contentType,

        // 🔥 NEW
        id_primary_company:
          primaryCompanyId || null,
      });

      onSaved();
      onClose();

    } catch (e) {
      console.error(e);
      setError("Erreur sauvegarde");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-end z-50">

      <div className="w-[600px] bg-white h-full shadow-xl p-6 space-y-6 overflow-y-auto">

        {/* HEADER */}
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold">
              Éditer RAW
            </h2>
            <div className="text-xs text-gray-500">
              Import : {raw.import_type || "—"}
            </div>
          </div>
          <button onClick={onClose}>✕</button>
        </div>

        {/* ERROR */}
        {error && (
          <div className="text-sm text-red-600">
            {error}
          </div>
        )}

        {/* TITLE */}
        <div className="space-y-2">
          <label className="text-sm">Titre</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full border rounded p-2"
          />
        </div>

        {/* DATE */}
        <div className="space-y-2">
          <label className="text-sm">Date</label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-full border rounded p-2"
          />
        </div>

        {/* 🔥 CONTENT TYPE */}
        <div className="space-y-2">
          <label className="text-sm">Type de contenu</label>

          <select
            value={contentType}
            onChange={(e) =>
              setContentType(
                e.target.value as "ANALYSIS" | "NEWS"
              )
            }
            className="w-full border rounded p-2"
          >
            <option value="ANALYSIS">Analysis</option>
            <option value="NEWS">News</option>
          </select>
        </div>

        {/* 🔥 PRIMARY COMPANY */}
        <div className="space-y-2">
          <label className="text-sm">
            Primary company
          </label>

          <select
            value={primaryCompanyId}
            onChange={(e) =>
              setPrimaryCompanyId(e.target.value)
            }
            className="w-full border rounded p-2"
          >
            <option value="">
              —
            </option>

            {companies.map((c) => (
              <option
                key={c.id_company}
                value={c.id_company}
              >
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* RAW TEXT */}
        <div className="space-y-2">
          <label className="text-sm">Texte brut</label>

          {loadingDetail ? (
            <div className="text-sm text-gray-500">
              Chargement...
            </div>
          ) : (
            <textarea
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              rows={14}
              className="w-full border rounded p-2 text-xs font-mono"
            />
          )}
        </div>

        {/* SAVE */}
        <button
          onClick={handleSave}
          disabled={loading}
          className="bg-ratecard-blue text-white px-4 py-2 rounded"
        >
          {loading ? "Enregistrement..." : "Enregistrer"}
        </button>

      </div>

    </div>
  );
}
