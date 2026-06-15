"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

/* ========================================================= */

type PreferenceItem = {
  id: string;
  label: string;
};

type Preferences = {
  COMPANY: PreferenceItem[];
  SOLUTION: PreferenceItem[];
  TOPIC: PreferenceItem[];
};

type Props = {
  userId: string;
};

/* ========================================================= */

function PreferenceSection({
  title,
  items,
}: {
  title: string;
  items: PreferenceItem[];
}) {

  return (
    <div className="space-y-2">

      <div className="text-sm font-medium text-gray-700">
        {title}
      </div>

      {items.length === 0 ? (

        <div className="text-sm text-gray-400">
          Aucun
        </div>

      ) : (

        <div className="flex flex-wrap gap-2">

          {items.map((item) => (

            <span
              key={item.id}
              className="
                px-3
                py-1
                rounded-full
                bg-gray-100
                text-sm
              "
            >
              {item.label}
            </span>

          ))}

        </div>

      )}

    </div>
  );
}

/* ========================================================= */

export default function UserPreferencesViewer({
  userId,
}: Props) {

  const [loading, setLoading] =
    useState(true);

  const [preferences, setPreferences] =
    useState<Preferences>({
      COMPANY: [],
      SOLUTION: [],
      TOPIC: [],
    });

  /* =====================================================
     LOAD
  ===================================================== */

  useEffect(() => {

    async function load() {

      try {

        setLoading(true);

        const res = await api.get(
          `/user/preferences/${userId}`
        );

        setPreferences(
          res?.preferences || {
            COMPANY: [],
            SOLUTION: [],
            TOPIC: [],
          }
        );

      } catch (e) {

        console.error(
          "❌ preferences load",
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
      space-y-6
    ">

      <div>

        <h2 className="
          text-lg
          font-semibold
        ">
          Favoris
        </h2>

        <p className="
          text-sm
          text-gray-500
          mt-1
        ">
          Préférences actuellement
          configurées par l'utilisateur.
        </p>

      </div>

      <PreferenceSection
        title={`Topics (${preferences.TOPIC.length})`}
        items={preferences.TOPIC}
      />

      <PreferenceSection
        title={`Companies (${preferences.COMPANY.length})`}
        items={preferences.COMPANY}
      />

      <PreferenceSection
        title={`Solutions (${preferences.SOLUTION.length})`}
        items={preferences.SOLUTION}
      />

    </div>
  );
}
