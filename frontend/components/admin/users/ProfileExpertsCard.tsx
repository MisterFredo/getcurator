"use client";

import { useEffect, useState } from "react";

import CardSection from "@/components/ui/CardSection";
import { api } from "@/lib/api";

/* ========================================================= */

type ExpertOption = {
  id: string;
  displayName: string;
  description?: string;
  isSelected: boolean;
  frequency?: string;
  userCount?: number;
  isActive?: boolean;
};

type Props = {
  userId: string;
};

/* ========================================================= */

function normalizeExpert(row: any): ExpertOption {
  return {
    id: row.ID_USER,
    displayName: row.DISPLAY_NAME ?? row.NAME ?? "",
    description: row.DESCRIPTION ?? "",
    isSelected: !!row.IS_SELECTED,
    frequency: row.FREQUENCY ?? "",
    userCount: row.USER_COUNT ?? 0,
    isActive: !!row.IS_ACTIVE,
  };
}

/* ========================================================= */

export default function ProfileExpertsCard({
  userId,
}: Props) {

  const [loading, setLoading] =
    useState(true);

  const [experts, setExperts] =
    useState<ExpertOption[]>([]);

  /* ========================================================= */

  async function loadExperts() {

    if (!userId) return;

    setLoading(true);

    try {

      const res =
        await api.get(
          `/user/admin/${userId}/experts`
        );

      setExperts(
        (res.experts ?? []).map(
          normalizeExpert
        )
      );

    } finally {

      setLoading(false);

    }

  }

  /* ========================================================= */

  async function toggleExpert(
    expert: ExpertOption,
  ) {

    if (expert.isSelected) {

      await api.delete(
        `/user/admin/${userId}/experts/${expert.id}`
      );

    } else {

      await api.post(
        `/user/admin/${userId}/experts/${expert.id}`,
        {}
      );

    }

    setExperts(previous =>
      previous.map(e => {

        if (e.id !== expert.id) {
          return e;
        }

        return {
          ...e,
          isSelected: !e.isSelected,
          userCount: e.isSelected
            ? Math.max(0, (e.userCount ?? 0) - 1)
            : (e.userCount ?? 0) + 1,
        };

      })
    );

  }

  /* ========================================================= */

  useEffect(() => {

    loadExperts();

  }, [userId]);

  /* ========================================================= */

  return (

    <CardSection
      title="Experts"
      description="Users receive Digests and can interact with the selected Experts."
    >

      {loading ? (

        <div className="py-8 text-center text-sm text-gray-500">
          Loading...
        </div>

      ) : experts.length === 0 ? (

        <div className="py-8 text-center text-sm text-gray-500">
          No Experts available.
        </div>

      ) : (

        <div className="space-y-3">

          {experts.map((expert) => (

            <label
              key={expert.id}
              className={`
                flex
                items-start
                gap-4
                rounded-lg
                border
                p-4
                cursor-pointer
                transition

                ${
                  expert.isSelected
                    ? "border-blue-500 bg-blue-50"
                    : "hover:bg-gray-50"
                }
              `}
            >

              <input
                type="checkbox"
                checked={expert.isSelected}
                onChange={() =>
                  toggleExpert(expert)
                }
                className="mt-1 h-4 w-4"
              />

              <div className="min-w-0 flex-1">

                <div className="flex items-center gap-2">

                  <div className="font-medium">
                    {expert.displayName}
                  </div>

                  {expert.frequency && (
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                      {expert.frequency}
                    </span>
                  )}

                  {expert.isActive === false && (
                    <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700">
                      Inactive
                    </span>
                  )}

                </div>

                {expert.description && (
                  <div className="mt-1 text-sm text-gray-500">
                    {expert.description}
                  </div>
                )}

                <div className="mt-2 text-xs text-gray-400">
                  {expert.userCount ?? 0} subscribers
                </div>

              </div>

            </label>

          ))}

          <div className="border-t pt-3 text-right text-xs text-gray-500">
            {
              experts.filter(
                expert => expert.isSelected
              ).length
            }
            {" / "}
            {experts.length}
            {" selected"}
          </div>

        </div>

      )}

    </CardSection>

  );

}
