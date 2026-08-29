import {
  api,
} from "@/lib/api";

import type {
  Campaign,
  CampaignDetail,
  CampaignCreateRequest,
  Digest,
  DigestBootstrapResult,
  DigestBulkBootstrapResult,
  DigestBulkGenerationResult,
  AdminDigestSearchFilters,
  AdminDigestSearchResponse,
} from "@/types/digest";


/* =========================================================
   CAMPAIGNS
========================================================= */

export async function listCampaigns():
  Promise<Campaign[]> {

  const res =
    await api.get(
      "/digest/campaigns",
    );

  return res.campaigns;

}


/* ========================================================= */

export async function getCampaign(
  id: string,
): Promise<CampaignDetail> {

  const res =
    await api.get(
      `/digest/campaigns/${id}`,
    );

  return res.campaign;

}


/* ========================================================= */

export async function createCampaign(
  request: CampaignCreateRequest,
): Promise<Campaign> {

  const res =
    await api.post(
      "/digest/campaigns",
      request,
    );

  return res.campaign;

}


/* ========================================================= */

export async function generateCampaign(
  id: string,
): Promise<Campaign> {

  const res =
    await api.post(
      `/digest/campaigns/${id}/generate`,
      {},
    );

  return res.campaign;

}


/* ========================================================= */

export async function sendCampaign(
  id: string,
): Promise<Campaign> {

  const res =
    await api.post(
      `/digest/campaigns/${id}/send`,
      {},
    );

  return res.campaign;

}


/* =========================================================
   BULK CAMPAIGN GENERATION
========================================================= */

export async function generateAllDigests():
  Promise<DigestBulkGenerationResult> {

  return api.post(
    "/digest/campaigns/generate-all",
    {},
  );

}


/* =========================================================
   PROFILE BOOTSTRAP
========================================================= */

export async function bootstrapProfileDigests(
  userId: string,
): Promise<DigestBootstrapResult> {

  return api.post(
    `/digest/bootstrap/${userId}`,
    {},
  );

}


/* =========================================================
   BULK BOOTSTRAP
========================================================= */

export async function bootstrapAllProfiles():
  Promise<DigestBulkBootstrapResult> {

  return api.post(
    "/digest/bootstrap-all",
    {},
  );

}


/* =========================================================
   ADMIN DIGEST SEARCH
========================================================= */

export async function searchAdminDigests(
  filters: AdminDigestSearchFilters = {},
): Promise<AdminDigestSearchResponse> {

  const params =
    new URLSearchParams();

  if (filters.query?.trim()) {

    params.set(
      "query",
      filters.query.trim(),
    );

  }

  if (filters.audience) {

    params.set(
      "audience",
      filters.audience,
    );

  }

  if (filters.status) {

    params.set(
      "status",
      filters.status,
    );

  }

  if (filters.campaign_id) {

    params.set(
      "campaign_id",
      filters.campaign_id,
    );

  }

  if (filters.period_start) {

    params.set(
      "period_start",
      filters.period_start,
    );

  }

  if (filters.period_end) {

    params.set(
      "period_end",
      filters.period_end,
    );

  }

  params.set(
    "limit",
    String(
      filters.limit ?? 50,
    ),
  );

  params.set(
    "offset",
    String(
      filters.offset ?? 0,
    ),
  );

  const query =
    params.toString();

  const res =
    await api.get(
      `/digest/admin/digests?${query}`,
    );

  return {

    items:
      res.items ?? [],

    total:
      res.total ?? 0,

    limit:
      res.limit
      ?? filters.limit
      ?? 50,

    offset:
      res.offset
      ?? filters.offset
      ?? 0,

  };

}


/* =========================================================
   GET DIGEST
========================================================= */

export async function getDigest(
  id: string,
): Promise<Digest> {

  const res =
    await api.get(
      `/digest/digests/${id}`,
    );

  return res.digest;

}


/* =========================================================
   GENERATE DIGEST
========================================================= */

export async function generateDigest(
  id: string,
): Promise<Digest> {

  const res =
    await api.post(
      `/digest/digests/${id}/generate`,
      {},
    );

  return res.digest;

}


/* =========================================================
   SEND DIGEST
========================================================= */

export async function sendDigest(
  id: string,
): Promise<Digest> {

  const res =
    await api.post(
      `/digest/digests/${id}/send`,
      {},
    );

  return res.digest;

}


/* =========================================================
   DELETE DIGEST
========================================================= */

export async function deleteDigest(
  id: string,
): Promise<void> {

  await api.delete(
    `/digest/digests/${id}`,
  );

}
