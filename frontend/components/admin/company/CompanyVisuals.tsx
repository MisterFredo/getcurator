// components/admin/company/CompanyVisuals.tsx

"use client";

import VisualSection from "@/components/visuals/VisualSection";

/* ========================================================= */

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL!;

const COMPANY_MEDIA_PATH =
  "companies";

/* ========================================================= */

type Props = {
  companyId: string | null;

  logoFilename: string | null;

  onUpdated: () => Promise<void>;
};

/* ========================================================= */

export default function CompanyVisuals({

  companyId,

  logoFilename,

  onUpdated,

}: Props) {

  if (!companyId) {

    return (

      <section className="space-y-4">

        <div>

          <h2 className="text-lg font-semibold">
            Visuals
          </h2>

          <p className="text-sm text-gray-500">
            Save the company before uploading a logo.
          </p>

        </div>

      </section>

    );

  }

  const rectUrl =
    logoFilename
      ? `${GCS_BASE_URL}/${COMPANY_MEDIA_PATH}/${logoFilename}`
      : null;

  return (

    <section className="space-y-6">

      <div>

        <h2 className="text-lg font-semibold">
          Visuals
        </h2>

        <p className="text-sm text-gray-500">
          Upload the assets associated with this company.
        </p>

      </div>

      <VisualSection
        entityId={companyId}
        entityType="company"
        rectUrl={rectUrl}
        onUpdated={onUpdated}
      />

    </section>

  );

}
