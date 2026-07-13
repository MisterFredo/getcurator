// components/admin/topic/TopicKnowledge.tsx

"use client";

import HtmlEditor from "@/components/admin/HtmlEditor";

/* ========================================================= */

type Props = {
  description: string;
  setDescription: (value: string) => void;

  seoTitle: string;
  setSeoTitle: (value: string) => void;

  seoDescription: string;
  setSeoDescription: (value: string) => void;
};

/* ========================================================= */

export default function TopicKnowledge({

  description,
  setDescription,

  seoTitle,
  setSeoTitle,

  seoDescription,
  setSeoDescription,

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
            Editorial description of the topic.
          </p>

        </div>

        <HtmlEditor
          value={description}
          onChange={setDescription}
        />

      </section>

      {/* =================================================== */}
      {/* SEO */}
      {/* =================================================== */}

      <section className="space-y-6">

        <div>

          <h2 className="text-lg font-semibold">
            SEO
          </h2>

          <p className="text-sm text-gray-500">
            Metadata used for search engines.
          </p>

        </div>

        <div className="space-y-2">

          <label className="text-sm font-medium">
            SEO title
          </label>

          <input
            value={seoTitle}
            onChange={(e) =>
              setSeoTitle(
                e.target.value
              )
            }
            className="w-full border rounded px-3 py-2"
            placeholder="SEO title"
          />

        </div>

        <div className="space-y-2">

          <label className="text-sm font-medium">
            SEO description
          </label>

          <textarea
            value={seoDescription}
            onChange={(e) =>
              setSeoDescription(
                e.target.value
              )
            }
            rows={4}
            className="w-full border rounded px-3 py-2"
            placeholder="SEO description"
          />

        </div>

      </section>

    </div>

  );

}
