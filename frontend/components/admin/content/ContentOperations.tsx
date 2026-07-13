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
        description:
          "Publish every draft content.",
      },
    ],
  },

  {
    title: "Maintenance",
    operations: [
      {
        id: "populate_content_enriched",
        label: "Populate CONTENT_ENRICHED",
        description:
          "Refresh the CONTENT_ENRICHED table.",
      },
      {
        id: "rebuild_company",
        label: "Rebuild Content → Company",
        description:
          "Rebuild company mappings.",
      },
      {
        id: "rebuild_solution",
        label: "Rebuild Content → Solution",
        description:
          "Rebuild solution mappings.",
      },
    ],
  },

  {
    title: "Quality",
    operations: [
      {
        id: "check_duplicate_urls",
        label: "Check Duplicate URLs",
        description:
          "Detect duplicated SOURCE_URL values.",
      },
      {
        id: "delete_duplicate_urls",
        label: "Delete Duplicate URLs",
        description:
          "Remove duplicated contents.",
        variant: "danger",
      },
    ],
  },
];
