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

        Chiffres clés

      </div>

      <div
        className="
          space-y-3
        "
      >

        {chiffres.map(

          (value, index) => (

            <div

              key={index}

              className="
                flex
                items-start
                gap-3
              "

            >

              <div
                className="
                  mt-2
                  h-2
                  w-2
                  rounded-full
                  bg-black
                  shrink-0
                "
              />

              <div
                className="
                  text-[15px]
                  leading-7
                  text-gray-800
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
