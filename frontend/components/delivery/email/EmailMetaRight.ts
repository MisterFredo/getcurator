import { escapeHtml } from "./EmailHelpers";

export function EmailMetaRight(
  topics?: any[],
  company?: any,
  type?: string
) {

  const topicBadges =
    topics?.map(
      (t) => `
<span style="
  display:inline-block;
  font-size:11px;
  padding:4px 8px;
  margin:0 0 6px 0;
  border:1px solid #E5E7EB;
  border-radius:3px;
  background:#F9FAFB;
  color:#374151;">
  ${escapeHtml(t.LABEL || t.label || "")}
</span>`
    ).join("") || "";

  const companyBadge = company
    ? `
<span style="
  display:inline-block;
  font-size:11px;
  padding:4px 8px;
  margin-bottom:6px;
  border:1px solid #E5E7EB;
  border-radius:3px;
  background:#F3F4F6;
  color:#111827;">
  ${escapeHtml(company.name)}
</span>`
    : "";

  const typeBadge = type
    ? `
<span style="
  display:inline-block;
  font-size:11px;
  padding:4px 8px;
  margin-bottom:6px;
  border:1px solid #111827;
  border-radius:3px;
  color:#111827;">
  ${escapeHtml(type)}
</span>`
    : "";

  return `
<td valign="top"
    width="160"
    style="padding-left:18px;
           font-family:Arial,Helvetica,sans-serif;
           vertical-align:top;">
  ${typeBadge}
  ${companyBadge}
  ${topicBadges}
</td>`;
}
