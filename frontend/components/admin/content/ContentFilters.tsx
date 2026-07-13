"use client";

import type { ContentFilters } from "@/types/content";
import type { CompanyOption } from "@/types/company";
import type { SolutionOption } from "@/types/solution";
import type { TopicOption } from "@/types/topic";
import type { ConceptOption } from "@/types/concept";
import type { SourceOption } from "@/types/source";

type Props = {
  filters: ContentFilters;
  onChange: (filters: ContentFilters) => void;

  companies: CompanyOption[];
  solutions: SolutionOption[];
  topics: TopicOption[];
  concepts: ConceptOption[];
  sources: SourceOption[];

  onSearch: () => void;
  onReset: () => void;
};

export default function ContentFilters({
  filters,
  onChange,
  companies,
  solutions,
  topics,
  concepts,
  sources,
  onSearch,
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

      {/* Header */}

      {/* Quick Search */}

      {/* Entity filters */}

      {/* Date */}

      {/* Options */}

      {/* Actions */}

    </div>
  );
}ontent
