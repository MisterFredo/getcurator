"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  api,
} from "@/lib/api";

import HomeInterlocutors, {
  HomeInterlocutor,
} from "@/components/home/HomeInterlocutors";

import HomeContents
  from "@/components/home/HomeContents";

import HomeDigests
  from "@/components/home/HomeDigests";

import HomeConversation
  from "@/components/home/HomeConversation";

/* =========================================================
   TYPES
========================================================= */

type ExpertRow = {
  ID_USER: string;
  DISPLAY_NAME?: string | null;
  NAME?: string | null;
  COMPANY?: string | null;
  DESCRIPTION?: string | null;
  IS_SELECTED?: boolean;
  IS_ACTIVE?: boolean;
};

/* =========================================================
   PAGE
========================================================= */

export default function HomePage() {

  const [
    interlocutors,
    setInterlocutors,
  ] = useState<HomeInterlocutor[]>(
    [],
  );

  const [
    selectedInterlocutorId,
    setSelectedInterlocutorId,
  ] = useState<string | null>(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  /* =========================================================
     LOAD
  ========================================================= */

  useEffect(() => {

    async function load() {

      setLoading(
        true,
      );

      try {

        const [
          meRes,
          expertsRes,
        ] = await Promise.all([

          api.get(
            "/user/me",
          ),

          api.get(
            "/user/experts",
          ),

        ]);

        /* ===================================================
           CURRENT USER
        =================================================== */

        const user =
          meRes?.user;

        if (!user?.ID_USER) {

          setError(
            "Unable to identify the current user.",
          );

          return;

        }

        const self:
          HomeInterlocutor = {

          id:
            user.ID_USER,

          displayName:
            user.DISPLAY_NAME
            ??
            user.NAME
            ??
            "User",

          company:
            user.COMPANY
            ?? null,

          description:
            "Your profile, interests and accumulated knowledge.",

          type:
            "self",
        };

        /* ===================================================
           EXPERTS
        =================================================== */

        const expertRows:
          ExpertRow[] =
          Array.isArray(
            expertsRes,
          )
            ? expertsRes
            : expertsRes?.experts
              ?? [];

        const experts:
          HomeInterlocutor[] =
          expertRows
            .filter(
              expert =>
                expert.IS_SELECTED === true
                &&
                expert.IS_ACTIVE !== false,
            )
            .map(
              expert => ({

                id:
                  expert.ID_USER,

                displayName:
                  expert.DISPLAY_NAME
                  ??
                  expert.NAME
                  ??
                  "Expert",

                company:
                  expert.COMPANY
                  ?? null,

                description:
                  expert.DESCRIPTION
                  ?? null,

                type:
                  "expert",

              }),
            );

        /* ===================================================
           AVAILABLE INTERLOCUTORS
        =================================================== */

        const available = [
          self,
          ...experts,
        ];

        setInterlocutors(
          available,
        );

        setSelectedInterlocutorId(
          self.id,
        );

        setError(
          null,
        );

      } catch (e) {

        console.error(
          "❌ Home load error:",
          e,
        );

        setInterlocutors(
          [],
        );

        setSelectedInterlocutorId(
          null,
        );

        setError(
          "Unable to load your profiles.",
        );

      } finally {

        setLoading(
          false,
        );

      }

    }

    load();

  }, []);

  /* =========================================================
     SELECTED INTERLOCUTOR
  ========================================================= */

  const selectedInterlocutor =
    useMemo(
      () => {

        if (
          !selectedInterlocutorId
        ) {

          return null;

        }

        return (
          interlocutors.find(
            interlocutor =>
              interlocutor.id ===
              selectedInterlocutorId,
          )
          ?? null
        );

      },
      [
        interlocutors,
        selectedInterlocutorId,
      ],
    );

  /* =========================================================
     SELECT
  ========================================================= */

  function handleSelectInterlocutor(
    id: string,
  ) {

    setSelectedInterlocutorId(
      id,
    );

  }

  /* =========================================================
     LOADING
  ========================================================= */

  if (loading) {

    return (

      <div
        className="
          flex
          min-h-[500px]
          items-center
          justify-center
        "
      >

        <div
          className="
            text-sm
            text-gray-400
          "
        >
          Loading your GetCurator...
        </div>

      </div>

    );

  }

  /* =========================================================
     ERROR
  ========================================================= */

  if (
    error
    ||
    !selectedInterlocutor
  ) {

    return (

      <div
        className="
          mx-auto
          max-w-3xl
          py-12
        "
      >

        <div
          className="
            rounded-xl
            border
            border-red-200
            bg-red-50
            px-5
            py-4
            text-sm
            text-red-700
          "
        >
          {
            error
            ?? "No profile available."
          }
        </div>

      </div>

    );

  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div
      className="
        mx-auto
        max-w-[1500px]
        space-y-8
      "
    >

      {/* =====================================================
          PROFILE SELECTOR
      ===================================================== */}

      <HomeInterlocutors

        interlocutors={
          interlocutors
        }

        selectedId={
          selectedInterlocutorId
        }

        onSelect={
          handleSelectInterlocutor
        }

      />

      {/* =====================================================
          MAIN GRID
      ===================================================== */}

      <div
        className="
          grid
          grid-cols-1
          gap-8

          lg:grid-cols-[minmax(0,1.4fr)_minmax(360px,1fr)]
        "
      >

        {/* ===================================================
            LEFT
        =================================================== */}

        <div
          className="
            space-y-10
          "
        >

          {/* =================================================
              CONTENTS
          ================================================= */}

          <HomeContents

            interlocutorId={
              selectedInterlocutor.id
            }

          />

          {/* =================================================
              DIGESTS
          ================================================= */}

          <HomeDigests

            interlocutorId={
              selectedInterlocutor.id
            }

          />

        </div>

        {/* ===================================================
            RIGHT
        =================================================== */}

        <div
          className="
            lg:sticky
            lg:top-6
            lg:self-start
          "
        >

          <HomeConversation

            interlocutorId={
              selectedInterlocutor.id
            }

            interlocutorName={
              selectedInterlocutor
                .displayName
            }

          />

        </div>

      </div>

    </div>

  );

}
