"use client";

import { SelectOption } from "@/components/ui/SearchableMultiSelect";

type Props = {
  topics: SelectOption[];
  companies: SelectOption[];
  types: SelectOption[];

  onRemoveTopic: (id: string) => void;
  onRemoveCompany: (id: string) => void;
  onRemoveType: (id: string) => void;
};

export default function DigestActiveFilters({
  topics,
  companies,
  types,
  onRemoveTopic,
  onRemoveCompany,
  onRemoveType,
}: Props) {
  const hasFilters =
    topics.length > 0 ||
    companies.length > 0 ||
    types.length > 0;

  if (!hasFilters) return null;

  return (
    <div className="border border-gray-200 rounded-lg bg-gray-50 px-3 py-3 space-y-2">
      <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wide">
        Filtres actifs
      </p>

      <div className="flex flex-wrap gap-1.5">
        {topics.map((t) => (
          <Tag
            key={`topic-${t.id}`}
            label={t.label}
            onRemove={() => onRemoveTopic(t.id)}
          />
        ))}

        {companies.map((c) => (
          <Tag
            key={`company-${c.id}`}
            label={c.label}
            onRemove={() => onRemoveCompany(c.id)}
          />
        ))}

        {types.map((t) => (
          <Tag
            key={`type-${t.id}`}
            label={t.label}
            onRemove={() => onRemoveType(t.id)}
          />
        ))}
      </div>
    </div>
  );
}

function Tag({
  label,
  onRemove,
}: {
  label: string;
  onRemove: () => void;
}) {
  return (
    <span
      className="
        inline-flex items-center gap-1
        px-2 py-0.5
        bg-white
        border border-gray-200
        rounded
        text-[11px]
        text-gray-700
      "
    >
      <span className="truncate max-w-[140px]">
        {label}
      </span>

      <button
        onClick={onRemove}
        className="
          text-gray-400
          hover:text-gray-700
          text-[11px]
        "
      >
        ×
      </button>
    </span>
  );
}
