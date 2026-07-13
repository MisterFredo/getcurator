// components/admin/topic/TopicIdentity.tsx

"use client";

import { Universe } from "@/types/topic";

/* ========================================================= */

type Props = {
  label: string;
  setLabel: (value: string) => void;

  universes: Universe[];

  selectedUniverses: string[];
  setSelectedUniverses: (values: string[]) => void;
};

/* ========================================================= */

export default function TopicIdentity({

  label,
  setLabel,

  universes,

  selectedUniverses,
  setSelectedUniverses,

}: Props) {

  function toggleUniverse(
    id: string,
  ) {

    if (
      selectedUniverses.includes(id)
    ) {

      setSelectedUniverses(
        selectedUniverses.filter(
          (u) => u !== id
        )
      );

      return;

    }

    setSelectedUniverses([
      ...selectedUniverses,
      id,
    ]);

  }

  return (

    <div className="space-y-8">

      {/* ===================================================== */}
      {/* IDENTITY */}
      {/* ===================================================== */}

      <section className="space-y-6">

        <div>

          <h2 className="text-lg font-semibold">
            Identity
          </h2>

          <p className="text-sm text-gray-500">
            Main information describing the topic.
          </p>

        </div>

        <div className="space-y-2">

          <label className="text-sm font-medium">
            Label
          </label>

          <input
            value={label}
            onChange={(e) =>
              setLabel(
                e.target.value
              )
            }
            className="w-full border rounded px-3 py-2"
            placeholder="Topic label"
          />

        </div>

      </section>

      {/* ===================================================== */}
      {/* CLASSIFICATION */}
      {/* ===================================================== */}

      <section className="space-y-6">

        <div>

          <h2 className="text-lg font-semibold">
            Classification
          </h2>

          <p className="text-sm text-gray-500">
            Select the universes associated with this topic.
          </p>

        </div>

        <div className="flex flex-wrap gap-2">

          {universes.map((u) => {

            const selected =
              selectedUniverses.includes(
                u.id_universe
              );

            return (

              <button
                key={u.id_universe}
                type="button"
                onClick={() =>
                  toggleUniverse(
                    u.id_universe
                  )
                }
                className={`
                  px-3
                  py-1
                  rounded
                  border
                  transition
                  ${
                    selected
                      ? "bg-ratecard-blue text-white border-ratecard-blue"
                      : "bg-white hover:bg-gray-50"
                  }
                `}
              >
                {u.label}
              </button>

            );

          })}

        </div>

      </section>

    </div>

  );

}
