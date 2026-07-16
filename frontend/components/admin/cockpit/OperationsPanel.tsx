
"use client";

import {
  Play,
  RefreshCw,
  Database,
  Upload,
  HardDrive,
  RotateCcw,
} from "lucide-react";

import {
  useCockpitOperations,
} from "@/hooks/useCockpitOperations";

/* ========================================================= */

type Operation = {
  id: string;
  label: string;
  description: string;
  icon: React.ElementType;
};

type Group = {
  title: string;
  operations: Operation[];
};

/* ========================================================= */

const GROUPS: Group[] = [

  {
    title: "Publishing",

    operations: [
      {
        id: "publish-drafts",
        label: "Publish Drafts",
        description:
          "Publish every draft content.",
        icon: Upload,
      },
    ],
  },

  {
    title: "Maintenance",

    operations: [
      {
        id: "rebuild-company",
        label: "Rebuild Company",
        description:
          "Rebuild Content → Company.",
        icon: RefreshCw,
      },
      {
        id: "rebuild-solution",
        label: "Rebuild Solution",
        description:
          "Rebuild Content → Solution.",
        icon: RefreshCw,
      },
      {
        id: "populate-content-enriched",
        label: "Populate CONTENT_ENRICHED",
        description:
          "Refresh CONTENT_ENRICHED.",
        icon: Database,
      },
    ],
  },

  {
    title: "Environment",

    operations: [
      {
        id: "backup",
        label: "Backup Production",
        description:
          "Copy PROD to BACKUP.",
        icon: HardDrive,
      },
      {
        id: "sync-dev",
        label: "Sync Development",
        description:
          "Copy PROD to DEV.",
        icon: Database,
      },
    ],
  },

  {
    title: "Processing",

    operations: [
      {
        id: "restart-destock",
        label: "Restart Destock",
        description:
          "Restart stopped contents.",
        icon: RotateCcw,
      },
    ],
  },

];

/* ========================================================= */

export default function OperationsPanel() {

  const {
    loading,
    success,
    error,
    run,
  } = useCockpitOperations();

  return (

    <div className="border rounded-xl bg-white p-6">

      <div className="mb-6">

        <h2 className="text-xl font-semibold">
          Operations
        </h2>

        <p className="text-sm text-gray-500 mt-1">
          Maintenance and administration tasks.
        </p>

      </div>

      {success && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {success}
        </div>
      )}

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="space-y-8">

        {GROUPS.map((group) => (

          <div key={group.title}>

            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
              {group.title}
            </h3>

            <div className="space-y-3">

              {group.operations.map((operation) => {

                const Icon =
                  operation.icon;

                return (

                  <div
                    key={operation.id}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >

                    <div className="flex items-start gap-3">

                      <Icon
                        size={18}
                        className="mt-1 text-gray-500"
                      />

                      <div>

                        <div className="font-medium">
                          {operation.label}
                        </div>

                        <div className="text-sm text-gray-500">
                          {operation.description}
                        </div>

                      </div>

                    </div>

                    <button
                      disabled={loading}
                      onClick={() =>
                        run(operation.id)
                      }
                      className="inline-flex items-center gap-2 rounded-lg bg-ratecard-blue px-4 py-2 text-white disabled:opacity-50"
                    >

                      <Play size={16} />

                      Run

                    </button>

                  </div>

                );

              })}

            </div>

          </div>

        ))}

      </div>

    </div>

  );

}
