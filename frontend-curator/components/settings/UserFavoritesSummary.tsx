"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

/* ========================================================= */

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL || "";

/* ========================================================= */

type Entity = {
  id: string;
  label: string;
  logo?: string | null;
};

type Preferences = {
  COMPANY: Entity[];
  SOLUTION: Entity[];
  TOPIC: Entity[];
};

/* ========================================================= */

function EntityCard({
  item,
}: {
  item: Entity;
}) {

  const logoUrl =
    item.logo
      ? `${GCS_BASE_URL}/companies/${item.logo}`
      : null;

  return (

    <div
      className="
        bg-white
        border
        rounded-xl
        overflow-hidden
        text-center
      "
    >

      <div
        className="
          h-20
          flex
          items-center
          justify-center
          bg-gray-50
        "
      >

        {logoUrl ? (

          <img
            src={logoUrl}
            alt={item.label}
            className="
              max-h-12
              max-w-[80%]
              object-contain
            "
          />

        ) : (

          <div
            className="
              text-xs
              text-gray-400
              px-2
            "
          >
            {item.label}
          </div>

        )}

      </div>

      <div
        className="
          p-2
          text-xs
          font-medium
          text-gray-700
          line-clamp-2
        "
      >
        {item.label}
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
          "favorites load error",
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

    <div className="space-y-6">

      {/* =====================================================
          COMPANIES
      ===================================================== */}

      {preferences.COMPANY.length > 0 && (

        <div>

          <h3
            className="
              text-sm
              font-medium
              mb-3
            "
          >
            Favorite Companies
          </h3>

          <div
            className="
              grid
              grid-cols-2
              sm:grid-cols-3
              md:grid-cols-4
              gap-3
            "
          >

            {preferences.COMPANY.map(
              (item) => (
                <EntityCard
                  key={item.id}
                  item={item}
                />
              )
            )}

          </div>

        </div>

      )}

      {/* =====================================================
          SOLUTIONS
      ===================================================== */}

      {preferences.SOLUTION.length > 0 && (

        <div>

          <h3
            className="
              text-sm
              font-medium
              mb-3
            "
          >
            Favorite Solutions
          </h3>

          <div
            className="
              grid
              grid-cols-2
              sm:grid-cols-3
              md:grid-cols-4
              gap-3
            "
          >

            {preferences.SOLUTION.map(
              (item) => (
                <EntityCard
                  key={item.id}
                  item={item}
                />
              )
            )}

          </div>

        </div>

      )}

      {/* =====================================================
          TOPICS
      ===================================================== */}

      {preferences.TOPIC.length > 0 && (

        <div>

          <h3
            className="
              text-sm
              font-medium
              mb-3
            "
          >
            Favorite Topics
          </h3>

          <div
            className="
              flex
              flex-wrap
              gap-2
            "
          >

            {preferences.TOPIC.map(
              (item) => (

                <div
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
                </div>

              )
            )}

          </div>

        </div>

      )}

    </div>

  );
}
