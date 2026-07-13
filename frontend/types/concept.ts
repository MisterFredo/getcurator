// frontend/types/concept.ts

/* ========================================================= */

export type ConceptFormData = {
  label: string;

  description: string;
};

/* ========================================================= */

export const EMPTY_CONCEPT: ConceptFormData = {
  label: "",

  description: "",
};

/* ========================================================= */

export type ConceptDetail = ConceptFormData & {
  id_concept: string;

  created_at?: string | null;

  updated_at?: string | null;
};
