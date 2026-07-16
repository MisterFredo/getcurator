"use client";

import { ChevronRight } from "lucide-react";

export default function QualityPanel() {

  const reports = [

    {
      id: "duplicate-titles",
      label: "Duplicate titles",
    },

    {
      id: "unmatched-companies",
      label: "Unmatched companies",
    },

    {
      id: "unmatched-solutions",
      label: "Unmatched solutions",
    },

    {
      id: "numbers-structure",
      label: "Numbers structure",
    },

  ];

  return (

    <div className="border rounded-xl bg-white p-6">

      <h2 className="text-xl font-semibold">
        Quality
      </h2>

      <p className="text-sm text-gray-500 mt-1">
        Dataset quality diagnostics.
      </p>

      <div className="mt-6 space-y-2">

        {reports.map((report) => (

          <button
            key={report.id}
            className="w-full flex items-center justify-between border rounded-lg p-4 hover:bg-gray-50"
          >

            <span>

              {report.label}

            </span>

            <ChevronRight size={18} />

          </button>

        ))}

      </div>

    </div>

  );

}
