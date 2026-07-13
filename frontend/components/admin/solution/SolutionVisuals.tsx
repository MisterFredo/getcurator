// components/admin/solution/SolutionVisuals.tsx

"use client";

import VisualSection from "@/components/visuals/VisualSection";

/* ========================================================= */

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL!;

const SOLUTION_MEDIA_PATH =
  "solutions";

/* ========================================================= */

type Props = {

  solutionId: string | null;

  logoFilename: string | null;

  onUpdated: () => Promise<void>;

};

/* ========================================================= */

export default function SolutionVisuals({

  solutionId,

  logoFilename,

  onUpdated,

}: Props) {

  if (!solutionId) {

    return (

      <section className="space-y-4">

        <div>

          <h2 className="text-lg font-semibold">
            Visuals
          </h2>

          <p className="text-sm text-gray-500">
            Save the solution before uploading a logo.
          </p>

        </div>

      </section>

    );

  }

  const rectUrl =
    logoFilename
      ? `${GCS_BASE_URL}/${SOLUTION_MEDIA_PATH}/${logoFilename}`
      : null;

  return (

    <section className="space-y-6">

      <div>

        <h2 className="text-lg font-semibold">
          Visuals
        </h2>

        <p className="text-sm text-gray-500">
          Upload the assets associated with this solution.
        </p>

      </div>

      <VisualSection
        entityId={solutionId}
        entityType="solution"
        rectUrl={rectUrl}
        onUpdated={onUpdated}
      />

    </section>

  );

}
