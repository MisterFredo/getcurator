// frontend/types/topic.ts

/* =========================================================
   UNIVERSE
========================================================= */

export type Universe = {

  id_universe: string;

  label: string;

};


/* =========================================================
   TOPIC FORM
========================================================= */

export type TopicFormData = {

  label: string;

  description: string;

  universes: string[];

};


/* =========================================================
   TOPIC OPTION
========================================================= */

export type TopicOption = {

  id_topic: string;

  label: string;

};


/* =========================================================
   EMPTY TOPIC
========================================================= */

export const EMPTY_TOPIC: TopicFormData = {

  label: "",

  description: "",

  universes: [],

};


/* =========================================================
   TOPIC DETAIL
========================================================= */

export type TopicDetail =
  TopicFormData & {

    id_topic: string;

    is_active?: boolean;

    created_at?: string | null;

    updated_at?: string | null;

  };
