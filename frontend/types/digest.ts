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
   CAMPAIGN
========================================================= */

export type Campaign = {
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
    | "generating"
    | "generated"
    | "sending"
    | "completed"
    | "failed";

  digests_count: number;
  generated_count: number;
  sent_count: number;
  failed_count: number;

  created_at: string;

  completed_at?: string | null;
};

/* =========================================================
   CREATE CAMPAIGN
========================================================= */

export type CampaignCreateRequest = {
  frequency:
    | "weekly"
    | "monthly";

  audience:
    | "user"
    | "expert";

  period_start: string;
  period_end: string;
};

/* =========================================================
   DIGEST
========================================================= */

export type Digest = {
  id: string;

  campaign_id: string;

  user_id: string;

  status:
    | "pending"
    | "generating"
    | "generated"
    | "sending"
    | "sent"
    | "failed";

  total_contents: number;
  analyzed_contents: number;

  knowledge: any;

  document: DigestDocument;

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
   CAMPAIGN DETAIL
========================================================= */

export type CampaignDetail = {
  campaign: Campaign;

  digests: Digest[];
};
