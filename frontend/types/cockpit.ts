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

  english_source_ready: number;

  english_source_missing: number;

  title_fr_done: number;

  excerpt_fr_done: number;

  content_body_fr_done: number;

  signal_fr_done: number;

  mecanique_fr_done: number;

  enjeu_fr_done: number;

  friction_fr_done: number;

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

  [key: string]:
    unknown;

};


export type QualityResponse = {

  status: string;

  results: QualityRow[];

};
