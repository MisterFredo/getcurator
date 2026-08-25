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
   DIGEST
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
