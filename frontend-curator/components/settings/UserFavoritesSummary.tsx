"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

/* ========================================================= */

type FavoriteItem = {
  id: string;
  label: string;
};

type Preferences = {
  COMPANY: FavoriteItem[];
  SOLUTION: FavoriteItem[];
  TOPIC: FavoriteItem[];
};

/* ========================================================= */

function Section({
  title,
  items,
}: {
  title: string;
  items: FavoriteItem[];
}) {
  if (!items.length) return null;

  return (
    <div className="space-y-2">

      <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">
        {title}
      </div>

      <div className="flex flex-wrap gap-2">

        {items.map((item) => (
          <div
            key={item.id}
            className="
              px-3
              py-1.5
              rounded-full
              bg-gray-100
              text-sm
              text-gray-700
            "
          >
            {item.label}
          </div>
        ))}

      </div>

    </div>
  );
}

/* ========================================================= */

export default function UserFavoritesSummary() {

  const [loading, setLoading] =
    useState(true);

  const [preferences, setPreferences] =
    useState<Preferences>({
      COMPANY: [],
      SOLUTION: [],
      TOPIC: [],
    });

  useEffect(() => {

    async function load() {

      try {

        const userId =
          localStorage.getItem(
            "user_id"
          );

        if (!userId) return;

        const res =
          await api.get(
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
          "favorites summary error",
          e
        );

      } finally {

        setLoading(false);

      }
    }

    load();

  }, []);

  if (loading) {
    return null;
  }

  const total =
    preferences.COMPANY.length +
    preferences.SOLUTION.length +
    preferences.TOPIC.length;

  if (total === 0) {
    return null;
  }

  return (

    <div className="
      bg-white
      border
      rounded-xl
      p-5
      space-y-5
    ">

      <div>

        <h2 className="
          text-sm
          font-semibold
          text-gray-900
        ">
          Favorites
        </h2>

        <p className="
          text-xs
          text-gray-500
          mt-1
        ">
          Content sources you follow
        </p>

      </div>

      <Section
        title="Companies"
        items={preferences.COMPANY}
      />

      <Section
        title="Solutions"
        items={preferences.SOLUTION}
      />

      <Section
        title="Topics"
        items={preferences.TOPIC}
      />

    </div>
  );
}
