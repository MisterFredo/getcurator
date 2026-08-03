export type KnowledgeBlock = {
  block_type: string;
  content: string;
  version: number;
  updated_at: string;
};

export type KnowledgeEntity = {
  entity_type: string;
  entity_id: string;

  signal_analytique: KnowledgeBlock;
  mecanique_expliquee: KnowledgeBlock;
  enjeu_strategique: KnowledgeBlock;
  point_de_friction: KnowledgeBlock;
  chiffres: KnowledgeBlock;

  updated_at: string;
};
