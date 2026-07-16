"use client";

import type {
  QualityRow,
} from "@/types/cockpit";

/* ========================================================= */

type Props = {
  title: string;

  rows: QualityRow[];
};

/* ========================================================= */

export default function ResultsPanel({
  title,
  rows,
}: Props) {

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

              </tr>

            </thead>

            <tbody>

              {rows.map((row, index) => (

                <tr
                  key={index}
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

                </tr>

              ))}

            </tbody>

          </table>

        </div>

      )}

    </div>

  );

}
