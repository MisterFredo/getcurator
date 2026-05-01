"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

import TopicSelector from "@/components/admin/TopicSelector";
import CompanySelector from "@/components/admin/CompanySelector";
import ConceptSelector, {
  Concept,
} from "@/components/admin/ConceptSelector";
import SolutionSelector, {
  Solution,
} from "@/components/admin/SolutionSelector";

import PersonSelector, {
  PersonRef,
  ArticlePerson,
} from "@/components/admin/PersonSelector";

import HtmlEditor from "@/components/admin/HtmlEditor";

/* =========================================================
   TYPES
========================================================= */

type NewsType = {
  code: string;
  label: string;
};

type Props = {
  title: string;
  excerpt: string;
  body: string;

  company: any | null;
  topics: any[];
  persons: ArticlePerson[];

  concepts: Concept[];
  solutions: Solution[];

  newsKind: "NEWS" | "BRIEF";
  newsType?: string | null;

  onChange: (d: {
    title?: string;
    excerpt?: string;
    body?: string;
    company?: any | null;
    topics?: any[];
    persons?: ArticlePerson[];
    concepts?: Concept[];
    solutions?: Solution[];
    newsKind?: "NEWS" | "BRIEF";
    newsType?: string | null;
  }) => void;

  onValidate: () => void;
  saving: boolean;
};

/* =========================================================
   COMPONENT
========================================================= */

export default function NewsStepContent({
  title,
  excerpt,
  body,
  company,
  topics,
  persons,
  concepts,
  solutions,
  newsKind,
  newsType = null,
  onChange,
  onValidate,
  saving,
}: Props) {

  /* =====================================================
     NEWS TYPES
  ===================================================== */

  const [newsTypes, setNewsTypes] = useState<NewsType[]>([]);
  const [loadingTypes, setLoadingTypes] = useState(true);

  useEffect(() => {
    async function loadTypes() {
      try {
        const res = await api.get("/news/types");
        setNewsTypes(res.types || []);
      } catch (e) {
        console.error("Erreur chargement NEWS_TYPE", e);
        setNewsTypes([]);
      } finally {
        setLoadingTypes(false);
      }
    }

    loadTypes();
  }, []);

  /* =====================================================
     PERSONNES
  ===================================================== */

  const [allPersons, setAllPersons] = useState<PersonRef[]>([]);

  useEffect(() => {
    async function loadPersons() {
      try {
        const res = await api.get("/person/list");

        setAllPersons(
          (res.persons || []).map((p: any) => ({
            id_person: p.id_person,
            name: p.name,
            title: p.title || "",
            id_company: p.id_company || null,
          }))
        );
      } catch (e) {
        console.error("Erreur chargement personnes", e);
        setAllPersons([]);
      }
    }

    loadPersons();
  }, []);

  /* =====================================================
     UI
  ===================================================== */

  return (
    <div className="space-y-8">

      {/* TYPE */}
      <div>
        <label className="block font-medium mb-2">
          Type de contenu
        </label>

        <div className="flex gap-6">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              checked={newsKind === "NEWS"}
              onChange={() => onChange({ newsKind: "NEWS" })}
            />
            <span>News</span>
          </label>

          <label className="flex items-center gap-2">
            <input
              type="radio"
              checked={newsKind === "BRIEF"}
              onChange={() => onChange({ newsKind: "BRIEF" })}
            />
            <span>Brève</span>
          </label>
        </div>
      </div>

      {/* CATÉGORIE */}
      <div>
        <label className="block font-medium mb-2">
          Catégorie éditoriale
        </label>

        <select
          className="border rounded p-2 w-full"
          disabled={loadingTypes}
          value={newsType || ""}
          onChange={(e) =>
            onChange({ newsType: e.target.value || null })
          }
        >
          <option value="">— Non renseignée —</option>

          {newsTypes.map((t) => (
            <option key={t.code} value={t.code}>
              {t.label}
            </option>
          ))}
        </select>
      </div>

      {/* TAXONOMIE */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">

        <CompanySelector
          values={company ? [company] : []}
          onChange={(items) => {
            onChange({ company: items[0] || null });
            onChange({ persons: [] });
          }}
        />

        <TopicSelector
          values={topics}
          onChange={(items) => onChange({ topics: items })}
        />

        {/* ✅ Concepts indépendants des topics */}
        <ConceptSelector
          values={concepts}
          onChange={(items) => onChange({ concepts: items })}
        />

        <SolutionSelector
          values={solutions}
          onChange={(items) => onChange({ solutions: items })}
        />

      </div>

      {/* TITRE */}
      <div>
        <label className="block font-medium mb-2">
          Titre *
        </label>
        <input
          type="text"
          className="w-full border rounded p-2"
          value={title}
          onChange={(e) => onChange({ title: e.target.value })}
        />
      </div>

      {/* EXCERPT */}
      <div>
        <label className="block font-medium mb-2">
          Excerpt *
        </label>
        <textarea
          className="w-full border rounded p-2 h-24"
          value={excerpt}
          onChange={(e) => onChange({ excerpt: e.target.value })}
        />
      </div>

      {/* BODY */}
      {newsKind === "NEWS" && (
        <HtmlEditor
          value={body}
          onChange={(html) => onChange({ body: html })}
        />
      )}

      {/* PERSONNES */}
      <PersonSelector
        values={persons}
        persons={allPersons}
        companyId={company?.id_company || null}
        onChange={(items) => onChange({ persons: items })}
      />

      {/* ACTION */}
      <button
        onClick={onValidate}
        disabled={saving}
        className="bg-ratecard-green text-white px-6 py-2 rounded"
      >
        {saving ? "Sauvegarde…" : "Enregistrer"}
      </button>

    </div>
  );
}
