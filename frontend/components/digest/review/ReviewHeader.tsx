"use client";

import type {
  DigestReview,
} from "@/types/digest";

/* ========================================================= */

type Props = {

  review: DigestReview;

  onClose: () => void;

};

/* ========================================================= */

export default function ReviewHeader({

  review,

  onClose,

}: Props) {

  return (

    <div className="border-b bg-white px-6 py-5">

      <div className="flex items-start justify-between">

        {/* ============================================= */}
        {/* LEFT */}
        {/* ============================================= */}

        <div>

          <h2 className="text-lg font-semibold">

            Digest Review

          </h2>

          <div className="mt-2 space-y-1 text-sm text-gray-500">

            <div>

              User : {review.user_id}

            </div>

            <div>

              Contents :

              {" "}

              {review.analyzed_contents}

              {" / "}

              {review.total_contents}

            </div>

            <div>

              Generated :

              {" "}

              {review.created_at}

            </div>

          </div>

        </div>

        {/* ============================================= */}
        {/* RIGHT */}
        {/* ============================================= */}

        <div className="flex items-center gap-3">

          <button
            className="rounded-md border px-4 py-2 text-sm hover:bg-gray-50"
          >
            Regenerate
          </button>

          <button
            className="rounded-md bg-ratecard-blue px-4 py-2 text-sm text-white hover:opacity-90"
          >
            Send
          </button>

          <button
            onClick={onClose}
            className="text-gray-500 hover:text-black"
          >
            ✕

          </button>

        </div>

      </div>

    </div>

  );

}
