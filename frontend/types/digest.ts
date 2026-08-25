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
   AUDIENCE
========================================================= */

export type DigestAudience =
  | "user"
  | "expert";


/* =========================================================
   CAMPAIGN
========================================================= */

export type Campaign = {

  id: string;

  audience: DigestAudience;

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

  audience: DigestAudience;

};


/* =========================================================
   BADGE
========================================================= */

export type DigestBadge = {

  label: string;

  type:
    | "company"
    | "topic"
    | "solution"
    | "keyword";

};


/* =========================================================
   PROFILE
========================================================= */

export type DigestProfile = {

  name: string;

  company?: string | null;

  role?: string | null;

  description?: string | null;

  geography_1?: string | null;

  geography_2?: string | null;

  geography_3?: string | null;

  companies: DigestBadge[];

  topics: DigestBadge[];

  solutions: DigestBadge[];

  keywords: string[];

};


/* =========================================================
   CARD
========================================================= */

export type DigestCard = {

  id: string;

  title: string;

  excerpt: string;

  url: string;

  source_title?: string | null;

  published_at?: string | null;

  badges: DigestBadge[];

  matching_badges: DigestBadge[];

  company_logo?: string | null;

};


/* =========================================================
   SECTION
========================================================= */

export type DigestSection = {

  title: string;

  content: string;

  cards: DigestCard[];

};


/* =========================================================
   DOCUMENT
========================================================= */

export type DigestDocument = {

  title: string;

  subtitle?: string;

  period: string;

  created_at: string;

  audience: DigestAudience;

  profile: DigestProfile;

  sections: DigestSection[];

};


/* =========================================================
   DIGEST
========================================================= */

export type Digest = {

  id: string;

  campaign_id: string;

  user_id: string;

  user_name?: string | null;

  user_email?: string | null;

  status:
    | "created"
    | "generating"
    | "generated"
    | "sending"
    | "sent"
    | "failed";

  total_contents: number;

  analyzed_contents: number;

  knowledge?: Record<
    string,
    unknown
  > | null;

  document?: DigestDocument | null;

  generated_at?: string | null;

  sent_at?: string | null;

  error?: string | null;

};


/* =========================================================
   CAMPAIGN DETAIL
========================================================= */

export type CampaignDetail = {

  campaign: Campaign;

  digests: Digest[];

};


/* =========================================================
   DIGEST HISTORY
========================================================= */

export type DigestHistoryItem = {

  ID: string;

  CAMPAIGN_ID: string;

  USER_ID: string;

  STATUS: string;

  TOTAL_CONTENTS?: number | null;

  ANALYZED_CONTENTS?: number | null;

  GENERATED_AT?: string | null;

  SENT_AT?: string | null;

  AUDIENCE?: DigestAudience | null;

  PERIOD_START?: string | null;

  PERIOD_END?: string | null;

  NAME?: string | null;

  DISPLAY_NAME?: string | null;

  COMPANY?: string | null;

  DESCRIPTION?: string | null;

  PROFILE_TYPE?: string | null;

};
