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

  return (

    <section
      className="
        rounded-2xl
        border
        border-gray-200
        bg-white
        px-5
        py-4
        shadow-sm
      "
    >

      <div
        className="
          flex
          items-center
          gap-2
          overflow-x-auto
        "
      >

        {interlocutors.map(
          interlocutor => {

            const isSelected =
              interlocutor.id ===
              selectedId;

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
                    {interlocutor.displayName}
                  </span>

                </span>

              </button>

            );

          },
        )}

      </div>

    </section>

  );

}
