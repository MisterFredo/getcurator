"use client";

import CardSection from "@/components/ui/CardSection";

/* ========================================================= */

export type ExpertOption = {
  id: string;
  displayName: string;
  description?: string;

  isSelected: boolean;

  frequency?: string;
  userCount?: number;
  isActive?: boolean;
};

/* ========================================================= */

type Props = {
  experts: ExpertOption[];

  onToggleExpert: (
    expertId: string,
  ) => void;
};

/* ========================================================= */

export default function UserExpertsCard({
  experts,
  onToggleExpert,
}: Props) {

  return (

    <CardSection
      title="Experts"
      description="Users receive Digests and can interact with the selected Experts."
    >

      {experts.length === 0 ? (

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
                  onToggleExpert(
                    expert.id,
                  )
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

                {expert.userCount !== undefined && (

                  <div className="mt-2 text-xs text-gray-400">

                    {expert.userCount} subscribers

                  </div>

                )}

              </div>

            </label>

          ))}

          <div className="border-t pt-3 text-right text-xs text-gray-500">

            {
              experts.filter(
                (expert) => expert.isSelected,
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
