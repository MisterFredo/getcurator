/* =========================================================
   MONITORING
========================================================= */

export type DestockMonitoring = {
  run_time: string;

  total: number;

  stored: number;

  processing: number;

  processed: number;

  errors: number;

  progress_pct: number;
};

/* ========================================================= */

export type TranslationMonitoring = {
  total_contents: number;

  title_en_done: number;

  excerpt_en_done: number;

  fully_translated: number;

  missing_translation: number;

  pct_fully_translated: number;
};

/* ========================================================= */

export type CockpitMonitoring = {
  destock: DestockMonitoring;

  translation: TranslationMonitoring;
};

/* =========================================================
   QUALITY
========================================================= */

export type QualityRow = {
  [key: string]: unknown;
};

export type QualityResponse = {
  status: string;

  results: QualityRow[];
};
