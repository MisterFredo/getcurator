"use client";

/* ========================================================= */

type Props = {

  chiffres?: string[];

};

/* ========================================================= */

export default function ContentNumbers({

  chiffres,

}: Props) {

  if (
    !chiffres ||
    chiffres.length === 0
  ) {

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

        Chiffres clés

      </h2>

      <div
        className="
          rounded-xl
          border
          border-gray-200
          overflow-hidden
        "
      >

        {chiffres.map(

          (value, index) => (

            <div

              key={index}

              className={`
                px-5
                py-4

                ${
                  index !==
                  chiffres.length - 1
                    ? "border-b border-gray-100"
                    : ""
                }
              `}

            >

              <div
                className="
                  text-[16px]
                  leading-8
                  text-gray-900
                "
              >

                {value}

              </div>

            </div>

          ),

        )}

      </div>

    </section>

  );

}
