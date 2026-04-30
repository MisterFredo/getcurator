"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import HtmlEditor from "@/components/admin/HtmlEditor";

type Universe = {
  id_universe: string;
  label: string;
};

export default function CreateTopic() {

  const [label, setLabel] = useState("");

  const [universes, setUniverses] = useState<Universe[]>([]);
  const [selectedUniverses, setSelectedUniverses] = useState<string[]>([]);

  const [description, setDescription] = useState("");
  const [seoTitle, setSeoTitle] = useState("");
  const [seoDescription, setSeoDescription] = useState("");

  const [insightFrequency, setInsightFrequency] =
    useState("QUARTERLY");

  const [loading, setLoading] = useState(false);
  const [createdId, setCreatedId] = useState<string | null>(null);

  // ============================================================
  // LOAD UNIVERS
  // ============================================================

  useEffect(() => {
    async function loadUniverses() {
      try {
        const res = await api.get("/universe/list");
        setUniverses(res?.universes || []);
      } catch (e) {
        console.error("❌ erreur univers", e);
      }
    }

    loadUniverses();
  }, []);

  // ============================================================
  // HANDLE SELECT
  // ============================================================

  function toggleUniverse(id: string) {
    setSelectedUniverses((prev) =>
      prev.includes(id)
        ? prev.filter((u) => u !== id)
        : [...prev, id]
    );
  }

  // ============================================================
  // SAVE
  // ============================================================

  async function save() {

    if (!label.trim()) {
      alert("Label requis");
      return;
    }

    if (selectedUniverses.length === 0) {
      alert("Sélectionner au moins un univers");
      return;
    }

    try {

      setLoading(true);

      const res = await api.post("/topic/create", {
        label,
        description: description || null,
        seo_title: seoTitle || null,
        seo_description: seoDescription || null,
        insight_frequency: insightFrequency,
        universe_ids: selectedUniverses,
      });

      if (!res.id_topic) {
        alert("Erreur création topic");
        return;
      }

      setCreatedId(res.id_topic);

      alert("Topic créé avec succès");

      // reset
      setLabel("");
      setSelectedUniverses([]);
      setDescription("");
      setSeoTitle("");
      setSeoDescription("");
      setInsightFrequency("QUARTERLY");

    } catch (e) {

      console.error(e);
      alert("❌ Erreur création topic");

    } finally {

      setLoading(false);

    }

  }

  return (
    <div className="space-y-10">

      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">
          Ajouter un topic
        </h1>

        <Link href="/admin/topic" className="underline">
          ← Retour
        </Link>
      </div>

      {/* LABEL */}
      <div className="space-y-2 max-w-2xl">
        <label className="block text-sm font-medium">
          Label
        </label>

        <input
          className="border p-2 w-full rounded"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
        />
      </div>

      {/* UNIVERS */}
      <div className="space-y-2 max-w-2xl">
        <label className="block text-sm font-medium">
          Univers
        </label>

        <div className="flex flex-wrap gap-2">
          {universes.map((u) => (
            <button
              key={u.id_universe}
              type="button"
              onClick={() => toggleUniverse(u.id_universe)}
              className={`px-3 py-1 rounded border ${
                selectedUniverses.includes(u.id_universe)
                  ? "bg-blue-600 text-white"
                  : "bg-white"
              }`}
            >
              {u.label}
            </button>
          ))}
        </div>
      </div>

      {/* DESCRIPTION */}
      <div className="space-y-2 max-w-2xl">
        <label className="block text-sm font-medium">
          Description éditoriale
        </label>

        <HtmlEditor
          value={description}
          onChange={setDescription}
        />
      </div>

      {/* FREQUENCE */}
      <div className="space-y-2 max-w-2xl">
        <label className="block text-sm font-medium">
          Fréquence des insights
        </label>

        <select
          value={insightFrequency}
          onChange={(e) => setInsightFrequency(e.target.value)}
          className="border px-3 py-2 rounded w-full max-w-xs"
        >
          <option value="WEEKLY">Weekly</option>
          <option value="MONTHLY">Monthly</option>
          <option value="QUARTERLY">Quarterly</option>
        </select>
      </div>

      {/* SEO */}
      <div className="space-y-4 max-w-2xl">

        <div>
          <label className="block text-sm font-medium mb-1">
            SEO title
          </label>

          <input
            className="border p-2 w-full rounded"
            value={seoTitle}
            onChange={(e) => setSeoTitle(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            SEO description
          </label>

          <textarea
            className="border p-2 w-full rounded h-20"
            value={seoDescription}
            onChange={(e) =>
              setSeoDescription(e.target.value)
            }
          />
        </div>

      </div>

      <button
        onClick={save}
        disabled={loading}
        className="bg-ratecard-blue px-4 py-2 text-white rounded disabled:opacity-50"
      >
        {loading ? "Création…" : "Créer"}
      </button>

      {createdId && (
        <p className="text-green-600 text-sm">
          Topic créé (ID : {createdId})
        </p>
      )}

    </div>
  );
}
