"use client";

import { useEffect, useState } from "react";

import CardSection from "@/components/ui/CardSection";
import { api } from "@/lib/api";

/* ========================================================= */

type Props = {
  userId: string;
};

type UserProfile = {
  geography_1?: string | null;
  geography_2?: string |null;
  geography_3?: string | null;
};

/* ========================================================= */

export default function UserGeographyEditor({
  userId,
}: Props) {

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [
    geography1,
    setGeography1,
  ] = useState("");

  const [
    geography2,
    setGeography2,
  ] = useState("");

  const [
    geography3,
    setGeography3,
  ] = useState("");

  /* =====================================================
     LOAD
  ===================================================== */

  useEffect(() => {

    async function load() {

      try {

        setLoading(true);

        const res =
          await api.get(
            `/user/profile/${userId}`,
          );

        const profile: UserProfile =
          res?.profile ?? {};

        setGeography1(
          profile.geography_1 ?? "",
        );

        setGeography2(
          profile.geography_2 ?? "",
        );

        setGeography3(
          profile.geography_3 ?? "",
        );

      } catch (error) {

        console.error(
          "Failed to load geographies",
          error,
        );

      } finally {

        setLoading(false);

      }

    }

    if (userId) {
      load();
    }

  }, [userId]);

  /* =====================================================
     SAVE
  ===================================================== */

  async function save() {

    try {

      setSaving(true);

      await api.post(
        "/user/profile/update",
        {
          user_id: userId,

          geography_1:
            geography1 || null,

          geography_2:
            geography2 || null,

          geography_3:
            geography3 || null,
        },
      );

      alert(
        "Geographies updated.",
      );

    } catch (error) {

      console.error(
        "Failed to save geographies",
        error,
      );

      alert(
        "Unable to save changes.",
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
      title="Geographies"
      description="Prioritize markets to improve content selection and future Digests."
    >

      {loading ? (

        <div className="text-sm text-gray-500">
          Loading...
        </div>

      ) : (

        <div className="space-y-6">

          <div className="grid gap-4">

            <div className="space-y-2">

              <label className="text-sm font-medium">
                Priority 1
              </label>

              <input
                value={geography1}
                onChange={(e) =>
                  setGeography1(
                    e.target.value,
                  )
                }
                placeholder="United States"
                className="
                  w-full
                  rounded-lg
                  border
                  px-3
                  py-2
                "
              />

            </div>

            <div className="space-y-2">

              <label className="text-sm font-medium">
                Priority 2
              </label>

              <input
                value={geography2}
                onChange={(e) =>
                  setGeography2(
                    e.target.value,
                  )
                }
                placeholder="China"
                className="
                  w-full
                  rounded-lg
                  border
                  px-3
                  py-2
                "
              />

            </div>

            <div className="space-y-2">

              <label className="text-sm font-medium">
                Priority 3
              </label>

              <input
                value={geography3}
                onChange={(e) =>
                  setGeography3(
                    e.target.value,
                  )
                }
                placeholder="Australia"
                className="
                  w-full
                  rounded-lg
                  border
                  px-3
                  py-2
                "
              />

            </div>

          </div>

          <div className="flex justify-end">

            <button
              onClick={save}
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

              {saving
                ? "Saving..."
                : "Save"}

            </button>

          </div>

        </div>

      )}

    </CardSection>

  );

}
