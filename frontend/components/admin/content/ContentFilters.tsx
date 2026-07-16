"use client";

import SearchableSelect from "@/components/ui/SearchableSelect";

import type { ContentFilters } from "@/types/content";
import type { CompanyOption } from "@/types/company";
import type { SolutionOption } from "@/types/solution";
import type { TopicOption } from "@/types/topic";
import type { ConceptOption } from "@/types/concept";
import type { SourceOption } from "@/types/source";

/* ========================================================= */

type Props = {
  filters: ContentFilters;
  onChange: (filters: ContentFilters) => void;

  companies: CompanyOption[];
  solutions: SolutionOption[];
  topics: TopicOption[];
  concepts: ConceptOption[];
  sources: SourceOption[];

  onReset: () => void;
};

/* ========================================================= */

export default function ContentFilters({
  filters,
  onChange,
  companies,
  solutions,
  topics,
  concepts,
  sources,
  onReset,
}: Props) {

  function update<K extends keyof ContentFilters>(
    key: K,
    value: ContentFilters[K],
  ) {

    onChange({
      ...filters,
      [key]: value,
    });

  }

  return (

    <div className="border rounded-lg bg-white p-6 space-y-6">

      {/* =================================================== */}
      {/* HEADER */}
      {/* =================================================== */}

      <div>

        <h2 className="text-xl font-semibold">
          Filters
        </h2>

        <p className="text-sm text-gray-500">
          Search and narrow down contents.
        </p>

      </div>

      {/* =================================================== */}
      {/* QUICK SEARCH */}
      {/* =================================================== */}

      <div>

        <input
          type="text"
          value={filters.search}
          onChange={(e) =>
            update(
              "search",
              e.target.value,
            )
          }
          placeholder="Search title..."
          className="w-full border rounded px-3 py-2"
        />

      </div>

      {/* =================================================== */}
      {/* ENTITIES */}
      {/* =================================================== */}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">

        <SearchableSelect
          label="Company"
          placeholder="Select company..."
          options={companies.map((c) => ({
            id: c.id_company,
            label: c.name,
          }))}
          value={
            companies
              .filter(
                (c) =>
                  c.id_company ===
                  filters.company_id,
              )
              .map((c) => ({
                id: c.id_company,
                label: c.name,
              }))[0] || null
          }
          onChange={(value) =>
            update(
              "company_id",
              value?.id || "",
            )
          }
        />

        <SearchableSelect
          label="Solution"
          placeholder="Select solution..."
          options={solutions.map((s) => ({
            id: s.id_solution,
            label: s.name,
          }))}
          value={
            solutions
              .filter(
                (s) =>
                  s.id_solution ===
                  filters.solution_id,
              )
              .map((s) => ({
                id: s.id_solution,
                label: s.name,
              }))[0] || null
          }
          onChange={(value) =>
            update(
              "solution_id",
              value?.id || "",
            )
          }
        />

        <SearchableSelect
          label="Topic"
          placeholder="Select topic..."
          options={topics.map((t) => ({
            id: t.id_topic,
            label: t.label,
          }))}
          value={
            topics
              .filter(
                (t) =>
                  t.id_topic ===
                  filters.topic_id,
              )
              .map((t) => ({
                id: t.id_topic,
                label: t.label,
              }))[0] || null
          }
          onChange={(value) =>
            update(
              "topic_id",
              value?.id || "",
            )
          }
        />

        <SearchableSelect
          label="Concept"
          placeholder="Select concept..."
          options={concepts.map((c) => ({
            id: c.id_concept,
            label: c.label,
          }))}
          value={
            concepts
              .filter(
                (c) =>
                  c.id_concept ===
                  filters.concept_id,
              )
              .map((c) => ({
                id: c.id_concept,
                label: c.label,
              }))[0] || null
          }
          onChange={(value) =>
            update(
              "concept_id",
              value?.id || "",
            )
          }
        />

        <SearchableSelect
          label="Source"
          placeholder="Select source..."
          options={sources.map((s) => ({
            id: s.source_id,
            label: s.name,
          }))}
          value={
            sources
              .filter(
                (s) =>
                  s.source_id ===
                  filters.source_id,
              )
              .map((s) => ({
                id: s.source_id,
                label: s.name,
              }))[0] || null
          }
          onChange={(value) =>
            update(
              "source_id",
              value?.id || "",
            )
          }
        />

      </div>

      {/* =================================================== */}
      {/* DATES */}
      {/* =================================================== */}

      <div className="grid gap-4 md:grid-cols-2">

        <div>

          <label className="block text-sm font-medium mb-2">
            From
          </label>

          <input
            type="date"
            value={filters.date_from}
            onChange={(e) =>
              update(
                "date_from",
                e.target.value,
              )
            }
            className="w-full border rounded px-3 py-2"
          />

        </div>

        <div>

          <label className="block text-sm font-medium mb-2">
            To
          </label>

          <input
            type="date"
            value={filters.date_to}
            onChange={(e) =>
              update(
                "date_to",
                e.target.value,
              )
            }
            className="w-full border rounded px-3 py-2"
          />

        </div>

      </div>

      {/* =================================================== */}
      {/* OPTIONS */}
      {/* =================================================== */}

      <label className="flex items-center gap-3">

        <input
          type="checkbox"
          checked={filters.only_numbers}
          onChange={(e) =>
            update(
              "only_numbers",
              e.target.checked,
            )
          }
        />

        <span className="text-sm">
          Only contents containing numbers
        </span>

      </label>

      {/* =================================================== */}
      {/* ACTIONS */}
      {/* =================================================== */}

      <div className="flex justify-end">

        <button
          type="button"
          onClick={onReset}
          className="px-4 py-2 border rounded hover:bg-gray-50"
        >
          Reset filters
        </button>

      </div>

    </div>

  );

}
