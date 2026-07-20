"use client";

import ReviewSections from "./ReviewSections";

import type {
  DigestDocument,
} from "@/types/digest";

/* ========================================================= */

type Props = {

  document: DigestDocument;

};

/* ========================================================= */

export default function ReviewPreview({

  document,

}: Props) {

  return (

    <div className="overflow-hidden rounded-lg border bg-white">

      {/* ================================================ */}
      {/* TITLE */}
      {/* ================================================ */}

      <div className="border-b px-8 py-6">

        <h1 className="text-2xl font-semibold">

          {document.title}

        </h1>

        <div className="mt-2 text-sm text-gray-500">

          {document.period}

        </div>

      </div>

      {/* ================================================ */}
      {/* BODY */}
      {/* ================================================ */}

      <div className="space-y-8 px-8 py-8">

        <ReviewSections

          sections={document.sections}

        />

      </div>

    </div>

  );

}
