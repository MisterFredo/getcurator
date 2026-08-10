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
        rounded-xl
        border
        border-gray-200
        bg-white
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
          mb-4
        "
      >

        Article

      </div>

      <div
        className="
          whitespace-pre-wrap
          text-[16px]
          leading-8
          text-gray-800
        "
      >

        {content}

      </div>

    </section>

  );

}
