import Link from "next/link";

import LinkedInStudio from "@/components/admin/content/LinkedInStudio";

/* ========================================================= */

export default function LinkedInStudioPage() {

  return (

    <div className="space-y-10">

      <div className="flex items-center justify-between">

        <div>

          <h1 className="text-3xl font-semibold text-ratecard-blue">
            LinkedIn Studio
          </h1>

          <p className="text-gray-500 mt-1">
            Import LinkedIn activity into the content pipeline.
          </p>

        </div>

        <Link
          href="/admin/content"
          className="underline"
        >
          ← Back
        </Link>

      </div>

      <LinkedInStudio />

    </div>

  );

}
