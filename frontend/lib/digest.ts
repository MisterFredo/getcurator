import { api } from "@/lib/api";

import type {
  Campaign,
  CampaignDetail,
  CampaignCreateRequest,
  Digest,
} from "@/types/digest";

/* =========================================================
   CAMPAIGNS
========================================================= */

export async function listCampaigns(): Promise<Campaign[]> {

  const res =
    await api.get("/campaigns");

  return res.campaigns;

}

export async function getCampaign(
  id: string,
): Promise<CampaignDetail> {

  const res =
    await api.get(`/campaigns/${id}`);

  return res;

}

export async function createCampaign(
  request: CampaignCreateRequest,
): Promise<Campaign> {

  const res =
    await api.post(
      "/campaigns",
      request,
    );

  return res.campaign;

}

export async function generateCampaign(
  id: string,
): Promise<void> {

  await api.post(
    `/campaigns/${id}/generate`,
    {},
  );

}

export async function sendCampaign(
  id: string,
): Promise<void> {

  await api.post(
    `/campaigns/${id}/send`,
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
      `/digests/${id}`,
    );

  return res.digest;

}
