"use client";

import {
  useEffect,
  useState,
} from "react";

import CardSection
  from "@/components/ui/CardSection";

import {
  api,
} from "@/lib/api";

/* =========================================================
   TYPES
========================================================= */

type ExpertOption = {

  id: string;

  displayName: string;

  description?: string;

  isSelected: boolean;

  userCount?: number;

  isActive?: boolean;

};


type Props = {

  userId: string;

  refreshKey?: number;

};

/* =========================================================
   NORMALIZE
========================================================= */

function normalizeExpert(
  row: any,
): ExpertOption {

  return {

    id:
      row.ID_USER,

    displayName:
      row.DISPLAY_NAME
      ?? row.NAME
      ?? "",

    description:
      row.DESCRIPTION
      ?? "",

    isSelected:
      !!row.IS_SELECTED,

    userCount:
      row.USER_COUNT
      ?? 0,

    isActive:
      row.IS_ACTIVE !== false,

  };

}

/* =========================================================
   COMPONENT
========================================================= */

export default function ProfileExpertsCard({

  userId,

  refreshKey = 0,

}: Props) {

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    experts,
    setExperts,
  ] = useState<ExpertOption[]>([]);

  const [
    updatingExpertId,
    setUpdatingExpertId,
  ] = useState<string | null>(
    null,
  );

  /* =======================================================
     LOAD
  ======================================================= */

  async function loadExperts() {

    if (!userId) {

      setExperts(
        [],
      );

      setLoading(
        false,
      );

      return;

    }

    setLoading(
      true,
    );

    try {

      const res =
        await api.get(
          `/user/admin/${userId}/experts`,
        );

      const rows =
        Array.isArray(
          res?.experts,
        )
          ? res.experts
          : [];

      setExperts(
        rows.map(
          normalizeExpert,
        ),
      );

    } catch (error) {

      console.error(
        "Failed to load experts",
        error,
      );

      setExperts(
        [],
      );

    } finally {

      setLoading(
        false,
      );

    }

  }

  /* =======================================================
     TOGGLE
  ======================================================= */

  async function toggleExpert(
    expert: ExpertOption,
  ) {

    if (
      updatingExpertId
      || !userId
    ) {

      return;

    }

    setUpdatingExpertId(
      expert.id,
    );

    try {

      if (expert.isSelected) {

        await api.delete(
          `/user/admin/${userId}/experts/${expert.id}`,
        );

      } else {

        await api.post(
          `/user/admin/${userId}/experts/${expert.id}`,
          {},
        );

      }

      setExperts(
        previous =>
          previous.map(
            current => {

              if (
                current.id !==
                expert.id
              ) {

                return current;

              }

              return {

                ...current,

                isSelected:
                  !current.isSelected,

                userCount:
                  current.isSelected

                    ? Math.max(
                        0,
                        (
                          current.userCount
                          ?? 0
                        ) - 1,
                      )

                    : (
                        current.userCount
                        ?? 0
                      ) + 1,

              };

            },
          ),
      );

    } catch (error) {

      console.error(
        "Failed to update expert",
        error,
      );

      alert(
        "Unable to update this expert. "
        + "Check that the user and expert "
        + "share at least one universe.",
      );

      await loadExperts();

    } finally {

      setUpdatingExpertId(
        null,
      );

    }

  }

  /* =======================================================
     RELOAD
  ======================================================= */

  useEffect(() => {

    loadExperts();

  }, [
    userId,
    refreshKey,
  ]);

  /* =======================================================
     COUNTS
  ======================================================= */

  const selectedCount =
    experts.filter(
      expert =>
        expert.isSelected,
    ).length;

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <CardSection

      title="Experts"

      description="
        Only Experts sharing at least
        one universe with this user
        can be selected.
      "

    >

      {loading ? (

        <div
          className="
            py-8
            text-center
            text-sm
            text-gray-500
          "
        >
          Loading...
        </div>

      ) : experts.length === 0 ? (

        <div
          className="
            rounded-lg
            border
            border-dashed
            border-gray-200
            px-5
            py-8
            text-center
          "
        >

          <div
            className="
              text-sm
              font-medium
              text-gray-700
            "
          >
            No compatible Experts
          </div>

          <div
            className="
              mt-1
              text-xs
              text-gray-500
            "
          >
            Assign at least one universe
            shared with an active Expert.
          </div>

        </div>

      ) : (

        <div
          className="
            space-y-3
          "
        >

          {experts.map(
            expert => {

              const updating =
                updatingExpertId ===
                expert.id;

              const disabled = Boolean(
                updatingExpertId,
              );

              return (

                <label

                  key={
                    expert.id
                  }

                  className={`
                    flex
                    items-start
                    gap-4
                    rounded-lg
                    border
                    p-4
                    transition

                    ${

                      disabled

                        ? `
                          cursor-not-allowed
                          opacity-60
                        `

                        : `
                          cursor-pointer
                        `

                    }

                    ${

                      expert.isSelected

                        ? `
                          border-blue-500
                          bg-blue-50
                        `

                        : `
                          border-gray-200
                          bg-white
                          hover:bg-gray-50
                        `

                    }
                  `}

                >

                  <input

                    type="checkbox"

                    checked={
                      expert.isSelected
                    }

                    disabled={
                      disabled
                    }

                    onChange={() =>
                      toggleExpert(
                        expert,
                      )
                    }

                    className="
                      mt-1
                      h-4
                      w-4
                    "

                  />

                  <div
                    className="
                      min-w-0
                      flex-1
                    "
                  >

                    <div
                      className="
                        flex
                        items-center
                        gap-2
                      "
                    >

                      <div
                        className="
                          font-medium
                        "
                      >
                        {expert.displayName}
                      </div>

                      {updating && (

                        <span
                          className="
                            text-xs
                            text-gray-400
                          "
                        >
                          Updating...
                        </span>

                      )}

                      {expert.isActive ===
                        false && (

                        <span
                          className="
                            rounded-full
                            bg-red-100
                            px-2
                            py-0.5
                            text-xs
                            text-red-700
                          "
                        >
                          Inactive
                        </span>

                      )}

                    </div>

                    {expert.description && (

                      <div
                        className="
                          mt-1
                          text-sm
                          text-gray-500
                        "
                      >
                        {expert.description}
                      </div>

                    )}

                    <div
                      className="
                        mt-2
                        text-xs
                        text-gray-400
                      "
                    >
                      {expert.userCount ?? 0}
                      {" "}
                      subscribers
                    </div>

                  </div>

                </label>

              );

            },
          )}

          <div
            className="
              border-t
              pt-3
              text-right
              text-xs
              text-gray-500
            "
          >
            {selectedCount}
            {" / "}
            {experts.length}
            {" selected"}
          </div>

        </div>

      )}

    </CardSection>

  );

}
