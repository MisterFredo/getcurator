// frontend/types/company.ts

/* ========================================================= */

export type CompanyType = {
  id_type: string;
  label: string;
};

/* ========================================================= */

export type Universe = {
  id_universe: string;
  label: string;
};

/* ========================================================= */

export type CompanyAlias = {
  alias: string;
};

/* ========================================================= */

export type CompanyFormData = {
  name: string;

  type: string;

  description: string;

  wiki_content: string;

  linkedin_url: string;

  website_url: string;

  is_partner: boolean;

  universes: string[];

  aliases: CompanyAlias[];
};

/* ========================================================= */

export const EMPTY_COMPANY: CompanyFormData = {

  name: "",

  type: "",

  description: "",

  wiki_content: "",

  linkedin_url: "",

  website_url: "",

  is_partner: false,

  universes: [],

  aliases: [],

};

/* ========================================================= */

export type CompanyDetail = CompanyFormData & {

  id_company: string;

  media_logo_rectangle_id: string | null;

  created_at?: string | null;

  updated_at?: string | null;

};

export type CompanyOption = {
  id_company: string;
  name: string;
};
