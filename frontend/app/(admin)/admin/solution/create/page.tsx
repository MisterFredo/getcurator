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

export default function CreateSolution() {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [content, setContent] = useState("");
  const [aliasesInput, setAliasesInput] = useState("");

  const [status, setStatus] =
    useState<"DRAFT" | "PUBLISHED">("DRAFT");
  const [idCompany, setIdCompany] =
    useState<string | null>(null);
  const [insightFrequency, setInsightFrequency] =
    useState("QUARTERLY");
  const [companies, setCompanies] =
    useState<Company[]>([]);
  const [loading, setLoading] =
    useState(false);
  const [solutionId, setSolutionId] =
    useState<string | null>(null);
  const [logoFilename, setLogoFilename] =
    useState<string | null>(null);

  /* ---------------------------------------------------------
     LOAD COMPANIES
  --------------------------------------------------------- */

  useEffect(() => {
    async function loadCompanies() {
      try {
        const res = await api.get("/company/list");

        setCompanies(
          res.companies || []
        );

      } catch (e) {
        console.error(
          "Erreur chargement sociétés",
          e
        );

        setCompanies([]);
      }
    }

    loadCompanies();

  }, []);

  /* ---------------------------------------------------------
     SAVE
  --------------------------------------------------------- */

  async function save() {
    if (!name.trim()) {
      alert("Nom requis");
      return;
    }

    try {
      setLoading(true);

      const aliases = aliasesInput
        .split(";")
        .map((a) => a.trim())
        .filter(Boolean);

      const res = await api.post(
        "/solution/create",
        {
          name,
          description:
            description || null,

          content:
            content || null,

          status,

          id_company:
            idCompany || null,

          insight_frequency:
            insightFrequency,

          aliases,
        }
      );

      if (!res.id_solution) {
        throw new Error(
          "ID solution manquant"
        );
      }

      setSolutionId(
        res.id_solution
      );

      alert(
        "Solution créée. Vous pouvez maintenant ajouter un logo."
      );

    } catch (e) {
      console.error(e);

      alert(
        "❌ Erreur création"
      );

    } finally {
      setLoading(false);
    }
  }

  /* ---------------------------------------------------------
     RELOAD SOLUTION
  --------------------------------------------------------- */

  async function reloadSolution() {
    if (!solutionId) return;

    try {
      const s = await api.get(
        `/solution/${solutionId}`
      );

      setLogoFilename(
        s.media_logo_rectangle_id || null
      );

      if (s.insight_frequency) {
        setInsightFrequency(
          s.insight_frequency
        );
      }

    } catch (e) {
      console.error(e);

      alert(
        "❌ Erreur rechargement solution"
      );
    }
  }

  const rectUrl = logoFilename
    ? `${GCS_BASE_URL}/${SOLUTION_MEDIA_PATH}/${logoFilename}`
    : null;

  /* ---------------------------------------------------------
     UI
  --------------------------------------------------------- */

  return (
    <div className="space-y-10">

      <div className="flex justify-between">
        <h1 className="text-2xl font-semibold">
          Ajouter une solution
        </h1>

        <Link
          href="/admin/solution"
          className="underline"
        >
          ← Retour
        </Link>
      </div>

      {/* NAME */}

      <input
        className="border p-2 w-full rounded"
        placeholder="Nom de la solution"
        value={name}
        onChange={(e) =>
          setName(e.target.value)
        }
      />

      {/* COMPANY */}

      <select
        className="border p-2 rounded w-full"
        value={idCompany || ""}
        onChange={(e) =>
          setIdCompany(
            e.target.value || null
          )
        }
      >
        <option value="">
          — Aucune société associée —
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

      {/* ALIASES */}

      <div className="space-y-2">
        <label className="block font-medium">
          Aliases
        </label>

        <input
          className="border p-2 w-full rounded"
          placeholder="Alias 1 ; Alias 2 ; Alias 3"
          value={aliasesInput}
          onChange={(e) =>
            setAliasesInput(
              e.target.value
            )
          }
        />

        <p className="text-sm text-gray-500">
          Séparer les aliases avec ;
        </p>
      </div>

      {/* DESCRIPTION */}

      <textarea
        className="border p-2 w-full rounded h-24"
        placeholder="Description courte"
        value={description}
        onChange={(e) =>
          setDescription(
            e.target.value
          )
        }
      />

      {/* CONTENT */}

      <HtmlEditor
        value={content}
        onChange={setContent}
      />

      {/* FREQUENCY */}

      <div className="space-y-2">
        <label className="block font-medium">
          Fréquence des insights
        </label>

        <select
          value={insightFrequency}
          onChange={(e) =>
            setInsightFrequency(
              e.target.value
            )
          }
          className="border px-3 py-2 rounded w-full max-w-xs"
        >
          <option value="WEEKLY">
            Weekly
          </option>

          <option value="MONTHLY">
            Monthly
          </option>

          <option value="QUARTERLY">
            Quarterly
          </option>
        </select>
      </div>

      {/* STATUS */}

      <select
        className="border p-2 rounded w-full max-w-xs"
        value={status}
        onChange={(e) =>
          setStatus(
            e.target.value as
              | "DRAFT"
              | "PUBLISHED"
          )
        }
      >
        <option value="DRAFT">
          DRAFT
        </option>

        <option value="PUBLISHED">
          PUBLISHED
        </option>
      </select>

      {/* CTA */}

      <button
        onClick={save}
        disabled={loading}
        className="bg-ratecard-blue px-6 py-2 text-white rounded"
      >
        {loading
          ? "Création…"
          : "Créer"}
      </button>

      {/* VISUAL */}

      {solutionId && (
        <VisualSection
          entityId={solutionId}
          entityType="solution"
          rectUrl={rectUrl}
          onUpdated={reloadSolution}
        />
      )}

    </div>
  );
}
