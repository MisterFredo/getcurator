"use client";

import type {
  DigestDocument,
} from "@/types/digest";

import DigestSection from "./DigestSection";

type Props = {
  document: DigestDocument;
};

export default function DigestPreview({
  document,
}: Props) {

  return (

    <div className="space-y-6">

      <div className="rounded-lg border bg-white p-6">

        <h1 className="text-3xl font-bold">

          {document.title}

        </h1>

        {document.subtitle && (

          <p className="mt-2 text-gray-600">

            {document.subtitle}

          </p>

        )}

        <div className="mt-4 text-sm text-gray-500">

          {document.period}

        </div>

      </div>

      {document.sections.map((section) => (

        <DigestSection
          key={section.id}
          section={section}
        />

      ))}

    </div>

  );

}
