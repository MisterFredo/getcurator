"use client";

type Operation = {
  id: string;
  label: string;
  description: string;
  variant?: "default" | "warning" | "danger";
};

type OperationGroup = {
  title: string;
  operations: Operation[];
};

const GROUPS: OperationGroup[] = [
  {
    title: "Publishing",
    operations: [
      {
        id: "draft_to_published",
        label: "Draft → Published",
        description: "Publish every draft content.",
      },
    ],
  },
  {
    title: "Maintenance",
    operations: [
      {
        id: "populate_content_enriched",
        label: "Populate CONTENT_ENRICHED",
        description: "Refresh the CONTENT_ENRICHED table.",
      },
      {
        id: "rebuild_company",
        label: "Rebuild Content → Company",
        description: "Rebuild company mappings.",
      },
      {
        id: "rebuild_solution",
        label: "Rebuild Content → Solution",
        description: "Rebuild solution mappings.",
      },
    ],
  },
  {
    title: "Quality",
    operations: [
      {
        id: "check_duplicate_urls",
        label: "Check Duplicate URLs",
        description: "Detect duplicated SOURCE_URL values.",
      },
      {
        id: "delete_duplicate_urls",
        label: "Delete Duplicate URLs",
        description: "Remove duplicated contents.",
        variant: "danger",
      },
    ],
  },
];

/* ========================================================= */

export default function ContentOperations() {

  return (

    <div className="border rounded-lg bg-white p-6 space-y-6">

      <h2 className="text-xl font-semibold">
        Operations
      </h2>

      {GROUPS.map((group) => (

        <div
          key={group.title}
          className="space-y-3"
        >

          <h3 className="text-sm font-semibold uppercase text-gray-500">
            {group.title}
          </h3>

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">

            {group.operations.map((operation) => (

              <button
                key={operation.id}
                type="button"
                className={`border rounded-lg p-4 text-left hover:border-blue-500 transition ${
                  operation.variant === "danger"
                    ? "border-red-300"
                    : ""
                }`}
              >

                <div className="font-medium">
                  {operation.label}
                </div>

                <div className="mt-1 text-sm text-gray-500">
                  {operation.description}
                </div>

              </button>

            ))}

          </div>

        </div>

      ))}

    </div>

  );

}
