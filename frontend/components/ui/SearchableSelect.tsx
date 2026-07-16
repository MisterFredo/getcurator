"use client";

import { useEffect, useMemo, useRef, useState } from "react";

/* ========================================================= */

export type SelectOption = {
  id: string;
  label: string;
};

type Props = {
  label: string;
  placeholder?: string;
  required?: boolean;

  options: SelectOption[];

  value: SelectOption | null;

  onChange: (
    value: SelectOption | null,
  ) => void;
};

/* ========================================================= */

export default function SearchableSelect({
  label,
  placeholder = "Search...",
  required = false,
  options,
  value,
  onChange,
}: Props) {

  const [
    open,
    setOpen,
  ] = useState(false);

  const [
    query,
    setQuery,
  ] = useState("");

  const containerRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  /* ===================================================== */

  const filtered =
    useMemo(() => {

      const q =
        query
          .toLowerCase()
          .trim();

      if (!q) {
        return options;
      }

      return options.filter((o) =>
        o.label
          .toLowerCase()
          .includes(q)
      );

    }, [
      options,
      query,
    ]);

  /* ===================================================== */

  function select(
    option: SelectOption,
  ) {

    onChange(option);

    setOpen(false);

    setQuery("");

  }

  function clear() {

    onChange(null);

  }

  /* ===================================================== */

  useEffect(() => {

    function onClickOutside(
      e: MouseEvent,
    ) {

      if (
        containerRef.current &&
        !containerRef.current.contains(
          e.target as Node
        )
      ) {

        setOpen(false);

      }

    }

    document.addEventListener(
      "mousedown",
      onClickOutside,
    );

    return () =>
      document.removeEventListener(
        "mousedown",
        onClickOutside,
      );

  }, []);

  /* ===================================================== */

  return (

    <div
      className="space-y-2"
      ref={containerRef}
    >

      <label className="text-sm font-medium">

        {label}

        {required && (
          <span className="text-red-500">
            {" "}
            *
          </span>
        )}

      </label>

      {/* Selected */}

      {value && (

        <div className="flex">

          <span className="inline-flex items-center gap-2 px-2 py-1 rounded bg-blue-100 text-blue-700 text-xs">

            {value.label}

            <button
              type="button"
              onClick={clear}
              className="hover:text-blue-900"
            >
              ×
            </button>

          </span>

        </div>

      )}

      {/* Dropdown */}

      <div className="relative">

        <button
          type="button"
          onClick={() =>
            setOpen(!open)
          }
          className="w-full border rounded px-3 py-2 bg-white text-left"
        >

          <span className="text-gray-500">

            {value
              ? "Change selection"
              : placeholder}

          </span>

        </button>

        {open && (

          <div className="absolute z-20 mt-2 w-full bg-white border rounded shadow-lg">

            {/* Search */}

            <div className="p-2 border-b">

              <input
                autoFocus
                value={query}
                onChange={(e) =>
                  setQuery(
                    e.target.value
                  )
                }
                placeholder={placeholder}
                className="w-full border rounded px-2 py-1 text-sm"
              />

            </div>

            {/* Options */}

            <div className="max-h-64 overflow-auto">

              {filtered.length === 0 && (

                <div className="p-3 text-sm text-gray-500">
                  No results
                </div>

              )}

              {filtered.map((option) => {

                const selected =
                  value?.id ===
                  option.id;

                return (

                  <div
                    key={option.id}
                    onMouseDown={(e) => {

                      e.preventDefault();

                      e.stopPropagation();

                      select(option);

                    }}
                    className={`px-3 py-2 cursor-pointer text-sm select-none ${
                      selected
                        ? "bg-blue-50 text-blue-700"
                        : "hover:bg-gray-50"
                    }`}
                  >

                    {option.label}

                  </div>

                );

              })}

            </div>

          </div>

        )}

      </div>

    </div>

  );

}
