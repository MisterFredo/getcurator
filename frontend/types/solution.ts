// frontend/types/solution.ts

/* ========================================================= */

export type SolutionOption = {
  id_solution: string;
  name: string;
};

/* ========================================================= */

export type SolutionAlias = {
  alias: string;
};

/* ========================================================= */

export type SolutionFormData = {

  name: string;

  id_company: string;

  description: string;

  content: string;

  aliases: SolutionAlias[];

};

/* ========================================================= */

export const EMPTY_SOLUTION: SolutionFormData = {

  name: "",

  id_company: "",

  description: "",

  content: "",

  aliases: [],

};

/* ========================================================= */

export type SolutionDetail = SolutionFormData & {

  id_solution: string;

  media_logo_rectangle_id: string | null;

  created_at?: string | null;

  updated_at?: string | null;

};
