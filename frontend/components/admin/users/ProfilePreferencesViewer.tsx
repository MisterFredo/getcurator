"use client";

import { useEffect, useState } from "react";

import CardSection from "@/components/ui/CardSection";
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

    <div className="space-y-3">

      <div className="flex items-center justify-between">

        <h3 className="font-medium">
          {title}
        </h3>

        <span className="text-sm text-gray-400">
          {items.length}
        </span>

      </div>

      {items.length === 0 ? (

        <div className="text-sm text-gray-400 italic">
          No preferences selected.
        </div>

      ) : (

        <div className="flex flex-wrap gap-2">

          {items.map((item) => (

            <span
              key={item.id}
              className="
                rounded-full
                bg-gray-100
                px-3
                py-1
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

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    preferences,
    setPreferences,
  ] = useState<Preferences>({
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

        const res =
          await api.get(
            `/user/preferences/${userId}`,
          );

        setPreferences(
          res?.preferences ?? {
            COMPANY: [],
            SOLUTION: [],
            TOPIC: [],
          },
        );

      } catch (error) {

        console.error(
          "Failed to load preferences",
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
     UI
  ===================================================== */

  return (

    <CardSection
      title="Preferences"
      description="Topics, Companies and Solutions followed by this profile."
    >

      {loading ? (

        <div className="text-sm text-gray-500">
          Loading...
        </div>

      ) : (

        <div className="space-y-8">

          <PreferenceSection
            title="Topics"
            items={preferences.TOPIC}
          />

          <PreferenceSection
            title="Companies"
            items={preferences.COMPANY}
          />

          <PreferenceSection
            title="Solutions"
            items={preferences.SOLUTION}
          />

        </div>

      )}

    </CardSection>

  );

}
