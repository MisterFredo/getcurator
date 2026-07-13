"use client";

import Link from "next/link";

import { useParams } from "next/navigation";

import ConceptForm from "@/components/admin/concept/ConceptForm";

/* ========================================================= */

export default function EditConceptPage() {

  const params =
    useParams();

  return (

    <div className="space-y-10">

      <div className="flex justify-between items-center">

        <div>

          <h1 className="text-3xl font-semibold">
            Edit concept
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
        mode="edit"
        conceptId={
          params.id as string
        }
      />

    </div>

  );

}
