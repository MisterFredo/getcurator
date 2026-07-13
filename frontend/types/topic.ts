// frontend/types/topic.ts

/* ========================================================= */

export type Universe = {
  id_universe: string;
  label: string;
};

/* ========================================================= */

export type TopicFormData = {
  label: string;

  description: string;

  seo_title: string;

  seo_description: string;

  universes: string[];
};

/* ========================================================= */

export const EMPTY_TOPIC: TopicFormData = {
  label: "",

  description: "",

  seo_title: "",

  seo_description: "",

  universes: [],
};

/* ========================================================= */

export type TopicDetail = TopicFormData & {
  id_topic: string;

  media_square_id: string | null;

  media_rectangle_id: string | null;

  created_at?: string | null;

  updated_at?: string | null;
};
