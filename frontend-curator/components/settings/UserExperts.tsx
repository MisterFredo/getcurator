"use client";

import {
  useEffect,
  useState,
} from "react";

import { api } from "@/lib/api";

/* =========================================================
   TYPES
========================================================= */

type Expert = {
  id: string;
  displayName: string;
  description: string;
  frequency?: string;
  isSelected: boolean;
  isActive: boolean;
};

/* =========================================================
   NORMALIZE
========================================================= */

function normalizeExpert(
  row: any,
): Expert {

  return {
    id: row.ID_USER,
    displayName:
      row.DISPLAY_NAME ??
      row.NAME ??
      "Expert",
    description:
      row.DESCRIPTION ?? "",
    frequency:
      row.FREQUENCY ?? "",
    isSelected:
      !!row.IS_SELECTED,
    isActive:
      row.IS_ACTIVE !== false,
  };

}

/* =========================================================
   COMPONENT
========================================================= */

export default function UserExperts() {

  const [loading, setLoading] =
    useState(true);

  const [experts, setExperts] =
    useState<Expert[]>([]);

  /* =====================================================
     LOAD
  ===================================================== */

  async function loadExperts() {

    try {

      setLoading(true);

      const res =
        await api.get(
          "/user/experts",
        );

      /*
       * Public route currently returns
       * get_user_experts() directly.
       *
       * We accept both formats so the
       * component remains robust:
       *
       * [...]
       *
       * or
       *
       * { experts: [...] }
       */

      const rows =
        Array.isArray(res)
          ? res
          : res?.experts ?? [];

      setExperts(
        rows.map(
          normalizeExpert,
        ),
      );

    } catch (e) {

      console.error(
        "experts load error",
        e,
      );

    } finally {

      setLoading(false);

    }

  }

  /* =====================================================
     TOGGLE
  ===================================================== */

  async function toggleExpert(
    expert: Expert,
  ) {

    try {

      if (expert.isSelected) {

        await api.delete(
          `/user/experts/${expert.id}`,
        );

      } else {

        await api.post(
          `/user/experts/${expert.id}`,
          {},
        );

      }

      setExperts(
        previous =>
          previous.map(item => {

            if (
              item.id !== expert.id
            ) {
              return item;
            }

            return {
              ...item,
              isSelected:
                !item.isSelected,
            };

          }),
      );

    } catch (e) {

      console.error(
        "expert toggle error",
        e,
      );

    }

  }

  /* =====================================================
     LOADING
  ===================================================== */

  if (loading) {

    return (
      <div
        className="
          py-8
          text-center
          text-sm
          text-gray-500
        "
      >
        Loading experts...
      </div>
    );

  }

  /* =====================================================
     EMPTY
  ===================================================== */

  if (experts.length === 0) {

    return (
      <div
        className="
          py-8
          text-center
          text-sm
          text-gray-500
        "
      >
        No Experts available.
      </div>
    );

  }

  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <div className="space-y-5">

      {/* HEADER */}

      <div>

        <div
          className="
            text-base
            font-semibold
            text-gray-900
          "
        >
          My Experts
        </div>

        <div
          className="
            mt-1
            text-sm
            text-gray-500
          "
        >
          Select the Experts you want
          to add to your GetCurator
          experience.
        </div>

      </div>

      {/* GRID */}

      <div
        className="
          grid
          grid-cols-1
          gap-4
          md:grid-cols-2
        "
      >

        {experts.map(
          expert => (

            <div
              key={expert.id}
              className={`
                rounded-xl
                border
                p-5
                transition

                ${
                  expert.isSelected
                    ? `
                      border-emerald-300
                      bg-emerald-50/40
                    `
                    : `
                      border-gray-200
                      bg-white
                    `
                }
              `}
            >

              {/* TOP */}

              <div
                className="
                  flex
                  items-start
                  justify-between
                  gap-4
                "
              >

                <div
                  className="
                    min-w-0
                  "
                >

                  <div
                    className="
                      font-semibold
                      text-gray-900
                    "
                  >
                    {
                      expert.displayName
                    }
                  </div>

                  {
                    expert.frequency && (

                      <div
                        className="
                          mt-2
                          inline-flex
                          rounded-full
                          bg-gray-100
                          px-2.5
                          py-1
                          text-xs
                          text-gray-600
                        "
                      >
                        {
                          expert.frequency
                        }
                      </div>

                    )
                  }

                </div>

                {
                  expert.isSelected && (

                    <div
                      className="
                        shrink-0
                        rounded-full
                        bg-emerald-100
                        px-2.5
                        py-1
                        text-xs
                        font-medium
                        text-emerald-700
                      "
                    >
                      Selected
                    </div>

                  )
                }

              </div>

              {/* DESCRIPTION */}

              {
                expert.description && (

                  <div
                    className="
                      mt-4
                      text-sm
                      leading-6
                      text-gray-600
                    "
                  >
                    {
                      expert.description
                    }
                  </div>

                )
              }

              {/* ACTION */}

              <div
                className="
                  mt-5
                  border-t
                  border-gray-100
                  pt-4
                "
              >

                <button
                  type="button"
                  disabled={
                    !expert.isActive
                  }
                  onClick={() =>
                    toggleExpert(
                      expert,
                    )
                  }
                  className={`
                    rounded-lg
                    px-4
                    py-2
                    text-sm
                    font-medium
                    transition

                    ${
                      expert.isSelected
                        ? `
                          border
                          border-gray-200
                          bg-white
                          text-gray-700
                          hover:bg-gray-50
                        `
                        : `
                          bg-emerald-600
                          text-white
                          hover:bg-emerald-700
                        `
                    }

                    ${
                      !expert.isActive
                        ? `
                          cursor-not-allowed
                          opacity-50
                        `
                        : ""
                    }
                  `}
                >

                  {
                    !expert.isActive
                      ? "Unavailable"
                      : expert.isSelected
                        ? "Remove"
                        : "Add Expert"
                  }

                </button>

              </div>

            </div>

          ),
        )}

      </div>

    </div>

  );

}
