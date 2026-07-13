// components/admin/solution/SolutionKnowledge.tsx

"use client";

import HtmlEditor from "@/components/admin/HtmlEditor";

/* ========================================================= */

type Props = {

  description: string;

  setDescription: (
    value: string,
  ) => void;

  content: string;

  setContent: (
    value: string,
  ) => void;

};

/* ========================================================= */

export default function SolutionKnowledge({

  description,
  setDescription,

  content,
  setContent,

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
            Short summary describing the solution.
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
      {/* EDITORIAL CONTENT */}
      {/* =================================================== */}

      <section className="space-y-6">

        <div>

          <h2 className="text-lg font-semibold">
            Editorial content
          </h2>

          <p className="text-sm text-gray-500">
            Reference content describing the solution in detail.
          </p>

        </div>

        <HtmlEditor
          value={content}
          onChange={setContent}
        />

      </section>

    </div>

  );

}
