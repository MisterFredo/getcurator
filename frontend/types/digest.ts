// frontend/types/digest.ts

/* =========================================================
   BATCH
========================================================= */

export type DigestBatch = {

  id: string;

  frequency:
    | "WEEKLY"
    | "MONTHLY";

  audience:
    | "USER"
    | "EXPERT";

  period_start: string;

  period_end: string;

  status:
    | "created"
    | "prepared"
    | "generating"
    | "generated"
    | "sending"
    | "completed"
    | "failed";

  items_count: number;

  generated_count: number;

  sent_count: number;

  failed_count: number;

  created_at: string;

  completed_at?: string | null;

};

/* =========================================================
   BATCH ITEM
========================================================= */

export type DigestBatchItem = {

  id: string;

  batch_id: string;

  user_id: string;

  review_id?: string | null;

  status:
    | "pending"
    | "generating"
    | "generated"
    | "sending"
    | "sent"
    | "failed";

  generated_at?: string | null;

  sent_at?: string | null;

  error?: string | null;

};

/* =========================================================
   DOCUMENT
========================================================= */

export type DigestDocument = {

  title: string;

  period: string;

  sections: DigestSection[];

};

/* =========================================================
   SECTION
========================================================= */

export type DigestSection = {

  id: string;

  title: string;

  body: string;

  cards?: DigestCard[];

};

/* =========================================================
   CARD
========================================================= */

export type DigestCard = {

  id: string;

  title: string;

  excerpt: string;

  url: string;

  source_title?: string;

  published_at?: string;

  company_logo?: string | null;

};

/* =========================================================
   REVIEW
========================================================= */

export type DigestReview = {

  id: string;

  user_id: string;

  total_contents: number;

  analyzed_contents: number;

  created_at: string;

  document: DigestDocument;

};
