"use client";

import ReviewHeader from "./ReviewHeader";
import ReviewPreview from "./ReviewPreview";

import type {
  DigestReview,
} from "@/types/digest";

/* ========================================================= */

type Props = {

  review: DigestReview | null;

  onClose: () => void;

};

/* ========================================================= */

export default function ReviewStudio({

  review,

  onClose,

}: Props) {

  if (!review)
    return null;

  return (

    <div className="fixed inset-0 z-50 flex justify-end bg-black/40">

      <div className="flex h-full w-[720px] flex-col bg-white shadow-xl">

        {/* ================================================ */}
        {/* HEADER */}
        {/* ================================================ */}

        <ReviewHeader

          review={review}

          onClose={onClose}

        />

        {/* ================================================ */}
        {/* BODY */}
        {/* ================================================ */}

        <div className="flex-1 overflow-y-auto bg-gray-50 p-6">

          <div className="mx-auto max-w-[820px]">

            <ReviewPreview

              document={review.document}

            />

          </div>

        </div>

      </div>

    </div>

  );

}
