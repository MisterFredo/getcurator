"use client";

import { useState } from "react";
import { api } from "@/lib/api";

import EditableList from "@/components/admin/content/steps/EditableList";

type Props = {
  sourceId: string | null;
  sourceText: string;

  // 🔥 NEW
  contentType?: "ANALYSIS" | "NEWS";

  // 🔥 NEW
  primaryCompanyId?: string | null;

  title: string;
  title_en: string;

  excerpt: string;
  excerpt_en: string;

  contentBody: string;

  chiffres: string[];

  acteurs: string[];
  concepts: string[];
  solutions: string[];
  topics: string[];

  mecanique: string;
  enjeu: string;
  friction: string;
  signal: string;

  onChange: (data: any) => void;

  onNext: () => void;
};

export default function StepSummary(
  props: Props
) {

  const [loading, setLoading] =
    useState(false);

  // =====================================================
  // HELPERS
  // =====================================================

  function normalizeList(
    input: any
  ): string[] {

    if (!input) return [];

    if (Array.isArray(input)) {

      return input
        .flatMap((item) => {

          if (
            typeof item === "string"
          ) {
            return item.split(
              /[,;\n]/
            );
          }

          return [];

        })
        .map((x) => x.trim())
        .filter(Boolean);

    }

    if (typeof input === "string") {

      return input
        .split(/[,;\n]/)
        .map((x) => x.trim())
        .filter(Boolean);

    }

    return [];
  }

  function stripHtmlList(
    text: string
  ): string {

    if (!text) return "";

    return text
      .replace(/<\/?ul>/g, "")
      .replace(/<\/?li>/g, "\n")
      .trim();
  }

  // =====================================================
  // GENERATE (LLM)
  // =====================================================

  async function generate() {

    if (!props.sourceText?.trim()) {
      return;
    }

    setLoading(true);

    try {

      const res = await api.post(
        "/content/ai/generate",
        {

          // 🔥 NEW
          id_primary_company:
            props.primaryCompanyId,

          source_text:
            props.sourceText,

          source_id:
            props.sourceId,
        }
      );

      props.onChange({

        title:
          res.title || "",

        title_en:
          res.title_en || "",

        excerpt:
          res.excerpt || "",

        excerpt_en:
          res.excerpt_en || "",

        contentBody:
          stripHtmlList(
            res.content_body || ""
          ),

        chiffres:
          normalizeList(
            res.chiffres
          ),

        acteurs:
          normalizeList(
            res.acteurs_cites
          ),

        // 🔥 ALIGNÉ
        concepts:
          normalizeList(
            res.concepts
          ),

        solutions:
          normalizeList(
            res.solutions
          ),

        topics:
          res.topics || [],

        mecanique:
          res.mecanique_expliquee || "",

        enjeu:
          res.enjeu_strategique || "",

        friction:
          res.point_de_friction || "",

        signal:
          res.signal_analytique || "",

      });

    } catch (e) {

      console.error(e);

      alert("Erreur génération");

    }

    setLoading(false);
  }

  // =====================================================
  // RENDER
  // =====================================================

  return (

    <div className="space-y-8">

      {/* HEADER */}

      <div className="flex justify-between items-center border-b pb-3">

        <h2 className="text-base font-semibold">
          Synthèse & Analyse
        </h2>

        <button
          onClick={generate}
          disabled={loading}
          className="px-3 py-1.5 bg-black text-white rounded text-sm"
        >
          {loading
            ? "Génération..."
            : "Générer"}
        </button>

      </div>

      {/* ================= ÉDITORIAL ================= */}

      <div className="space-y-4">

        <div>

          <label className="block text-sm font-medium mb-1">
            Title
          </label>

          <textarea
            value={props.title}
            onChange={(e) =>
              props.onChange({
                title:
                  e.target.value
              })
            }
            className="w-full border rounded p-3 min-h-[70px] text-sm"
          />

        </div>

        <div>

          <label className="block text-sm font-medium mb-1">
            Title EN
          </label>

          <textarea
            value={props.title_en}
            onChange={(e) =>
              props.onChange({
                title_en:
                  e.target.value
              })
            }
            className="w-full border rounded p-3 min-h-[70px] text-sm"
          />

        </div>

        <div>

          <label className="block text-sm font-medium mb-1">
            Résumé exécutif
          </label>

          <textarea
            value={props.excerpt}
            onChange={(e) =>
              props.onChange({
                excerpt:
                  e.target.value
              })
            }
            className="w-full border rounded p-3 min-h-[90px] text-sm"
          />

        </div>

        <div>

          <label className="block text-sm font-medium mb-1">
            Résumé exécutif EN
          </label>

          <textarea
            value={props.excerpt_en}
            onChange={(e) =>
              props.onChange({
                excerpt_en:
                  e.target.value
              })
            }
            className="w-full border rounded p-3 min-h-[90px] text-sm"
          />

        </div>

        <div>

          <label className="block text-sm font-medium mb-1">
            Points clés
          </label>

          <textarea
            value={props.contentBody}
            onChange={(e) =>
              props.onChange({
                contentBody:
                  e.target.value
              })
            }
            className="w-full border rounded p-3 min-h-[170px] text-sm"
          />

        </div>

      </div>

      {/* ================= EXTRACTIONS LLM ================= */}

      <div className="space-y-4 border-t pt-4">

        <h3 className="text-sm font-semibold text-gray-700">
          Extractions LLM
        </h3>

        <div className="bg-gray-50 border rounded p-4 space-y-4">

          <EditableList
            label="Topics suggérés"
            items={props.topics}
            onChange={(items) =>
              props.onChange({
                topics: items
              })
            }
          />

          <EditableList
            label="Acteurs cités"
            items={props.acteurs}
            onChange={(items) =>
              props.onChange({
                acteurs: items
              })
            }
          />

          <EditableList
            label="Concepts"
            items={props.concepts}
            onChange={(items) =>
              props.onChange({
                concepts: items
              })
            }
          />

          <EditableList
            label="Solutions"
            items={props.solutions}
            onChange={(items) =>
              props.onChange({
                solutions: items
              })
            }
          />

          <EditableList
            label="Chiffres clés"
            items={props.chiffres}
            onChange={(items) =>
              props.onChange({
                chiffres: items
              })
            }
          />

        </div>

      </div>

      {/* ================= ANALYSE ================= */}

      <div className="space-y-4 border-t pt-4">

        <h3 className="text-sm font-semibold text-gray-700">
          Analyse stratégique
        </h3>

        <div>

          <label className="block text-sm font-medium mb-1">
            Mécanique expliquée
          </label>

          <textarea
            value={props.mecanique}
            onChange={(e) =>
              props.onChange({
                mecanique:
                  e.target.value
              })
            }
            className="w-full border rounded p-3 min-h-[110px] text-sm"
          />

        </div>

        <div>

          <label className="block text-sm font-medium mb-1">
            Enjeu stratégique
          </label>

          <textarea
            value={props.enjeu}
            onChange={(e) =>
              props.onChange({
                enjeu:
                  e.target.value
              })
            }
            className="w-full border rounded p-3 min-h-[110px] text-sm"
          />

        </div>

        <div>

          <label className="block text-sm font-medium mb-1">
            Point de friction
          </label>

          <textarea
            value={props.friction}
            onChange={(e) =>
              props.onChange({
                friction:
                  e.target.value
              })
            }
            className="w-full border rounded p-3 min-h-[90px] text-sm"
          />

        </div>

        <div>

          <label className="block text-sm font-medium mb-1">
            Signal analytique
          </label>

          <textarea
            value={props.signal}
            onChange={(e) =>
              props.onChange({
                signal:
                  e.target.value
              })
            }
            className="w-full border rounded p-3 min-h-[110px] text-sm"
          />

        </div>

      </div>

      {/* ================= SAVE ================= */}

      <button
        onClick={props.onNext}
        className="px-4 py-2 bg-green-600 text-white rounded text-sm"
      >
        Sauvegarder l'éditorial
      </button>

    </div>
  );
}
