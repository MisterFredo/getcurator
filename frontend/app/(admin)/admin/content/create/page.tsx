import Link from "next/link";

import ContentStudio from "@/components/admin/content/ContentStudio";

/* ========================================================= */

export default function CreateContentPage() {

  return (

    <div className="space-y-10">

      <div className="flex items-center justify-between">

        <div>

          <h1 className="text-3xl font-semibold text-ratecard-blue">
            New content
          </h1>

          <p className="text-gray-500 mt-1">
            Create and prepare a new content.
          </p>

        </div>

        <Link
          href="/admin/content"
          className="underline"
        >
          ← Back
        </Link>

      </div>

      <ContentStudio
        mode="create"
      />

    </div>

  );

}
