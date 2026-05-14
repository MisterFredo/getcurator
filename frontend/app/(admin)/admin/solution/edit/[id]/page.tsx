"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import HtmlEditor from "@/components/admin/HtmlEditor";
import VisualSection from "@/components/visuals/VisualSection";

const GCS_BASE_URL = process.env.NEXT_PUBLIC_GCS_BASE_URL!;
const SOLUTION_MEDIA_PATH = "solutions";

type Company = {
  id_company: string;
  name: string;
};

type AliasItem = {
  alias: string;
};

export default function EditSolution({ params }: { params: { id: string } }) {

  const { id } = params;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [content, setContent] = useState("");

  const [status, setStatus] =
    useState<"DRAFT" | "PUBLISHED">("DRAFT");

  const [idCompany, setIdCompany] =
    useState<string | null>(null);

  const [insightFrequency, setInsightFrequency] =
    useState("QUARTERLY");

  const [companies, setCompanies] =
    useState<Company[]>([]);

  // 🔥 NEW → visuel
  const [logoFilename, setLogoFilename] =
    useState<string | null>(null);

  const [aliases, setAliases] =
    useState<AliasItem[]>([]);

  const [newAlias, setNewAlias] =
    useState("");

  /* ---------------------------------------------------------
     LOAD
  --------------------------------------------------------- */

  useEffect(() => {

    async function load() {

      try {

        const res = await api.get(`/solution/${id}`);
        const sol = res.solution;

        setName(sol?.name || "");
        setDescription(sol?.description || "");
        setContent(sol?.content || "");
        setStatus(sol?.status || "DRAFT");

        setIdCompany(
          sol?.id_company || null
        );

        setInsightFrequency(
          sol?.insight_frequency || "QUARTERLY"
        );

        setLogoFilename(
          sol?.media_logo_rectangle_id || null
        );

        const compRes =
          await api.get("/company/list");

        setCompanies(
          compRes.companies || []
        );

        const aliasesRes =
          await api.get(`/solution/${id}/aliases`);

        setAliases(
          aliasesRes.aliases || []
        );

      } catch (e) {

        console.error(
          "Erreur chargement solution",
          e
        );

        alert(
          "❌ Erreur chargement solution"
        );

      } finally {

        setLoading(false);

      }

    }

    load();

  }, [id]);

  /* ---------------------------------------------------------
     ADD ALIAS
  --------------------------------------------------------- */

  async function addAlias() {

    const value = newAlias.trim();

    if (!value) return;

    try {

      await api.post(`/solution/${id}/alias`, {
        alias: value,
      });

      setAliases((prev) => [
        ...prev,
        {
          alias: value,
        },
      ]);

      setNewAlias("");

    } catch (e) {

      console.error(e);
      alert("❌ Erreur ajout alias");

    }

  }

  /* ---------------------------------------------------------
     DELETE ALIAS
  --------------------------------------------------------- */

  async function deleteAlias(alias: string) {

    const confirmed = window.confirm(
      `Supprimer l'alias "${alias}" ?`
    );

    if (!confirmed) return;

    try {

      await api.delete(
        `/solution/${id}/alias?alias=${encodeURIComponent(alias)}`
      );

      setAliases((prev) =>
        prev.filter((a) => a.alias !== alias)
      );

    } catch (e) {

      console.error(e);
      alert("❌ Erreur suppression alias");

    }

  }

  /* ---------------------------------------------------------
     SAVE
  --------------------------------------------------------- */

  async function save() {

    try {

      setSaving(true);

      await api.put(`/solution/update/${id}`, {
        name,
        description: description || null,
        content: content || null,
        status,
        id_company: idCompany || null,
        insight_frequency: insightFrequency,
      });

      alert("Solution mise à jour");

    } catch (e) {

      console.error(e);
      alert("❌ Erreur mise à jour");

    } finally {

      setSaving(false);

    }

  }

  /* ---------------------------------------------------------
     RELOAD (après upload visuel)
  --------------------------------------------------------- */

  async function reloadSolution() {

    try {

      const res = await api.get(`/solution/${id}`);
      const sol = res.solution;

      setLogoFilename(
        sol?.media_logo_rectangle_id || null
      );

      if (sol?.insight_frequency) {
        setInsightFrequency(sol.insight_frequency);
      }

    } catch (e) {

      console.error(e);
      alert("❌ Erreur rechargement solution");

    }

  }

  const rectUrl = logoFilename
    ? `${GCS_BASE_URL}/${SOLUTION_MEDIA_PATH}/${logoFilename}`
    : null;

  if (loading) return <p>Chargement…</p>;

  /* ---------------------------------------------------------
     UI
  --------------------------------------------------------- */

  return (
    <div className="space-y-8">

      <div className="flex justify-between">
        <h1 className="text-3xl font-semibold">
          Modifier solution
        </h1>

        <Link
          href="/admin/solution"
          className="underline"
        >
          ← Retour
        </Link>
      </div>

      <input
        className="border p-2 w-full rounded"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Nom de la solution"
      />

      <select
        className="border p-2 rounded w-full"
        value={idCompany || ""}
        onChange={(e) =>
          setIdCompany(e.target.value || null)
        }
      >
        <option value="">
          — Aucune société —
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

      <div className="space-y-4">

        <div>

          <label className="block font-medium mb-2">
            Aliases
          </label>

          <div className="flex gap-2 max-w-2xl">

            <input
              type="text"
              value={newAlias}
              onChange={(e) =>
                setNewAlias(e.target.value)
              }
              placeholder="Ajouter un alias"
              className="border px-3 py-2 rounded flex-1"
            />

            <button
              type="button"
              onClick={addAlias}
              className="bg-ratecard-blue text-white px-4 py-2 rounded"
            >
              Ajouter
            </button>

          </div>

        </div>

        <div className="flex flex-wrap gap-2">

          {aliases.map((item) => (

            <div
              key={item.alias}
              className="flex items-center gap-2 bg-gray-100 px-3 py-1 rounded-full text-sm"
            >

              <span>{item.alias}</span>

              <button
                type="button"
                onClick={() =>
                  deleteAlias(item.alias)
                }
                className="text-red-500 font-bold"
              >
                ×
              </button>

            </div>

          ))}

        </div>

      </div>

      <textarea
        className="border p-2 w-full rounded h-24"
        value={description}
        onChange={(e) =>
          setDescription(e.target.value)
        }
        placeholder="Description"
      />

      <HtmlEditor
        value={content}
        onChange={setContent}
      />

      <div className="space-y-2">

        <label className="block font-medium">
          Fréquence des insights
        </label>

        <select
          value={insightFrequency}
          onChange={(e) =>
            setInsightFrequency(e.target.value)
          }
          className="border px-3 py-2 rounded w-full max-w-xs"
        >
          <option value="WEEKLY">Weekly</option>
          <option value="MONTHLY">Monthly</option>
          <option value="QUARTERLY">Quarterly</option>
        </select>

      </div>

      <select
        className="border p-2 rounded"
        value={status}
        onChange={(e) =>
          setStatus(
            e.target.value as "DRAFT" | "PUBLISHED"
          )
        }
      >
        <option value="DRAFT">DRAFT</option>
        <option value="PUBLISHED">PUBLISHED</option>
      </select>

      <button
        onClick={save}
        disabled={saving}
        className="bg-ratecard-blue px-6 py-2 text-white rounded"
      >
        {saving ? "Enregistrement…" : "Enregistrer"}
      </button>

      {/* 🔥 VISUAL */}

      <VisualSection
        entityId={id}
        entityType="solution"
        rectUrl={rectUrl}
        onUpdated={reloadSolution}
      />

    </div>
  );
}
