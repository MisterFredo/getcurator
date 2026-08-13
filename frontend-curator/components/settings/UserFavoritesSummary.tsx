"use client";

import {
  useEffect,
  useState,
} from "react";

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
  companies: Entity[];
  solutions: Entity[];
  topics: Entity[];
};

/* ========================================================= */

const EMPTY_PREFERENCES: Preferences = {
  companies: [],
  solutions: [],
  topics: [],
};

/* =========================================================
   ENTITY CARD
========================================================= */

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

/* =========================================================
   COMPONENT
========================================================= */

export default function UserFavoritesSummary() {

  const [loading, setLoading] =
    useState(true);

  const [
    preferences,
    setPreferences,
  ] = useState<Preferences>(
    EMPTY_PREFERENCES,
  );

  /* =====================================================
     LOAD
  ===================================================== */

  useEffect(() => {

    async function load() {

      try {

        const userId =
          localStorage.getItem(
            "user_id",
          );

        if (!userId) {

          setPreferences(
            EMPTY_PREFERENCES,
          );

          return;

        }

        const res =
          await api.get(
            `/user/preferences/${userId}`,
          );

        const raw =
          res?.preferences ?? {};

        setPreferences({
          companies:
            Array.isArray(
              raw.companies,
            )
              ? raw.companies
              : [],

          solutions:
            Array.isArray(
              raw.solutions,
            )
              ? raw.solutions
              : [],

          topics:
            Array.isArray(
              raw.topics,
            )
              ? raw.topics
              : [],
        });

      } catch (e) {

        console.error(
          "favorites load error",
          e,
        );

        setPreferences(
          EMPTY_PREFERENCES,
        );

      } finally {

        setLoading(false);

      }

    }

    load();

  }, []);

  /* =====================================================
     LOADING
  ===================================================== */

  if (loading) {
    return null;
  }

  /* =====================================================
     TOTAL
  ===================================================== */

  const total =
    preferences.companies.length +
    preferences.solutions.length +
    preferences.topics.length;

  if (total === 0) {
    return null;
  }

  const MAX_PREFERENCES = 10;

  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <div className="space-y-6">

      <div
        className="
          flex
          items-center
          justify-between
        "
      >
        <div>
          <h2
            className="
              text-base
              font-semibold
            "
          >
            Your favorites
          </h2>
      
          <p
            className="
              text-sm
              text-gray-500
              mt-1
            "
          >
            These favorites personalize your
            GetCurator experience.
          </p>
        </div>
      
        <div
          className={`
            text-sm
            font-medium
      
            ${
              total >= MAX_PREFERENCES
                ? "text-amber-600"
                : "text-gray-500"
            }
          `}
        >
          {total} / {MAX_PREFERENCES}
        </div>
      </div>

      {/* =====================================================
          COMPANIES
      ===================================================== */}

      {preferences.companies.length > 0 && (

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

            {preferences.companies.map(
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

      {preferences.solutions.length > 0 && (

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

            {preferences.solutions.map(
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

      {preferences.topics.length > 0 && (

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

            {preferences.topics.map(
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
