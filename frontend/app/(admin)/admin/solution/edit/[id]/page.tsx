"use client";

import { useParams } from "next/navigation";

import Link from "next/link";

import SolutionForm from "@/components/admin/solution/SolutionForm";

/* ========================================================= */

export default function EditSolutionPage() {

  const params =
    useParams();

  const solutionId =
    params.id as string;

  return (

    <div className="space-y-10">

      <div className="flex items-center justify-between">

        <div>

          <h1 className="text-3xl font-semibold text-ratecard-blue">
            Edit solution
          </h1>

          <p className="text-gray-500 mt-1">
            Update the information associated with this solution.
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

        mode="edit"

        solutionId={solutionId}

      />

    </div>

  );

}
