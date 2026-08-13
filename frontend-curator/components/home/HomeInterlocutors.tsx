"use client";

/* =========================================================
   TYPES
========================================================= */

export type HomeInterlocutor = {
  id: string;
  displayName: string;
  company?: string | null;
  description?: string | null;
  type: "self" | "expert";
};

type Props = {
  interlocutors: HomeInterlocutor[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

/* =========================================================
   COMPONENT
========================================================= */

export default function HomeInterlocutors({

  interlocutors,

  selectedId,

  onSelect,

}: Props) {

  if (interlocutors.length === 0) {

    return null;

  }

  const selected =
    interlocutors.find(
      interlocutor =>
        interlocutor.id === selectedId,
    ) ?? interlocutors[0];

  return (

    <section
      className="
        rounded-2xl
        border
        border-gray-200
        bg-white
        px-5
        py-5
        shadow-sm
      "
    >

      {/* =====================================================
          SELECTOR
      ===================================================== */}

      <div
        className="
          flex
          items-center
          gap-2
          overflow-x-auto
          pb-1
        "
      >

        {interlocutors.map(
          interlocutor => {

            const isSelected =
              interlocutor.id ===
              selected.id;

            return (

              <button

                key={
                  interlocutor.id
                }

                type="button"

                onClick={() =>
                  onSelect(
                    interlocutor.id,
                  )
                }

                className={`
                  shrink-0
                  rounded-full
                  border
                  px-4
                  py-2
                  text-sm
                  font-medium
                  transition

                  ${
                    isSelected

                      ? `
                        border-gray-900
                        bg-gray-900
                        text-white
                      `

                      : `
                        border-gray-200
                        bg-white
                        text-gray-600
                        hover:border-gray-300
                        hover:text-gray-900
                      `
                  }
                `}
              >

                <span
                  className="
                    flex
                    items-center
                    gap-2
                  "
                >

                  {interlocutor.type ===
                    "self" && (

                    <span
                      className="
                        text-[10px]
                        uppercase
                        tracking-wide
                        opacity-70
                      "
                    >
                      Me
                    </span>

                  )}

                  <span>
                    {
                      interlocutor
                        .displayName
                    }
                  </span>

                </span>

              </button>

            );

          },
        )}

      </div>

      {/* =====================================================
          ACTIVE PROFILE
      ===================================================== */}

      <div
        className="
          mt-5
          border-t
          border-gray-100
          pt-4
        "
      >

        <div
          className="
            flex
            items-start
            justify-between
            gap-6
          "
        >

          <div
            className="
              min-w-0
            "
          >

            <div
              className="
                text-lg
                font-semibold
                text-gray-900
              "
            >
              {selected.displayName}
            </div>

            {selected.company && (

              <div
                className="
                  mt-1
                  text-sm
                  text-gray-500
                "
              >
                {selected.company}
              </div>

            )}

            {selected.description && (

              <p
                className="
                  mt-2
                  max-w-3xl
                  text-sm
                  leading-6
                  text-gray-500
                "
              >
                {selected.description}
              </p>

            )}

          </div>

          <div
            className="
              shrink-0
              rounded-full
              bg-gray-100
              px-3
              py-1.5
              text-[11px]
              font-medium
              text-gray-500
            "
          >
            {
              selected.type === "self"
                ? "Augmented self"
                : "Expert"
            }
          </div>

        </div>

      </div>

    </section>

  );

}
