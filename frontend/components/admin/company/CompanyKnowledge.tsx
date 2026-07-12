// components/admin/company/CompanyKnowledge.tsx

"use client";

import HtmlEditor from "@/components/admin/HtmlEditor";

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

  return (

    <section className="space-y-8">

      {/* =================================================== */}
      {/* DESCRIPTION */}
      {/* =================================================== */}

      <div className="space-y-6">

        <div>

          <h2 className="text-lg font-semibold">
            Description
          </h2>

          <p className="text-sm text-gray-500">
            Short editorial summary describing the company.
          </p>

        </div>

        <textarea
          rows={4}
          value={company.description}
          onChange={(e) =>
            setCompany((prev) => ({

              ...prev,

              description:
                e.target.value,

            }))
          }
          className="w-full border rounded px-3 py-2"
          placeholder="Short editorial description..."
        />

      </div>

      {/* =================================================== */}
      {/* KNOWLEDGE */}
      {/* =================================================== */}

      <div className="space-y-6">

        <div>

          <h2 className="text-lg font-semibold">
            Knowledge
          </h2>

          <p className="text-sm text-gray-500">
            Long-form reference content describing the company.
          </p>

        </div>

        <HtmlEditor
          value={company.wiki_content}
          onChange={(value) =>
            setCompany((prev) => ({

              ...prev,

              wiki_content: value,

            }))
          }
        />

      </div>

    </section>

  );

}
