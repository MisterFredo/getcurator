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

          {companyId
            ? "Upload the assets associated with this company."
            : "Save the company before uploading a logo."}

        </p>

      </div>

      {!companyId ? (

        <div className="rounded border border-dashed p-6 text-sm text-gray-500">

          The visual section will become available once the company has been created.

        </div>

      ) : (

        <VisualSection
          entityId={companyId}
          entityType="company"
          rectUrl={rectUrl}
          onUpdated={onUpdated}
        />

      )}

    </section>

  );

}
