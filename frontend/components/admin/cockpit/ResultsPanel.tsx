"use client";

import {
  useState,
} from "react";

import {
  Trash2,
} from "lucide-react";

import {
  api,
} from "@/lib/api";

import type {
  QualityRow,
} from "@/types/cockpit";

/* ========================================================= */

type Props = {

  title: string;

  rows: QualityRow[];

  onDelete?: (
    contentId: string,
  ) => void;

};

/* ========================================================= */

export default function ResultsPanel({
  title,
  rows,
  onDelete,
}: Props) {

  const [
    deletingId,
    setDeletingId,
  ] = useState<string | null>(
    null,
  );

  /* ======================================================= */
  /* DUPLICATE REPORT */
  /* ======================================================= */
  
  const isDuplicateReport =
    title.trim().toLowerCase() ===
    "duplicate titles";

  /* ======================================================= */
  /* DELETE
  /* ======================================================= */

  async function handleDelete(
    contentId: string,
  ) {

    const confirmed =
      window.confirm(
        "Delete this duplicate content?"
      );

    if (!confirmed) {
      return;
    }

    try {

      setDeletingId(
        contentId,
      );

      await api.delete(
        `/cockpit/quality/duplicate-titles/${contentId}`
      );

      onDelete?.(
        contentId,
      );

    } catch (error) {

      console.error(
        "Delete duplicate error:",
        error,
      );

      alert(
        "Unable to delete duplicate."
      );

    } finally {

      setDeletingId(
        null,
      );

    }

  }

  /* ======================================================= */

  if (!title) {

    return (

      <div className="border rounded-xl bg-white p-8 text-center text-gray-500">

        Run a quality report to display its results.

      </div>

    );

  }

  return (

    <div className="border rounded-xl bg-white overflow-hidden">

      <div className="border-b bg-gray-50 px-6 py-4">

        <h2 className="text-xl font-semibold">

          {title}

        </h2>

        <p className="text-sm text-gray-500 mt-1">

          {rows.length} result{rows.length > 1 ? "s" : ""}

        </p>

      </div>

      {rows.length === 0 ? (

        <div className="p-8 text-center text-gray-500">

          No result.

        </div>

      ) : (

        <div className="overflow-auto">

          <table className="min-w-full text-sm">

            <thead className="bg-gray-100">

              <tr>

                {Object.keys(rows[0]).map((key) => (

                  <th
                    key={key}
                    className="border-b px-4 py-3 text-left font-semibold"
                  >

                    {key}

                  </th>

                ))}

                {isDuplicateReport && (

                  <th className="border-b px-4 py-3 text-right font-semibold">

                    Action

                  </th>

                )}

              </tr>

            </thead>

            <tbody>

              {rows.map((row, index) => {

                const contentId =
                  String(
                    row.ID_CONTENT ?? ""
                  );

                return (

                  <tr
                    key={
                      contentId ||
                      index
                    }
                    className="border-b hover:bg-gray-50"
                  >

                    {Object.values(row).map((value, i) => (

                      <td
                        key={i}
                        className="px-4 py-3 align-top"
                      >

                        {value === null
                          ? "—"
                          : String(value)}

                      </td>

                    ))}

                    {isDuplicateReport && (

                      <td className="px-4 py-3 text-right">

                        <button
                          type="button"
                          onClick={() =>
                            handleDelete(
                              contentId,
                            )
                          }
                          disabled={
                            !contentId ||
                            deletingId === contentId
                          }
                          className="inline-flex items-center gap-2 rounded border border-red-200 px-3 py-2 text-red-600 hover:bg-red-50 disabled:opacity-50"
                        >

                          <Trash2 size={15} />

                          {deletingId === contentId
                            ? "Deleting..."
                            : "Delete"}

                        </button>

                      </td>

                    )}

                  </tr>

                );

              })}

            </tbody>

          </table>

        </div>

      )}

    </div>

  );

}
