export type DigestHistoryItem = {
  ID: string;

  CAMPAIGN_ID: string;

  USER_ID: string;

  STATUS: string;

  TOTAL_CONTENTS?: number | null;

  ANALYZED_CONTENTS?: number | null;

  GENERATED_AT?: string | null;

  SENT_AT?: string | null;

  FREQUENCY?: string | null;

  AUDIENCE?: string | null;

  PERIOD_START?: string | null;

  PERIOD_END?: string | null;

  NAME?: string | null;

  DISPLAY_NAME?: string | null;

  COMPANY?: string | null;

  DESCRIPTION?: string | null;

  PROFILE_TYPE?: string | null;
};
