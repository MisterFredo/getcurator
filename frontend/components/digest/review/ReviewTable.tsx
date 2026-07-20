"use client";

import type {
  DigestBatchItem,
} from "@/types/digest";

/* ========================================================= */

type Props = {

  items: DigestBatchItem[];

  selectedItem: DigestBatchItem | null;

  onSelect: (
    item: DigestBatchItem,
  ) => void;

};

/* ========================================================= */

export default function ReviewTable({

  items,

  selectedItem,

  onSelect,

}: Props) {

  return (

    <div className="border rounded-lg bg-white overflow-hidden">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div className="px-6 py-4 border-b">

        <h2 className="font-semibold">

          Reviews

        </h2>

      </div>

      {/* ================================================= */}
      {/* TABLE */}
      {/* ================================================= */}

      <table className="w-full text-sm">

        <thead className="bg-gray-50">

          <tr className="text-left">

            <th className="px-4 py-3">
              User
            </th>

            <th className="px-4 py-3">
              Contents
            </th>

            <th className="px-4 py-3">
              Status
            </th>

            <th className="px-4 py-3">
              Generated
            </th>

          </tr>

        </thead>

        <tbody>

          {items.length === 0 && (

            <tr>

              <td
                colSpan={4}
                className="px-4 py-8 text-center text-gray-500"
              >

                No review available.

              </td>

            </tr>

          )}

          {items.map((item) => {

            const selected =
              selectedItem?.id === item.id;

            return (

              <tr

                key={item.id}

                onClick={() =>
                  onSelect(item)
                }

                className={`cursor-pointer border-t hover:bg-gray-50 ${
                  selected
                    ? "bg-blue-50"
                    : ""
                }`}

              >

                <td className="px-4 py-3">

                  {item.user_id}

                </td>

                <td className="px-4 py-3">

                  {item.selected_contents}

                </td>

                <td className="px-4 py-3">

                  {item.status}

                </td>

                <td className="px-4 py-3">

                  {item.generated_at
                    ? new Date(
                        item.generated_at
                      ).toLocaleString()
                    : "-"}

                </td>

              </tr>

            );

          })}

        </tbody>

      </table>

    </div>

  );

}
