"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

import MultiSelectTopics, {
  Topic,
} from "@/components/admin/content/steps/MultiSelectTopics";

import MultiSelectConcepts, {
  Concept,
} from "@/components/admin/content/steps/MultiSelectConcepts";

import CompanySelector, {
  Company,
} from "@/components/admin/CompanySelector";

import SolutionSelector, {
  Solution,
} from "@/components/admin/SolutionSelector";

type Props = {
  topicsRaw: string[];
  acteursRaw: string[];
  conceptsRaw: string[];
  solutionsRaw: string[];

  topics: string[];
  companies: string[];
  concepts: string[];
  solutions: string[];

  onChange: (data: {
    topics?: string[];
    companies?: string[];
    concepts?: string[];
    solutions?: string[];
  }) => void;

  onSave: () => void;
};

export default function StepValidation({
  topicsRaw,
  acteursRaw,
  conceptsRaw,
  solutionsRaw,
  topics,
  companies,
  concepts,
  solutions,
  onChange,
  onSave,
}: Props) {

  const [allTopics, setAllTopics] = useState<Topic[]>([]);
  const [allCompanies, setAllCompanies] = useState<Company[]>([]);
  const [allConcepts, setAllConcepts] = useState<Concept[]>([]);
  const [allSolutions, setAllSolutions] = useState<Solution[]>([]);

  // ============================================================
  // LOAD DATA
  // ============================================================

  useEffect(() => {

    async function load() {
      try {

        const [
          topicRes,
          companyRes,
          conceptRes,
          solutionRes,
        ] = await Promise.all([
          api.get("/topic/list"),
          api.get("/company/list"),
          api.get("/concept/list"),
          api.get("/solution/list"),
        ]);

        setAllTopics(
          (topicRes?.topics || []).map((t: any) => ({
            ID_TOPIC: t.id_topic,
            LABEL: t.label,
          }))
        );

        setAllCompanies(
          (companyRes?.companies || []).map((c: any) => ({
            id_company: c.id_company,
            name: c.name,
          }))
        );

        // 🔥 FORMAT ALIGNÉ MultiSelectConcepts
        setAllConcepts(
          (conceptRes?.concepts || []).map((c: any) => ({
            ID_CONCEPT: c.id_concept,
            LABEL: c.title,
          }))
        );

        setAllSolutions(
          (solutionRes?.solutions || []).map((s: any) => ({
            id_solution: s.id_solution,
            name: s.name,
          }))
        );

      } catch (e) {
        console.error("Erreur chargement validation", e);
      }
    }

    load();

  }, []);

  // ============================================================
  // AUTO-INJECT LLM (TOPICS + CONCEPTS)
  // ============================================================

  const [autoInjected, setAutoInjected] = useState(false);

  useEffect(() => {

    if (!autoInjected) {

      // 🔵 TOPICS
      if (topicsRaw?.length > 0) {
        onChange({ topics: topicsRaw });
      }

      // 🟣 CONCEPTS → mapping label → ID
      if (conceptsRaw?.length > 0 && allConcepts.length > 0) {

        const mapped = conceptsRaw
          .map((label) => {
            const match = allConcepts.find(
              (c) =>
                c.LABEL.toLowerCase() === label.toLowerCase()
            );
            return match?.ID_CONCEPT;
          })
          .filter(Boolean) as string[];

        if (mapped.length > 0) {
          onChange({ concepts: mapped });
        }
      }

      setAutoInjected(true);
    }

  }, [topicsRaw, conceptsRaw, allConcepts, autoInjected, onChange]);

  // ============================================================
  // MAPPING IDS → OBJECTS
  // ============================================================

  const selectedCompanies = allCompanies.filter((c) =>
    companies.includes(c.id_company)
  );

  const selectedSolutions = allSolutions.filter((s) =>
    solutions.includes(s.id_solution)
  );

  // ============================================================
  // UI
  // ============================================================

  return (

    <div className="space-y-6">

      <div className="text-sm font-semibold text-gray-700">
        Validation structurante
      </div>

      {/* RAW DISPLAY */}

      <div className="space-y-2 text-xs text-gray-500 border-b pb-3">

        {topicsRaw?.length > 0 && (
          <div>
            <strong>Topics LLM :</strong> {topicsRaw.join(", ")}
          </div>
        )}

        {acteursRaw?.length > 0 && (
          <div>
            <strong>Acteurs LLM :</strong> {acteursRaw.join(", ")}
          </div>
        )}

        {conceptsRaw?.length > 0 && (
          <div>
            <strong>Concepts LLM :</strong> {conceptsRaw.join(", ")}
          </div>
        )}

        {solutionsRaw?.length > 0 && (
          <div>
            <strong>Solutions LLM :</strong> {solutionsRaw.join(", ")}
          </div>
        )}

      </div>

      {/* TOPICS */}

      <MultiSelectTopics
        topics={allTopics}
        selected={topics}
        onChange={(ids: string[]) =>
          onChange({ topics: ids })
        }
      />

      {/* COMPANIES */}

      <CompanySelector
        values={selectedCompanies}
        onChange={(vals) =>
          onChange({
            companies: vals.map((v) => v.id_company),
          })
        }
      />

      {/* CONCEPTS — 🔥 VERSION BULLES */}

      <MultiSelectConcepts
        concepts={allConcepts}
        selected={concepts}
        onChange={(ids: string[]) =>
          onChange({ concepts: ids })
        }
      />

      {/* SOLUTIONS */}

      <SolutionSelector
        values={selectedSolutions}
        onChange={(vals) =>
          onChange({
            solutions: vals.map((v) => v.id_solution),
          })
        }
      />

      {/* SAVE */}

      <button
        onClick={onSave}
        className="w-full px-4 py-2 bg-black text-white rounded text-sm"
        type="button"
      >
        Sauvegarder la validation
      </button>

    </div>

  );

}
