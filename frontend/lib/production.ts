import {
  api,
} from "@/lib/api";

import type {
  Production,
  ProductionPrepareRequest,
  ProductionSummary,
  ProductionSavedPlan,
  ProductionPlanVersionSummary,
} from "@/types/production";


/* =========================================================
   CREATE PRODUCTION
========================================================= */

export async function createProduction(
  request: ProductionPrepareRequest,
): Promise<Production> {

  const response: {
    status: string;
    production: Production;
  } = await api.post(
    "/production/",
    request,
  );

  return response.production;

}


/* =========================================================
   LIST PRODUCTIONS
========================================================= */

export async function listProductions(
  limit: number = 20,
  offset: number = 0,
): Promise<ProductionSummary[]> {

  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  const response: {
    status: string;
    productions: ProductionSummary[];
  } = await api.get(
    `/production/?${params.toString()}`,
  );

  return response.productions;

}


/* =========================================================
   GET PRODUCTION
========================================================= */

export async function getProduction(
  productionId: string,
): Promise<Production> {

  const response: {
    status: string;
    production: Production;
  } = await api.get(
    `/production/${encodeURIComponent(productionId)}`,
  );

  return response.production;

}


/* =========================================================
   GENERATE PLAN
========================================================= */

export async function generateProductionPlan(
  productionId: string,
): Promise<ProductionSavedPlan> {

  const response: {
    status: string;
    plan: ProductionSavedPlan;
  } = await api.post(
    `/production/${encodeURIComponent(productionId)}/plan`,
    {},
  );

  return response.plan;

}


/* =========================================================
   GET LATEST OR SPECIFIC PLAN
========================================================= */

export async function getProductionPlan(
  productionId: string,
  version?: number,
): Promise<ProductionSavedPlan> {

  const params = new URLSearchParams();

  if (version !== undefined) {
    params.set(
      "version",
      String(version),
    );
  }

  const query = params.toString();

  const response: {
    status: string;
    plan: ProductionSavedPlan;
  } = await api.get(
    `/production/${encodeURIComponent(productionId)}/plan${
      query ? `?${query}` : ""
    }`,
  );

  return response.plan;

}


/* =========================================================
   LIST PLAN VERSIONS
========================================================= */

export async function listProductionPlans(
  productionId: string,
  limit: number = 20,
  offset: number = 0,
): Promise<ProductionPlanVersionSummary[]> {

  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  const response: {
    status: string;
    plans: ProductionPlanVersionSummary[];
  } = await api.get(
    `/production/${encodeURIComponent(productionId)}/plans?${params.toString()}`,
  );

  return response.plans;

}
