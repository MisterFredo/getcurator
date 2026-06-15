"use client";

import { useEffect, useState } from "react";

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

        const res = await api.get(
          `/user/profile/${userId}`
        );

        const profile: UserProfile =
          res?.profile || {};

        setGeography1(
          profile.geography_1 || ""
        );

        setGeography2(
          profile.geography_2 || ""
        );

        setGeography3(
          profile.geography_3 || ""
        );

      } catch (e) {

        console.error(
          "❌ geography load",
          e
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

      const current =
        await api.get(
          `/user/profile/${userId}`
        );

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

          profile_text:
            current?.profile
              ?.profile_text || null,
        }
      );

      alert(
        "Préférences géographiques enregistrées"
      );

    } catch (e) {

      console.error(
        "❌ geography save",
        e
      );

      alert(
        "Erreur sauvegarde"
      );

    } finally {

      setSaving(false);

    }
  }

  /* =====================================================
     UI
  ===================================================== */

  if (loading) {

    return (

      <div className="
        border
        rounded-lg
        p-6
      ">
        Chargement...
      </div>

    );
  }

  return (

    <div className="
      border
      rounded-lg
      p-6
      space-y-4
    ">

      <div>

        <h2 className="
          text-lg
          font-semibold
        ">
          Géographies
        </h2>

        <p className="
          text-sm
          text-gray-500
          mt-1
        ">
          Priorités géographiques
          utilisées pour le ciblage
          des contenus.
        </p>

      </div>

      {/* PRIORITY 1 */}

      <div className="
        space-y-1
      ">

        <label className="
          text-sm
          text-gray-500
        ">
          Priorité 1
        </label>

        <input
          value={geography1}
          onChange={(e) =>
            setGeography1(
              e.target.value
            )
          }
          placeholder="
            USA
          "
          className="
            border
            p-2
            rounded
            w-full
          "
        />

      </div>

      {/* PRIORITY 2 */}

      <div className="
        space-y-1
      ">

        <label className="
          text-sm
          text-gray-500
        ">
          Priorité 2
        </label>

        <input
          value={geography2}
          onChange={(e) =>
            setGeography2(
              e.target.value
            )
          }
          placeholder="
            China
          "
          className="
            border
            p-2
            rounded
            w-full
          "
        />

      </div>

      {/* PRIORITY 3 */}

      <div className="
        space-y-1
      ">

        <label className="
          text-sm
          text-gray-500
        ">
          Priorité 3
        </label>

        <input
          value={geography3}
          onChange={(e) =>
            setGeography3(
              e.target.value
            )
          }
          placeholder="
            Australia
          "
          className="
            border
            p-2
            rounded
            w-full
          "
        />

      </div>

      {/* SAVE */}

      <button
        onClick={save}
        disabled={saving}
        className="
          bg-ratecard-blue
          text-white
          px-4
          py-2
          rounded
        "
      >

        {saving
          ? "Sauvegarde..."
          : "Enregistrer"}

      </button>

    </div>
  );
}
