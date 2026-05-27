import type { TopicStat } from "@/types/newsletter";
import { escapeHtml } from "./EmailHelpers";

export function EmailStatsBlockGmail(
  topicStats: TopicStat[]
) {
  if (!topicStats?.length) return "";

  const rows = topicStats
    .map(
      (t) => `
<tr>
  <td style="
      padding:6px 0;
      font-size:14px;
      line-height:1.5;
      font-family:Arial,Helvetica,sans-serif;
      color:#1F2937;
    ">
    <span style="font-weight:500;">
      ${escapeHtml(t.label)}
    </span>
    <span style="
        font-weight:600;
        margin-left:6px;
      ">
      ${t.last_30_days}
    </span>
    <span style="
        color:#9CA3AF;
        margin-left:6px;
        font-size:13px;
      ">
      (${t.total})
    </span>
  </td>
</tr>
`
    )
    .join("");

  return `
<tr>
<td style="
    padding:28px 16px 32px 16px;
    font-family:Arial,Helvetica,sans-serif;
  ">

  <!-- CONTAINER -->
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
    
    <!-- TITLE -->
    <tr>
      <td style="
          font-size:13px;
          font-weight:700;
          letter-spacing:0.08em;
          text-transform:uppercase;
          color:#111827;
          padding-bottom:14px;
        ">
        Baromètre
      </td>
    </tr>

    <!-- SUBTITLE -->
    <tr>
      <td style="
          font-size:15px;
          color:#374151;
          padding-bottom:16px;
        ">
        Les sujets les plus actifs — 30 derniers jours
      </td>
    </tr>

    ${rows}

  </table>

</td>
</tr>
`;
}
