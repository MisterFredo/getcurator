"use client";

import {
  useEffect,
  useState,
} from "react";

import CardSection from "@/components/ui/CardSection";
import { api } from "@/lib/api";

/* ========================================================= */

type Props = {
  userId: string;
};

type Universe = {
  id_universe: string;
  label: string;
};

/* ========================================================= */

export default function ProfileUniversesEditor({
  userId,
}: Props) {

  const [
    universes,
    setUniverses,
  ] = useState<Universe[]>([]);

  const [
    selectedIds,
    setSelectedIds,
  ] = useState<string[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    saving,
    setSaving,
  ] = useState(false);

  /* =====================================================
     LOAD
  ===================================================== */

  useEffect(() => {

    async function load() {

      try {

        setLoading(true);

        const [
          universesRes,
          userRes,
        ] = await Promise.all([

          api.get(
            "/universe/list",
          ),

          api.get(
            `/user/${userId}`,
          ),

        ]);

        const universeList =
          universesRes?.universes ?? [];

        setUniverses(
          Array.isArray(
            universeList,
          )
            ? universeList
            : [],
        );

        const userUniverses =
          userRes?.universes ?? [];

        const normalizedUniverseIds =
          Array.isArray(
            userUniverses,
          )
            ? userUniverses
                .map(
                  (
                    item: any,
                  ) => {

                    if (
                      typeof item ===
                      "string"
                    ) {

                      return item;

                    }

                    return (
                      item?.id_universe
                      ?? item?.ID_UNIVERSE
                      ?? item?.id
                      ?? null
                    );

                  },
                )
                .filter(
                  (
                    id: string | null,
                  ): id is string =>
                    typeof id ===
                      "string"
                    && id.length > 0,
                )
            : [];

        setSelectedIds(
          normalizedUniverseIds,
        );

      } catch (error) {

        console.error(
          "Failed to load universes",
          error,
        );

      } finally {

        setLoading(false);

      }

    }

    if (userId) {

      load();

    }

  }, [
    userId,
  ]);

  /* =====================================================
     TOGGLE
  ===================================================== */

  function toggleUniverse(
    universeId: string,
  ) {

    setSelectedIds(
      (previous) =>

        previous.includes(
          universeId,
        )

          ? previous.filter(
              (id) =>
                id !== universeId,
            )

          : [
              ...previous,
              universeId,
            ],
    );

  }

  /* =====================================================
     SAVE
  ===================================================== */

  async function saveUniverses() {

    try {

      setSaving(true);

      const validUniverseIds =
        selectedIds.filter(
          (id) =>
            typeof id === "string"
            && id.length > 0,
        );

      await api.post(
        "/user/assign-universes",
        {
          user_id:
            userId,

          universes:
            validUniverseIds,
        },
      );

    } catch (error) {

      console.error(
        "Failed to save universes",
        error,
      );

      alert(
        "Unable to save universes.",
      );

    } finally {

      setSaving(false);

    }

  }

  /* =====================================================
     UI
  ===================================================== */

  return (

    <CardSection
      title="Universes"
      description="Universes available to this profile."
    >

      {loading ? (

        <div className="
          text-sm
          text-gray-500
        ">
          Loading...
        </div>

      ) : (

        <div className="
          space-y-5
        ">

          <div className="
            grid
            grid-cols-1
            md:grid-cols-2
            lg:grid-cols-3
            gap-3
          ">

            {universes.map(
              (universe) => {

                const selected =
                  selectedIds.includes(
                    universe.id_universe,
                  );

                return (

                  <button

                    key={
                      universe.id_universe
                    }

                    type="button"

                    onClick={() =>
                      toggleUniverse(
                        universe.id_universe,
                      )
                    }

                    className={`
                      text-left
                      rounded-lg
                      border
                      px-4
                      py-3
                      text-sm
                      transition

                      ${
                        selected
                          ? "border-ratecard-blue bg-blue-50 text-ratecard-blue"
                          : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
                      }
                    `}

                  >

                    {universe.label}

                  </button>

                );

              },
            )}

          </div>

          <div className="
            flex
            justify-end
          ">

            <button

              type="button"

              onClick={
                saveUniverses
              }

              disabled={
                saving
              }

              className="
                rounded-lg
                bg-ratecard-blue
                px-5
                py-2
                text-white
                transition
                hover:opacity-90
                disabled:opacity-50
              "

            >

              {
                saving
                  ? "Saving..."
                  : "Save universes"
              }

            </button>

          </div>

        </div>

      )}

    </CardSection>

  );

}
