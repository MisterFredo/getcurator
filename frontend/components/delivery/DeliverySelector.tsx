"use client";

import { useCallback, useMemo } from "react";

type Props<T> = {
  title: string;
  items: T[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;

  labelKey?: keyof T;
  metaKey?: keyof T;
};

export default function NewsletterSelector<
  T extends { id: string }
>({
  title,
  items,
  selectedIds,
  onChange,
  labelKey,
  metaKey,
}: Props<T>) {

  const toggle = useCallback(
    (id: string) => {
      const isSelected = selectedIds.includes(id);

      if (isSelected) {
        onChange(selectedIds.filter((x) => x !== id));
      } else {
        onChange([...selectedIds, id]);
      }
    },
    [selectedIds, onChange]
  );

  const selectedSet = useMemo(
    () => new Set(selectedIds),
    [selectedIds]
  );

  return (
    <section className="space-y-2">

      {title && (
        <h2 className="text-sm font-semibold tracking-tight">
          {title}
        </h2>
      )}

      <div
        className="
          max-h-[260px]
          overflow-y-auto
          border border-gray-200
          rounded-lg
          bg-white
          divide-y
        "
      >
        {items.length === 0 && (
          <div className="px-4 py-4 text-xs text-gray-400">
            Aucun élément disponible
          </div>
        )}

        {items.map((item) => {
          const resolvedLabelKey =
            labelKey ?? ("title" as keyof T);

          const label = String(
            item[resolvedLabelKey] ?? ""
          );

          const meta =
            metaKey && item[metaKey]
              ? String(item[metaKey])
              : null;

          const checked =
            selectedSet.has(item.id);

          return (
            <div
              key={item.id}
              className={`
                group
                flex items-start gap-2
                px-3 py-2
                text-sm
                cursor-pointer
                transition-colors duration-100
                ${
                  checked
                    ? "bg-gray-50"
                    : "hover:bg-gray-50"
                }
              `}
              onClick={() => toggle(item.id)}
            >
              <div className="pt-[2px]">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() =>
                    toggle(item.id)
                  }
                  onClick={(e) =>
                    e.stopPropagation()
                  }
                  className="
                    h-3.5 w-3.5
                    accent-black
                    cursor-pointer
                  "
                />
              </div>

              <div className="flex-1 min-w-0 flex flex-col gap-[2px]">
                <span
                  className="
                    text-gray-900
                    leading-snug
                    font-medium
                    break-words
                  "
                >
                  {label}
                </span>

                {meta && (
                  <span
                    className="
                      text-[10px]
                      text-gray-400
                      uppercase
                      tracking-wide
                    "
                  >
                    {meta}
                  </span>
                )}
              </div>

              {checked && (
                <div
                  className="
                    text-[9px]
                    font-semibold
                    uppercase
                    tracking-wide
                    text-black
                    opacity-50
                  "
                >
                  ✓
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
