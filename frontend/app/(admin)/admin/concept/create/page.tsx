"use client";

import Link from "next/link";

import ConceptForm from "@/components/admin/concept/ConceptForm";

/* ========================================================= */

export default function CreateConceptPage() {

  return (

    <div className="space-y-10">

      <div className="flex justify-between items-center">

        <div>

          <h1 className="text-3xl font-semibold">
            Create concept
          </h1>

        </div>

        <Link
          href="/admin/concept"
          className="underline"
        >
          ← Back
        </Link>

      </div>

      <ConceptForm
        mode="create"
      />

    </div>

  );

}
