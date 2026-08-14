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

  /* =======================================================
     UPDATE
  ======================================================= */

  function update<K extends keyof ContentFilters>(
    key: K,
    value: ContentFilters[K],
  ) {
    onChange({
      ...filters,
      [key]: value,
    });
  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (
    <div className="border rounded-lg bg-white p-4 space-y-4">

      {/* =================================================== */}
      {/* ROW 1 */}
      {/* =================================================== */}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-12 gap-3 items-end">

        {/* SEARCH */}

        <div className="xl:col-span-3">
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Search
          </label>

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
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        {/* STATUS */}

        <div className="xl:col-span-2">
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Status
          </label>

          <select
            value={filters.status}
            onChange={(e) =>
              update(
                "status",
                e.target.value as ContentFilters["status"],
              )
            }
            className="w-full border rounded px-3 py-2 text-sm bg-white"
          >
            <option value="">
              All statuses
            </option>

            <option value="DRAFT">
              Draft
            </option>

            <option value="PUBLISHED">
              Published
            </option>
          </select>
        </div>

        {/* COMPANY */}

        <div className="xl:col-span-2">
          <SearchableSelect
            label="Company"
            placeholder="All companies"
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
        </div>

        {/* SOLUTION */}

        <div className="xl:col-span-2">
          <SearchableSelect
            label="Solution"
            placeholder="All solutions"
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
        </div>

        {/* TOPIC */}

        <div className="xl:col-span-3">
          <SearchableSelect
            label="Topic"
            placeholder="All topics"
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
        </div>

      </div>

      {/* =================================================== */}
      {/* ROW 2 */}
      {/* =================================================== */}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-12 gap-3 items-end">

        {/* CONCEPT */}

        <div className="xl:col-span-3">
          <SearchableSelect
            label="Concept"
            placeholder="All concepts"
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
        </div>

        {/* SOURCE */}

        <div className="xl:col-span-3">
          <SearchableSelect
            label="Source"
            placeholder="All sources"
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

        {/* FROM */}

        <div className="xl:col-span-2">
          <label className="block text-xs font-medium text-gray-600 mb-1">
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
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        {/* TO */}

        <div className="xl:col-span-2">
          <label className="block text-xs font-medium text-gray-600 mb-1">
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
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        {/* RESET */}

        <div className="xl:col-span-2">
          <button
            type="button"
            onClick={onReset}
            className="w-full border rounded px-3 py-2 text-sm hover:bg-gray-50"
          >
            Reset
          </button>
        </div>

      </div>

    </div>
  );
}
