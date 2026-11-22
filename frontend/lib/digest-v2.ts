import { api } from "@/lib/api";

export const digestV2Endpoint = "/digest/admin/subject-digests";
export type DigestRecipient = { id: string; name: string; company?: string };
export type DigestBatchResult = {
  processed_count: number;
  generated_count: number;
  skipped_count: number;
  failed_count: number;
  errors: string[];
};

export function previousDigestMonday() {
  const today = new Intl.DateTimeFormat("fr-CA", { timeZone: "Europe/Paris" }).format(new Date());
  const date = new Date(today + "T12:00:00Z");
  date.setUTCDate(date.getUTCDate() - (date.getUTCDay() + 6) % 7 - 7);
  return date.toISOString().slice(0, 10);
}

export async function generateUserDigestsV2(
  periodStart = previousDigestMonday(),
  onProgress?: (message: string) => void,
): Promise<DigestBatchResult> {
  const response = await api.get(digestV2Endpoint + "/recipients?audience=user");
  const recipients: DigestRecipient[] = response.recipients;
  const existing = new Set<string>();
  for (let offset = 0; ; offset += 200) {
    const page = await api.get(digestV2Endpoint + "?" + new URLSearchParams({
      period_start: periodStart, limit: "200", offset: String(offset),
    }).toString());
    for (const item of page.digests) existing.add(item.user_id);
    if (page.digests.length < 200) break;
  }
  const result: DigestBatchResult = {
    processed_count: 0, generated_count: 0, skipped_count: 0, failed_count: 0, errors: [],
  };
  const seen = new Set<string>();
  for (const recipient of recipients) {
    if (seen.has(recipient.id)) continue;
    seen.add(recipient.id);
    result.processed_count += 1;
    onProgress?.(result.processed_count + "/" + recipients.length + " · " + recipient.name);
    if (existing.has(recipient.id)) {
      result.skipped_count += 1;
      continue;
    }
    try {
      await api.post(digestV2Endpoint, { user_id: recipient.id, period_start: periodStart });
      result.generated_count += 1;
    } catch (error) {
      result.failed_count += 1;
      result.errors.push(recipient.name + " · " + (error instanceof Error ? error.message : "Échec"));
    }
  }
  return result;
}

export function digestBatchMessage(result: DigestBatchResult) {
  return result.generated_count + " générés · " + result.skipped_count
    + " déjà disponibles · " + result.failed_count + " échecs";
}
