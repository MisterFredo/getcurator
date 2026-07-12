// components/admin/company/CompanyKnowledge.tsx

"use client";

import HtmlEditor from "@/components/admin/HtmlEditor";

/* ========================================================= */

type Props = {
  description: string;
  setDescription: (value: string) => void;

  wikiContent: string;
  setWikiContent: (value: string) => void;
};

/* ========================================================= */

export default function CompanyKnowledge({

  description,
  setDescription,

  wikiContent,
  setWikiContent,

}: Props) {

  return (

    <div className="space-y-8">

      {/* =================================================== */}
      {/* DESCRIPTION */}
      {/* =================================================== */}

      <section className="space-y-6">

        <div>

          <h2 className="text-lg font-semibold">
            Description
          </h2>

          <p className="text-sm text-gray-500">
            Short summary describing the company.
          </p>

        </div>

        <textarea
          value={description}
          onChange={(e) =>
            setDescription(
              e.target.value
            )
          }
          rows={4}
          className="w-full border rounded px-3 py-2"
          placeholder="Short editorial description..."
        />

      </section>

      {/* =================================================== */}
      {/* KNOWLEDGE */}
      {/* =================================================== */}

      <section className="space-y-6">

        <div>

          <h2 className="text-lg font-semibold">
            Knowledge
          </h2>

          <p className="text-sm text-gray-500">
            Reference content describing the company in detail.
          </p>

        </div>

        <HtmlEditor
          value={wikiContent}
          onChange={setWikiContent}
        />

      </section>

    </div>

  );

}
