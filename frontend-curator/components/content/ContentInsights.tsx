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
        pt-8
        border-t
        border-gray-200
      "
    >

      <h2
        className="
          text-xs
          uppercase
          tracking-wide
          font-semibold
          text-gray-500
          mb-5
        "
      >

        {title}

      </h2>

      <div
        className="
          whitespace-pre-wrap
          text-[17px]
          leading-9
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

    <div>

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
