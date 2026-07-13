"use client";

import Link from "next/link";
import { Pencil } from "lucide-react";

export type ContentRow = {
  id_content: string;
  title: string;
  source_title?: string | null;
  source_date?: string | null;
  published_at?: string | null;
};

type Props = {
  contents: ContentRow[];
  loading: boolean;
};

export default function ContentTable({
  contents,
  loading,
}: Props) {

  if (loading) {
    return (
      <div className="border rounded-lg bg-white p-8 text-center text-gray-500">
        Loading contents...
      </div>
    );
  }

  if (contents.length === 0) {
    return (
      <div className="border rounded-lg bg-white p-8 text-center text-gray-500">
        No content found.
      </div>
    );
  }

  return (
    <div className="border rounded-lg bg-white overflow-hidden">

      <table className="w-full text-sm">

        <thead className="bg-gray-100 text-left">
          <tr>
            <th className="p-3">Title</th>
            <th className="p-3">Source</th>
            <th className="p-3">Source date</th>
            <th className="p-3">Published</th>
            <th className="p-3 w-24 text-right">
              Actions
            </th>
          </tr>
        </thead>

        <tbody>

          {contents.map((content) => (

            <tr
              key={content.id_content}
              className="border-t hover:bg-gray-50"
            >

              <td className="p-3 font-medium">
                {content.title}
              </td>

              <td className="p-3">
                {content.source_title || "—"}
              </td>

              <td className="p-3">
                {content.source_date
                  ? new Date(
                      content.source_date
                    ).toLocaleDateString()
                  : "—"}
              </td>

              <td className="p-3">
                {content.published_at
                  ? new Date(
                      content.published_at
                    ).toLocaleDateString()
                  : "—"}
              </td>

              <td className="p-3 text-right">

                <Link
                  href={`/admin/content/edit/${content.id_content}`}
                  className="inline-flex text-blue-600 hover:text-blue-800"
                >
                  <Pencil size={16} />
                </Link>

              </td>

            </tr>

          ))}

        </tbody>

      </table>

    </div>
  );
}
