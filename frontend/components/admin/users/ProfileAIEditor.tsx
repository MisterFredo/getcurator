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
  geography_2?: string | null;
  geography_3?: string | null;
  profile_text?: string | null;
};

/* ========================================================= */

export default function UserProfileEditor({
  userId,
}: Props) {

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [
    profileText,
    setProfileText,
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

        setProfileText(
          profile.profile_text ?? "",
        );

      } catch (error) {

        console.error(
          "Failed to load profile",
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

          profile_text:
            profileText || null,
        },
      );

      alert(
        "Profile updated.",
      );

    } catch (error) {

      console.error(
        "Failed to save profile",
        error,
      );

      alert(
        "Unable to save profile.",
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
      title="Profile"
      description="Describe this profile to personalize analyses, Digests and future Expert interactions."
    >

      {loading ? (

        <div className="text-sm text-gray-500">
          Loading...
        </div>

      ) : (

        <div className="space-y-6">

          <textarea
            value={profileText}
            onChange={(e) =>
              setProfileText(
                e.target.value,
              )
            }
            rows={12}
            className="
              w-full
              rounded-lg
              border
              p-4
              text-sm
            "
            placeholder={`Example:

Global Digital Director

Priorities
- eB2B
- Retail Media
- Quick Commerce

Markets
- United States
- Europe

Competitors
- Diageo
- Pernod Ricard
- Brown-Forman

Strategic questions
- Premiumization
- 3-tier evolution
- AI in commerce
- Retail media monetization`}
          />

          <div className="flex justify-end">

            <button
              onClick={save}
              disabled={saving}
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
