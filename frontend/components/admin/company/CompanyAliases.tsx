// components/admin/company/CompanyAliases.tsx

"use client";

import { useState } from "react";

import {
  CompanyAlias,
} from "@/types/company";

/* ========================================================= */

type Props = {
  aliases: CompanyAlias[];

  onAdd: (
    alias: string,
  ) => Promise<void>;

  onDelete: (
    alias: string,
  ) => Promise<void>;

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

  /* =======================================================
     ADD
  ======================================================= */

  async function handleAdd() {

    const alias =
      value.trim();

    if (!alias) {
      return;
    }

    if (
      aliases.some(
        (a) =>
          a.alias.toLowerCase() ===
          alias.toLowerCase()
      )
    ) {
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

  /* =======================================================
     DELETE
  ======================================================= */

  async function handleDelete(
    alias: string,
  ) {

    const ok = confirm(
      `Delete alias "${alias}"?`
    );

    if (!ok) {
      return;
    }

    await onDelete(alias);

  }

  /* =======================================================
     RENDER
  ======================================================= */

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
          placeholder="New alias..."
          className="flex-1 border rounded px-3 py-2"
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
        />

        <button
          type="button"
          onClick={handleAdd}
          disabled={
            disabled ||
            loading ||
            !value.trim()
          }
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

          {aliases.map((alias) => (

            <div
              key={alias.alias}
              className="flex items-center justify-between border rounded px-3 py-2"
            >

              <span>

                {alias.alias.trim()}

              </span>

              <button
                type="button"
                disabled={disabled}
                onClick={() =>
                  handleDelete(
                    alias.alias
                  )
                }
                className="text-sm text-red-600 hover:text-red-800"
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
