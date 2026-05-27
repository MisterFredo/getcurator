import type { NewsletterAnalysisItem } from "@/types/newsletter";
import {
  escapeHtml,
  formatDate,
  renderEmailTags,
} from "./EmailHelpers";

/* =========================================================
   SECTION TITLE
========================================================= */

function renderSectionTitle(label: string) {
  return `
<tr>
<td style="
  padding:32px 0 12px 0;
  font-family:Arial,Helvetica,sans-serif;
">
  <div style="
    font-size:12px;
    font-weight:600;
    text-transform:uppercase;
    letter-spacing:0.12em;
    color:#6B7280;
  ">
    ${label}
  </div>
</td>
</tr>
`;
}

/* =========================================================
   ANALYSES BLOCK
========================================================= */

export function EmailAnalysesBlock(
  analyses: NewsletterAnalysisItem[]
) {
  if (!analyses.length) return "";

  const rows = analyses
    .map((a) => {

      // ✅ URL → CURATOR (pas de fallback)
      const url = `https://www.getcurator.ai/feed?analysis_id=${a.id}`;

      const tags = renderEmailTags({
        topics: a.topics,
        companies: a.company ? [a.company] : [],
        styles: ["ANALYSE"],
      });

      return `
<tr>
<td style="
  padding:24px 0;
  border-bottom:1px solid #E5E7EB;
  font-family:Arial,Helvetica,sans-serif;
">

  <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
    <tr>
      <td valign="top">

        <!-- DATE -->
        <div style="
          font-size:12px;
          color:#6B7280;
          margin-bottom:6px;
        ">
          ${formatDate(a.published_at)}
        </div>

        <!-- TITLE -->
        <a href="${url}" target="_blank" style="text-decoration:none;">
          <div style="
            font-size:16px;
            font-weight:600;
            color:#111827;
            line-height:1.3;
            margin-bottom:6px;
          ">
            ${escapeHtml(a.title)}
          </div>
        </a>

        ${
          tags
            ? `
        <div style="margin-bottom:6px;">
          ${tags}
        </div>
        `
            : ""
        }

        ${
          a.excerpt
            ? `
        <div style="
          font-size:14px;
          color:#6B7280;
          line-height:1.4;
          margin-bottom:8px;
        ">
          ${escapeHtml(a.excerpt)}
        </div>
        `
            : ""
        }

        <!-- CTA -->
        <a href="${url}" target="_blank" style="
          font-size:13px;
          font-weight:600;
          color:#111827;
          text-decoration:none;
          border-bottom:1px solid #111827;
        ">
          Lire l’analyse →
        </a>

      </td>
    </tr>
  </table>

</td>
</tr>
`;
    })
    .join("");

  return renderSectionTitle("Analyses") + rows;
}
