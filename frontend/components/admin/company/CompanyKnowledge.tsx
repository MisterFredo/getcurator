// components/admin/company/CompanyKnowledge.tsx

"use client";

import {
  useState,
} from "react";

import { api } from "@/lib/api";

import {
  CompanyFormData,
} from "@/types/company";

/* ========================================================= */

type Props = {

  company: CompanyFormData;

  setCompany: React.Dispatch<
    React.SetStateAction<CompanyFormData>
  >;

};

/* ========================================================= */

export default function CompanyKnowledge({

  company,

  setCompany,

}: Props) {

  const [
    generating,
    setGenerating,
  ] = useState(false);

  /* =======================================================
     GENERATE DESCRIPTION
  ======================================================= */

  async function handleGenerateDescription() {

    const name =
      company.name.trim();

    if (!name) {

      alert(
        "Enter the company name first."
      );

      return;

    }

    try {

      setGenerating(true);

      const res =
        await api.post(
          "/company/generate-description",
          {
            name,
          },
        );

      const description =
        res.description ?? "";

      if (!description) {

        alert(
          "No description was generated."
        );

        return;

      }

      setCompany((prev) => ({

        ...prev,

        description,

      }));

    } catch (e) {

      console.error(e);

      alert(
        "Unable to generate company description."
      );

    } finally {

      setGenerating(false);

    }

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <section className="space-y-6">

      {/* =================================================== */}
      {/* HEADER */}
      {/* =================================================== */}

      <div className="flex items-start justify-between gap-6">

        <div>

          <h2 className="text-lg font-semibold">
            Description
          </h2>

          <p className="text-sm text-gray-500">
            Corporate identity and reference information about the company.
          </p>

        </div>

        <button
          type="button"
          onClick={handleGenerateDescription}
          disabled={
            generating ||
            !company.name.trim()
          }
          className="
            shrink-0
            rounded
            bg-ratecard-blue
            px-4
            py-2
            text-sm
            text-white
            disabled:opacity-50
          "
        >

          {
            generating
              ? "Generating..."
              : company.description.trim()
                ? "Regenerate"
                : "Generate"
          }

        </button>

      </div>

      {/* =================================================== */}
      {/* DESCRIPTION */}
      {/* =================================================== */}

      <textarea
        rows={7}
        value={company.description}
        onChange={(e) =>
          setCompany((prev) => ({

            ...prev,

            description:
              e.target.value,

          }))
        }
        className="w-full border rounded px-3 py-2"
        placeholder="Corporate description..."
      />

    </section>

  );

}
