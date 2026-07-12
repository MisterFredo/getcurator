// components/admin/company/CompanyAliases.tsx

"use client";

import { useState } from "react";

/* ========================================================= */

type Alias = {
  alias: string;
};

type Props = {
  aliases: Alias[];

  onAdd: (alias: string) => Promise<void>;

  onDelete: (alias: string) => Promise<void>;

  disabled?: boolean;
};

/* ========================================================= */

export default function CompanyAliases({

  aliases,

  onAdd,

  onDelete,

  disabled = false,

}: Props) {

  const [
    value,
    setValue,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(false);

  /* ======================================================= */

  async function handleAdd() {

    const alias =
      value.trim();

    if (!alias) {
      return;
    }

    try {

      setLoading(true);

      await onAdd(alias);

      setValue("");

    } finally {

      setLoading(false);

    }

  }

  /* ======================================================= */

  return (

    <section className="space-y-6">

      <div>

        <h2 className="text-lg font-semibold">
          Aliases
        </h2>

        <p className="text-sm text-gray-500">
          Alternative names used to identify this company.
        </p>

      </div>

      {/* =================================================== */}
      {/* ADD */}
      {/* =================================================== */}

      <div className="flex gap-3">

        <input
          value={value}
          disabled={disabled}
          onChange={(e) =>
            setValue(
              e.target.value
            )
          }
          onKeyDown={(e) => {

            if (
              e.key === "Enter"
            ) {

              e.preventDefault();

              handleAdd();

            }

          }}
          className="flex-1 border rounded px-3 py-2"
          placeholder="New alias..."
        />

        <button
          type="button"
          disabled={
            disabled ||
            loading
          }
          onClick={handleAdd}
          className="px-4 py-2 rounded bg-ratecard-blue text-white disabled:opacity-40"
        >
          Add
        </button>

      </div>

      {/* =================================================== */}
      {/* LIST */}
      {/* =================================================== */}

      {aliases.length === 0 ? (

        <div className="text-sm text-gray-500">
          No alias defined.
        </div>

      ) : (

        <div className="space-y-2">

          {aliases.map((a) => (

            <div
              key={a.alias}
              className="flex items-center justify-between border rounded px-3 py-2"
            >

              <span>
                {a.alias}
              </span>

              <button
                type="button"
                disabled={disabled}
                onClick={() =>
                  onDelete(
                    a.alias
                  )
                }
                className="text-red-600 hover:text-red-800 text-sm"
              >
                Delete
              </button>

            </div>

          ))}

        </div>

      )}

    </section>

  );

}
