"use client";

import type {
  DigestReview,
} from "@/types/digest";

/* ========================================================= */

type Props = {

  reviews: DigestReview[];

  selectedReview: DigestReview | null;

  onSelect: (
    review: DigestReview,
  ) => void;

};

/* ========================================================= */

export default function ReviewTable({

  reviews,

  selectedReview,

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

          {reviews.length === 0 && (

            <tr>

              <td
                colSpan={4}
                className="px-4 py-8 text-center text-gray-500"
              >

                No review available.

              </td>

            </tr>

          )}

          {reviews.map((review) => {

            const selected =
              selectedReview?.id === review.id;

            return (

              <tr

                key={review.id}

                onClick={() =>
                  onSelect(review)
                }

                className={`cursor-pointer border-t hover:bg-gray-50 ${
                  selected
                    ? "bg-blue-50"
                    : ""
                }`}

              >

                <td className="px-4 py-3">

                  {review.user_id}

                </td>

                <td className="px-4 py-3">

                  {review.analyzed_contents}

                  {" / "}

                  {review.total_contents}

                </td>

                <td className="px-4 py-3">

                  Generated

                </td>

                <td className="px-4 py-3">

                  {review.created_at}

                </td>

              </tr>

            );

          })}

        </tbody>

      </table>

    </div>

  );

}
