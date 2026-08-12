"use client";

import {
  useEffect,
  useState,
} from "react";

import { api } from "@/lib/api";

import EntityDrawer
  from "@/components/drawers/EntityDrawer";

import DrawerHeader
  from "@/components/drawers/DrawerHeader";

import {
  useDrawer,
} from "@/contexts/DrawerContext";

/* =========================================================
   TYPES
========================================================= */

type Entity = {
  id: string;
  label: string;
  logo?: string | null;
};

type ExpertProfile = {
  geography_1?: string | null;
  geography_2?: string | null;
  geography_3?: string | null;
  profile_text?: string | null;
};

type Expert = {
  ID_USER: string;
  NAME?: string | null;
  DISPLAY_NAME?: string | null;
  COMPANY?: string | null;
  DESCRIPTION?: string | null;
};

type Preferences = {
  companies: Entity[];
  solutions: Entity[];
  topics: Entity[];
};

/* ========================================================= */

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL || "";

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
        rounded-lg
        border
        bg-white
        overflow-hidden
        text-center
      "
    >

      <div
        className="
          h-16
          flex
          items-center
          justify-center
          bg-gray-50
          px-3
        "
      >

        {logoUrl ? (

          <img
            src={logoUrl}
            alt={item.label}
            className="
              max-h-10
              max-w-[80%]
              object-contain
            "
          />

        ) : (

          <div
            className="
              text-xs
              text-gray-400
            "
          >
            {item.label}
          </div>

        )}

      </div>

      <div
        className="
          px-2
          py-2
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

export default function ExpertDrawer({
  expertId,
}: {
  expertId: string;
}) {

  const {
    closeLeftDrawer,
  } = useDrawer();

  const [loading, setLoading] =
    useState(true);

  const [expert, setExpert] =
    useState<Expert | null>(
      null,
    );

  const [profile, setProfile] =
    useState<ExpertProfile | null>(
      null,
    );

  const [
    preferences,
    setPreferences,
  ] = useState<Preferences>({
    companies: [],
    solutions: [],
    topics: [],
  });

  const [
    isFavorite,
    setIsFavorite,
  ] = useState(false);

  /* =====================================================
     LOAD
  ===================================================== */

  useEffect(() => {

    async function load() {

      try {

        setLoading(true);

        const [
          userRes,
          profileRes,
          preferencesRes,
          expertsRes,
        ] = await Promise.all([

          api.get(
            `/user/${expertId}`,
          ),

          api.get(
            `/user/profile/${expertId}`,
          ),

          api.get(
            `/user/preferences/${expertId}`,
          ),

          api.get(
            "/user/experts",
          ),

        ]);

        const user =
          userRes?.user ?? null;

        const expertProfile =
          profileRes?.profile ?? null;

        const rawPreferences =
          preferencesRes?.preferences ?? {};

        const expertRows =
          Array.isArray(expertsRes)
            ? expertsRes
            : expertsRes?.experts ?? [];

        const currentExpert =
          expertRows.find(
            (row: any) =>
              row.ID_USER === expertId,
          );

        setExpert(
          user,
        );

        setProfile(
          expertProfile,
        );

        setPreferences({
          companies:
            Array.isArray(
              rawPreferences.companies,
            )
              ? rawPreferences.companies
              : [],

          solutions:
            Array.isArray(
              rawPreferences.solutions,
            )
              ? rawPreferences.solutions
              : [],

          topics:
            Array.isArray(
              rawPreferences.topics,
            )
              ? rawPreferences.topics
              : [],
        });

        setIsFavorite(
          !!currentExpert?.IS_SELECTED,
        );

      } catch (e) {

        console.error(
          "expert drawer load error",
          e,
        );

      } finally {

        setLoading(false);

      }

    }

    load();

  }, [
    expertId,
  ]);

  /* =====================================================
     FAVORITE
  ===================================================== */

  async function toggleFavorite() {

    try {

      if (isFavorite) {

        await api.delete(
          `/user/experts/${expertId}`,
        );

      } else {

        await api.post(
          `/user/experts/${expertId}`,
          {},
        );

      }

      setIsFavorite(
        previous =>
          !previous,
      );

    } catch (e) {

      console.error(
        "expert favorite error",
        e,
      );

    }

  }

  /* =====================================================
     LOADING
  ===================================================== */

  if (loading) {

    return (

      <EntityDrawer
        onClose={
          closeLeftDrawer
        }
        header={
          <DrawerHeader
            title="Expert"
            onClose={
              closeLeftDrawer
            }
          />
        }
      >

        <div
          className="
            py-8
            text-sm
            text-gray-500
          "
        >
          Loading...
        </div>

      </EntityDrawer>

    );

  }

  if (!expert) {

    return null;

  }

  /* =====================================================
     DISPLAY NAME
  ===================================================== */

  const displayName =
    expert.DISPLAY_NAME ??
    expert.NAME ??
    "Expert";

  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <EntityDrawer
      onClose={
        closeLeftDrawer
      }
      header={
        <DrawerHeader
          title={
            displayName
          }
          onClose={
            closeLeftDrawer
          }
        />
      }
    >

      {/* =====================================================
          IDENTITY
      ===================================================== */}

      <section
        className="
          border-b
          border-gray-200
          py-4
        "
      >

        <div
          className="
            flex
            items-start
            justify-between
            gap-4
          "
        >

          <div>

            <div
              className="
                text-lg
                font-semibold
                text-gray-900
              "
            >
              {displayName}
            </div>

            {expert.COMPANY && (

              <div
                className="
                  mt-1
                  text-sm
                  text-gray-500
                "
              >
                {expert.COMPANY}
              </div>

            )}

          </div>

          <button
            type="button"
            onClick={
              toggleFavorite
            }
            className="
              text-[22px]
              leading-none
            "
          >
            {
              isFavorite
                ? "⭐"
                : "☆"
            }
          </button>

        </div>

      </section>

      {/* =====================================================
          DESCRIPTION
      ===================================================== */}

      {expert.DESCRIPTION && (

        <section
          className="
            border-b
            border-gray-200
            py-4
          "
        >

          <div
            className="
              mb-2
              text-xs
              font-semibold
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            Description
          </div>

          <div
            className="
              text-sm
              leading-6
              text-gray-700
              whitespace-pre-wrap
            "
          >
            {expert.DESCRIPTION}
          </div>

        </section>

      )}

      {/* =====================================================
          PROFESSIONAL PROFILE
      ===================================================== */}

      {profile?.profile_text && (

        <section
          className="
            border-b
            border-gray-200
            py-4
          "
        >

          <div
            className="
              mb-2
              text-xs
              font-semibold
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            Professional Profile
          </div>

          <div
            className="
              rounded-lg
              bg-gray-50
              p-4
              text-sm
              leading-6
              text-gray-700
              whitespace-pre-wrap
            "
          >
            {profile.profile_text}
          </div>

        </section>

      )}

      {/* =====================================================
          COMPANIES
      ===================================================== */}

      {preferences.companies.length > 0 && (

        <section
          className="
            border-b
            border-gray-200
            py-4
          "
        >

          <div
            className="
              mb-3
              text-xs
              font-semibold
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            Companies
          </div>

          <div
            className="
              grid
              grid-cols-2
              gap-3
            "
          >

            {preferences.companies.map(
              item => (

                <EntityCard
                  key={item.id}
                  item={item}
                />

              ),
            )}

          </div>

        </section>

      )}

      {/* =====================================================
          SOLUTIONS
      ===================================================== */}

      {preferences.solutions.length > 0 && (

        <section
          className="
            border-b
            border-gray-200
            py-4
          "
        >

          <div
            className="
              mb-3
              text-xs
              font-semibold
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            Solutions
          </div>

          <div
            className="
              grid
              grid-cols-2
              gap-3
            "
          >

            {preferences.solutions.map(
              item => (

                <EntityCard
                  key={item.id}
                  item={item}
                />

              ),
            )}

          </div>

        </section>

      )}

      {/* =====================================================
          TOPICS
      ===================================================== */}

      {preferences.topics.length > 0 && (

        <section
          className="
            py-4
          "
        >

          <div
            className="
              mb-3
              text-xs
              font-semibold
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            Topics
          </div>

          <div
            className="
              flex
              flex-wrap
              gap-2
            "
          >

            {preferences.topics.map(
              item => (

                <div
                  key={item.id}
                  className="
                    rounded-full
                    bg-gray-100
                    px-3
                    py-1.5
                    text-sm
                    text-gray-700
                  "
                >
                  {item.label}
                </div>

              ),
            )}

          </div>

        </section>

      )}

    </EntityDrawer>

  );

}
