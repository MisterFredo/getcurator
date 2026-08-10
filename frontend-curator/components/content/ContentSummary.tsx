"use client";

/* ========================================================= */

type Props = {

  excerpt?: string | null;

};

/* ========================================================= */

export default function ContentSummary({

  excerpt,

}: Props) {

  if (!excerpt) {

    return null;

  }

  return (

    <section
      className="
        rounded-xl
        border
        border-gray-200
        bg-gray-50
        p-6
      "
    >

      <div
        className="
          text-xs
          font-semibold
          uppercase
          tracking-wide
          text-gray-500
          mb-3
        "
      >

        Executive Summary

      </div>

      <p
        className="
          text-[16px]
          leading-8
          text-gray-800
        "
      >

        {excerpt}

      </p>

    </section>

  );

}
