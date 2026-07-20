"use client";

import type {
  DigestReview,
} from "@/types/digest";

import ReviewHeader from "./ReviewHeader";
import ReviewPreview from "./ReviewPreview";

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

    <div className="fixed inset-0 bg-black/40 flex justify-end z-50">

      <div className="w-[700px] bg-white h-full shadow-xl flex flex-col">

        <ReviewHeader
          review={review}
          onClose={onClose}
        />

        <div className="flex-1 overflow-y-auto p-6">

          <ReviewPreview
            document={
              review.document
            }
          />

        </div>

      </div>

    </div>

  );

}
