"use client";

import Link from "next/link";

import NewsletterStudio from "@/components/admin/content/NewsletterStudio";

export default function NewsletterStudioPage() {

  return (

    <div className="space-y-8">

      <div className="flex items-center justify-between">

        <div>

          <h1 className="text-3xl font-semibold">
            Newsletter Studio
          </h1>

          <p className="text-gray-500 mt-1">
            Extract and import articles from newsletters.
          </p>

        </div>

        <Link
          href="/admin/content"
          className="
            border
            rounded
            px-4
            py-2
            text-sm
            hover:bg-gray-50
          "
        >
          Back to contents
        </Link>

      </div>

      <NewsletterStudio />

    </div>

  );

}
