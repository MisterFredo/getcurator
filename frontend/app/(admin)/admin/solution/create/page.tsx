"use client";

import Link from "next/link";

import SolutionForm from "@/components/admin/solution/SolutionForm";

/* ========================================================= */

export default function CreateSolutionPage() {

  return (

    <div className="space-y-10">

      <div className="flex items-center justify-between">

        <div>

          <h1 className="text-3xl font-semibold text-ratecard-blue">
            Create solution
          </h1>

          <p className="text-gray-500 mt-1">
            Create a new solution and enrich it with editorial content.
          </p>

        </div>

        <Link
          href="/admin/solution"
          className="underline"
        >
          ← Back
        </Link>

      </div>

      <SolutionForm
        mode="create"
      />

    </div>

  );

}
