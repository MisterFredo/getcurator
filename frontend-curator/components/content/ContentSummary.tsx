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
        pt-2
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

        Executive Summary

      </h2>

      <p
        className="
          text-[20px]
          leading-10
          text-gray-900
          font-light
        "
      >

        {excerpt}

      </p>

    </section>

  );

}
