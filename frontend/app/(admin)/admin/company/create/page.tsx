"use client";

import Link from "next/link";

import CompanyForm from "@/components/admin/company/CompanyForm";

/* ========================================================= */

export default function CreateCompanyPage() {

  return (

    <div className="space-y-10">

      <div className="flex justify-between items-center">

        <h1 className="text-2xl font-semibold">
          Create company
        </h1>

        <Link
          href="/admin/company"
          className="underline"
        >
          ← Back
        </Link>

      </div>

      <CompanyForm
        mode="create"
      />

    </div>

  );

}
