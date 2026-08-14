"use client";

import Link from "next/link";
import { Pencil } from "lucide-react";

import type {
  ContentRow,
} from "@/types/content";

/* ========================================================= */

type Props = {
  contents: ContentRow[];
  loading: boolean;

  selectedIds: string[];

  onSelectionChange: (
    ids: string[],
  ) => void;
};

/* ========================================================= */

export default function ContentTable({
  contents,
  loading,
  selectedIds,
  onSelectionChange,
}: Props) {

  /* =======================================================
     SELECTION
  ======================================================= */

  function toggle(
    id: string,
  ) {

    if (
      selectedIds.includes(id)
    ) {

      onSelectionChange(
        selectedIds.filter(
          (v) => v !== id,
        ),
      );

      return;

    }

    onSelectionChange([
      ...selectedIds,
      id,
    ]);

  }

  function toggleAll() {

    const allSelected =
      contents.length > 0 &&
      contents.every(
        (content) =>
          selectedIds.includes(
            content.id_content,
          ),
      );

    if (allSelected) {

      onSelectionChange([]);

      return;

    }

    onSelectionChange(
      contents.map(
        (content) =>
          content.id_content,
      ),
    );

  }

  /* =======================================================
     STATUS
  ======================================================= */

  function renderStatus(
    status: ContentRow["status"],
  ) {

    switch (status) {

      case "PUBLISHED":

        return (
          <span className="inline-flex px-2 py-1 rounded bg-green-100 text-green-700 text-xs">
            Published
          </span>
        );

      case "SCHEDULED":

        return (
          <span className="inline-flex px-2 py-1 rounded bg-blue-100 text-blue-700 text-xs">
            Scheduled
          </span>
        );

      case "READY":

        return (
          <span className="inline-flex px-2 py-1 rounded bg-purple-100 text-purple-700 text-xs">
            Ready
          </span>
        );

      case "DRAFT":

        return (
          <span className="inline-flex px-2 py-1 rounded bg-yellow-100 text-yellow-700 text-xs">
            Draft
          </span>
        );

      default:

        return (
          <span className="inline-flex px-2 py-1 rounded bg-gray-100 text-gray-600 text-xs">
            {status || "—"}
          </span>
        );

    }

  }

  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {

    return (
      <div className="border rounded-lg bg-white p-8 text-center text-gray-500">
        Loading...
      </div>
    );

  }

  /* =======================================================
     EMPTY
  ======================================================= */

  if (
    contents.length === 0
  ) {

    return (
      <div className="border rounded-lg bg-white p-8 text-center text-gray-500">
        No content found.
      </div>
    );

  }

  /* =======================================================
     SELECT ALL STATE
  ======================================================= */

  const allSelected =
    contents.length > 0 &&
    contents.every(
      (content) =>
        selectedIds.includes(
          content.id_content,
        ),
    );

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="border rounded-lg bg-white overflow-hidden">

      <table className="w-full text-sm">

        <thead className="bg-gray-100">

          <tr>

            <th className="w-10 p-3">

              <input
                type="checkbox"
                checked={allSelected}
                onChange={toggleAll}
              />

            </th>

            <th className="p-3 text-left">
              Status
            </th>

            <th className="p-3 text-left">
              Title
            </th>

            <th className="p-3 text-left">
              Source
            </th>

            <th className="p-3 text-center">
              Source
              <br />
              date
            </th>

            <th className="p-3 text-center">
              Published
            </th>

            <th className="w-20 p-3 text-right">
              Actions
            </th>

          </tr>

        </thead>

        <tbody>

          {contents.map(
            (content) => (

              <tr
                key={
                  content.id_content
                }
                className="border-t hover:bg-gray-50"
              >

                <td className="p-3">

                  <input
                    type="checkbox"
                    checked={
                      selectedIds.includes(
                        content.id_content,
                      )
                    }
                    onChange={() =>
                      toggle(
                        content.id_content,
                      )
                    }
                  />

                </td>

                <td className="p-3">

                  {renderStatus(
                    content.status,
                  )}

                </td>

                <td className="p-3">

                  <div className="font-medium">
                    {content.title || "—"}
                  </div>

                </td>

                <td className="p-3 text-gray-600">

                  {content.source_title ||
                    "—"}

                </td>

                <td className="p-3 text-center whitespace-nowrap">

                  {content.source_date
                    ? new Date(
                        content.source_date,
                      ).toLocaleDateString()
                    : "—"}

                </td>

                <td className="p-3 text-center whitespace-nowrap">

                  {content.published_at
                    ? new Date(
                        content.published_at,
                      ).toLocaleDateString()
                    : "—"}

                </td>

                <td className="p-3 text-right">

                  <Link
                    href={`/admin/content/edit/${content.id_content}`}
                    className="inline-flex text-blue-600 hover:text-blue-800"
                  >

                    <Pencil
                      size={16}
                    />

                  </Link>

                </td>

              </tr>

            ),
          )}

        </tbody>

      </table>

    </div>

  );

}
