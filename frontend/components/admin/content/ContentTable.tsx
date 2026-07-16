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

    } else {

      onSelectionChange([
        ...selectedIds,
        id,
      ]);

    }

  }

  function toggleAll() {

    if (
      selectedIds.length ===
      contents.length
    ) {

      onSelectionChange([]);

      return;

    }

    onSelectionChange(
      contents.map(
        (c) => c.id_content,
      ),
    );

  }

  /* ===================================================== */

  if (loading) {

    return (
      <div className="border rounded-lg bg-white p-8 text-center text-gray-500">
        Loading...
      </div>
    );

  }

  if (
    contents.length === 0
  ) {

    return (
      <div className="border rounded-lg bg-white p-8 text-center text-gray-500">
        No content found.
      </div>
    );

  }

  /* ===================================================== */

  return (

    <div className="border rounded-lg bg-white overflow-hidden">

      <table className="w-full text-sm">

        <thead className="bg-gray-100">

          <tr>

            <th className="w-10 p-3">

              <input
                type="checkbox"
                checked={
                  contents.length > 0 &&
                  selectedIds.length ===
                    contents.length
                }
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
                    checked={selectedIds.includes(
                      content.id_content,
                    )}
                    onChange={() =>
                      toggle(
                        content.id_content,
                      )
                    }
                  />

                </td>

                <td className="p-3">

                  {content.published_at ? (

                    <span className="inline-flex px-2 py-1 rounded bg-green-100 text-green-700 text-xs">
                      Published
                    </span>

                  ) : (

                    <span className="inline-flex px-2 py-1 rounded bg-yellow-100 text-yellow-700 text-xs">
                      Draft
                    </span>

                  )}

                </td>

                <td className="p-3">

                  <div className="font-medium">
                    {content.title}
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
