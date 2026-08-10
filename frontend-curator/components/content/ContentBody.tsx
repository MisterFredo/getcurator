"use client";

/* ========================================================= */

type Props = {

  content?: string;

};

/* ========================================================= */

export default function ContentBody({

  content,

}: Props) {

  if (!content) {

    return null;

  }

  return (

    <section
      className="
        pt-2
      "
    >

      <div
        className="
          text-xs
          font-semibold
          uppercase
          tracking-wide
          text-gray-500
          mb-5
        "
      >

        Article

      </div>

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
