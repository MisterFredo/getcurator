// frontend/types/digest.ts

/* =========================================================
   REQUEST
========================================================= */

export type DigestRequest = {

  user_id: string;

  period_start: string;

  period_end: string;

  capabilities: string[];

  limit: number;

};

/* =========================================================
   BATCH
========================================================= */

export type DigestBatch = {

  id: string;

  frequency:
    | "weekly"
    | "monthly";

  audience:
    | "user"
    | "expert";

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

  selected_contents: number;

  generated_at?: string | null;

  sent_at?: string | null;

  error?: string | null;

};

/* =========================================================
   DOCUMENT
========================================================= */

export type DigestDocument = {

  title: string;

  subtitle?: string;

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

  cards: DigestCard[];

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

  request: DigestRequest;

  total_contents: number;

  analyzed_contents: number;

  created_at: string;

  document: DigestDocument;

};

/* =========================================================
   BATCH DETAIL
========================================================= */

export type DigestBatchDetail = {

  batch: DigestBatch;

  items: DigestBatchItem[];

};
