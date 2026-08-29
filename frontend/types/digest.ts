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
   DIGEST STATUS
========================================================= */

export type DigestStatus =
  | "created"
  | "generating"
  | "generated"
  | "sending"
  | "sent"
  | "failed";


/* =========================================================
   AVAILABLE DIGEST STATUS
========================================================= */

export type AvailableDigestStatus =
  | "generated"
  | "sent";


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

  status: DigestStatus;

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

  id: string;

  campaign_id: string;

  user_id: string;

  status: AvailableDigestStatus;

  total_contents: number;

  analyzed_contents: number;

  generated_at?: string | null;

  sent_at?: string | null;

  audience: DigestAudience;

  period_start: string;

  period_end: string;

  name?: string | null;

  display_name?: string | null;

  email?: string | null;

  company?: string | null;

  description?: string | null;

  profile_type?: string | null;

};


/* =========================================================
   ADMIN DIGEST SEARCH FILTERS
========================================================= */

export type AdminDigestSearchFilters = {

  query?: string;

  audience?: DigestAudience;

  status?: AvailableDigestStatus;

  campaign_id?: string;

  period_start?: string;

  period_end?: string;

  limit?: number;

  offset?: number;

};


/* =========================================================
   ADMIN DIGEST SEARCH RESPONSE
========================================================= */

export type AdminDigestSearchResponse = {

  items: DigestHistoryItem[];

  total: number;

  limit: number;

  offset: number;

};


/* =========================================================
   PROFILE BOOTSTRAP RESULT
========================================================= */

export type DigestBootstrapResult = {

  status:
    | "completed"
    | "partial"
    | "failed"
    | "not_eligible";

  user_id: string;

  audience: DigestAudience;

  created_count: number;

  generated_count: number;

  skipped_count: number;

  failed_count: number;

};


/* =========================================================
   BULK BOOTSTRAP RESULT
========================================================= */

export type DigestBulkBootstrapResult = {

  status:
    | "completed"
    | "partial"
    | "failed"
    | "not_eligible";

  profiles_count: number;

  processed_count: number;

  created_count: number;

  generated_count: number;

  skipped_count: number;

  failed_count: number;

};


/* =========================================================
   BULK GENERATION RESULT
========================================================= */

export type DigestBulkGenerationResult = {

  status:
    | "completed"
    | "partial"
    | "failed";

  campaigns_count: number;

  digests_count: number;

  generated_count: number;

  failed_count: number;

};
