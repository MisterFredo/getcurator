"use client";

import type {
  DigestBatch,
} from "@/types/digest";

/* ========================================================= */

type Props = {
  batches: DigestBatch[];

  loading: boolean;

  selectedBatch: DigestBatch | null;

  onSelect: (
    batch: DigestBatch,
  ) => void;
};

/* ========================================================= */

export default function BatchTable({

  batches,

  loading,

  selectedBatch,

  onSelect,

}: Props) {

  if (loading) {

    return (

      <div className="border rounded-lg bg-white p-6">

        <div className="text-sm text-gray-500">

          Loading batches...

        </div>

      </div>

    );

  }

  return (

    <div className="border rounded-lg bg-white overflow-hidden">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div className="px-6 py-4 border-b">

        <h2 className="font-semibold">

          Batches

        </h2>

      </div>

      {/* ================================================= */}
      {/* TABLE */}
      {/* ================================================= */}

      <table className="w-full text-sm">

        <thead className="bg-gray-50">

          <tr className="text-left">

            <th className="px-4 py-3">
              Frequency
            </th>

            <th className="px-4 py-3">
              Audience
            </th>

            <th className="px-4 py-3">
              Period
            </th>

            <th className="px-4 py-3">
              Status
            </th>

            <th className="px-4 py-3 text-right">
              Reviews
            </th>

            <th className="px-4 py-3">
              Created
            </th>

          </tr>

        </thead>

        <tbody>

          {batches.length === 0 && (

            <tr>

              <td
                colSpan={6}
                className="px-4 py-8 text-center text-gray-500"
              >

                No batch found.

              </td>

            </tr>

          )}

          {batches.map((batch) => {

            const selected =
              selectedBatch?.id === batch.id;

            return (

              <tr

                key={batch.id}

                onClick={() =>
                  onSelect(batch)
                }

                className={`cursor-pointer border-t hover:bg-gray-50 ${
                  selected
                    ? "bg-blue-50"
                    : ""
                }`}

              >

                <td className="px-4 py-3">

                  {batch.frequency}

                </td>

                <td className="px-4 py-3">

                  {batch.audience}

                </td>

                <td className="px-4 py-3">

                  {batch.period_start}

                  {" → "}

                  {batch.period_end}

                </td>

                <td className="px-4 py-3">

                  {batch.status}

                </td>

                <td className="px-4 py-3 text-right">

                  {batch.generated_count}

                  {" / "}

                  {batch.items_count}

                </td>

                <td className="px-4 py-3">

                  {batch.created_at}

                </td>

              </tr>

            );

          })}

        </tbody>

      </table>

    </div>

  );

}
