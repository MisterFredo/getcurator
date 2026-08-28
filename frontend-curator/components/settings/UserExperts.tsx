"use client";

import {
  useEffect,
  useState,
} from "react";

import { api } from "@/lib/api";

import ExpertCard
  from "@/components/expert/ExpertCard";

/* =========================================================
   TYPES
========================================================= */

type Expert = {
  id: string;
  displayName: string;
  company?: string | null;
  description?: string | null;
  isFavorite: boolean;
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

    company:
      row.COMPANY ?? null,

    description:
      row.DESCRIPTION ?? null,

    isFavorite:
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

  useEffect(() => {

    async function loadExperts() {

      try {

        setLoading(true);

        const res =
          await api.get(
            "/user/experts",
          );

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

        setExperts([]);

      } finally {

        setLoading(false);

      }

    }

    loadExperts();

  }, []);

  /* =====================================================
     FAVORITE UPDATE
  ===================================================== */

  function handleToggleFavorite(
    id: string,
    isFavorite: boolean,
  ) {

    setExperts(
      previous =>
        previous.map(
          expert => {

            if (
              expert.id !== id
            ) {
              return expert;
            }

            return {
              ...expert,
              isFavorite:
                !isFavorite,
            };

          },
        ),
    );

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
          Experts
        </div>

        <div
          className="
            mt-1
            text-sm
            text-gray-500
          "
        >
          Select the Experts you want
          to follow.
        </div>

      </div>

      {/* GRID */}

      <div
        className="
          grid
          grid-cols-[repeat(auto-fit,minmax(145px,1fr))]
          gap-4
        "
      >

        {experts.map(
          expert => (

            <ExpertCard

              key={expert.id}

              id={expert.id}

              displayName={
                expert.displayName
              }

              company={
                expert.company
              }

              description={
                expert.description
              }

              isFavorite={
                expert.isFavorite
              }

              isLoading={
                !expert.isActive
              }

              onToggleFavorite={
                handleToggleFavorite
              }

            />

          ),
        )}

      </div>

    </div>

  );

}
