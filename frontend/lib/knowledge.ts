import { api } from "@/lib/api";

import type {
  KnowledgeEntity,
  KnowledgeRequest,
  KnowledgeBlockUpdateRequest,
} from "@/types/knowledge";

/* =========================================================
   BUILD
========================================================= */

export async function buildKnowledge(
  request: KnowledgeRequest,
) {

  return api.post(
    "/api/knowledge/build",
    request,
  );

}

/* =========================================================
   GET
========================================================= */

export async function getKnowledge(
  entityType: string,
  entityId: string,
): Promise<KnowledgeEntity | null> {

  const res =
    await api.get(
      `/api/knowledge/${entityType}/${entityId}`,
    );

  return (
    res.knowledge ??
    null
  );

}

/* =========================================================
   UPDATE
========================================================= */

export async function updateKnowledge(
  request: KnowledgeRequest,
) {

  return api.post(
    "/api/knowledge/update",
    request,
  );

}

/* =========================================================
   UPDATE BLOCK
========================================================= */

export async function updateKnowledgeBlock(
  request: KnowledgeBlockUpdateRequest,
) {

  const res =
    await api.put(
      "/api/knowledge/block",
      request,
    );

  return (
    res.block ??
    null
  );

}
