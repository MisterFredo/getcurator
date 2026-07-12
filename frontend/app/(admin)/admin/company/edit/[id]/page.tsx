"use client";

import Link from "next/link";

import { useParams } from "next/navigation";

import CompanyForm from "@/components/admin/company/CompanyForm";

/* ========================================================= */

export default function EditCompanyPage() {

  const params =
    useParams();

  return (

    <div className="space-y-10">

      <div className="flex justify-between items-center">

        <h1 className="text-2xl font-semibold">
          Edit company
        </h1>

        <Link
          href="/admin/company"
          className="underline"
        >
          ← Back
        </Link>

      </div>

      <CompanyForm
        mode="edit"
        companyId={
          params.id as string
        }
      />

    </div>

  );

}
