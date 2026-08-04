// frontend/types/knowledge.ts

/* ===========================================================
   TYPES
=========================================================== */

export type KnowledgeEntityType =
  | "company"
  | "topic"
  | "solution";

export type KnowledgeBlockType =
  | "signal_analytique"
  | "mecanique_expliquee"
  | "enjeu_strategique"
  | "point_de_friction"
  | "chiffres";

/* ===========================================================
   REQUESTS
=========================================================== */

export type KnowledgeRequest = {

  entity_type: KnowledgeEntityType;

  entity_id: string;

};

export type KnowledgeBlockUpdateRequest = {

  entity_type: KnowledgeEntityType;

  entity_id: string;

  block_type: KnowledgeBlockType;

  content: string;

};

/* ===========================================================
   KNOWLEDGE
=========================================================== */

export type KnowledgeBlock = {

  block_type: KnowledgeBlockType;

  content: string;

  version: number;

  updated_at: string;

};

export type KnowledgeEntity = {

  entity_type: KnowledgeEntityType;

  entity_id: string;

  signal_analytique: KnowledgeBlock;

  mecanique_expliquee: KnowledgeBlock;

  enjeu_strategique: KnowledgeBlock;

  point_de_friction: KnowledgeBlock;

  chiffres: KnowledgeBlock;

  updated_at: string;

};

/* ===========================================================
   COCKPIT
=========================================================== */

export type KnowledgeEntitySummary = {

  entity_type: KnowledgeEntityType;

  entity_id: string;

  name: string;

  contents_count: number;

  users_count: number;

  experts_count: number;

  has_knowledge: boolean;

  last_build: string | null;

};

export type KnowledgeExplorer = {

  entities: KnowledgeEntitySummary[];

};

export type KnowledgeDashboard = {

  companies: number;

  topics: number;

  solutions: number;

  entities: number;

  knowledge_built: number;

  users: number;

  experts: number;

};
