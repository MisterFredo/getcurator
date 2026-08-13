// components/admin/topic/TopicKnowledge.tsx

"use client";

import HtmlEditor from "@/components/admin/HtmlEditor";


/* =========================================================
   TYPES
========================================================= */

type Props = {

  description: string;

  setDescription: (
    value: string,
  ) => void;

};


/* =========================================================
   COMPONENT
========================================================= */

export default function TopicKnowledge({

  description,
  setDescription,

}: Props) {

  return (

    <div className="space-y-8">

      {/* ===================================================
          DESCRIPTION
      =================================================== */}

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

          value={
            description
          }

          onChange={
            setDescription
          }

        />

      </section>

    </div>

  );

}
