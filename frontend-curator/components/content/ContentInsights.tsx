// frontend-curator/components/content/ContentInsights.tsx

"use client";

/* ========================================================= */

type Props = {

  signal?: string;

  mecanique?: string;

  enjeu?: string;

  friction?: string;

};

/* ========================================================= */

type InsightBlockProps = {

  title: string;

  content?: string;

};

/* ========================================================= */

function InsightBlock({

  title,

  content,

}: InsightBlockProps) {

  if (!content) {

    return null;

  }

  return (

    <section
      className="
        rounded-xl
        border
        border-gray-200
        bg-white
        p-6
      "
    >

      <h2
        className="
          text-sm
          font-semibold
          uppercase
          tracking-wide
          text-gray-500
          mb-4
        "
      >

        {title}

      </h2>

      <div
        className="
          whitespace-pre-wrap
          text-[15px]
          leading-8
          text-gray-800
        "
      >

        {content}

      </div>

    </section>

  );

}

/* ========================================================= */

export default function ContentInsights({

  signal,

  mecanique,

  enjeu,

  friction,

}: Props) {

  return (

    <div className="space-y-6">

      <InsightBlock

        title="Signal analytique"

        content={signal}

      />

      <InsightBlock

        title="Mécanique expliquée"

        content={mecanique}

      />

      <InsightBlock

        title="Enjeu stratégique"

        content={enjeu}

      />

      <InsightBlock

        title="Point de friction"

        content={friction}

      />

    </div>

  );

}
