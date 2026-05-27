import type { TopicStat } from "@/types/newsletter";
import { escapeHtml } from "./EmailHelpers";

export function EmailStatsBlock(topicStats: TopicStat[]) {
  if (!topicStats?.length) return "";

  const half = Math.ceil(topicStats.length / 2);
  const left = topicStats.slice(0, half);
  const right = topicStats.slice(half);

  function renderColumn(items: TopicStat[]) {
    return items
      .map(
        (t) => `
<tr>
  <td style="
      padding:6px 0;
      font-size:14px;
      font-family:Arial,Helvetica,sans-serif;
      line-height:1.5;
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
        font-weight:400;
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
  }

  return `
<tr>
<td style="
    padding:32px 0;
    border-top:1px solid #F1F5F9;
    border-bottom:1px solid #F1F5F9;
    font-family:Arial,Helvetica,sans-serif;
  ">

  <!-- CARD -->
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
    <tr>
      <td style="
          background:#F8FAFC;
          padding:20px 18px;
        ">

        <!-- LABEL -->
        <div style="
            font-size:11px;
            font-weight:600;
            letter-spacing:0.16em;
            text-transform:uppercase;
            color:#94A3B8;
            margin-bottom:6px;
          ">
          Baromètre
        </div>

        <!-- TITLE -->
        <div style="
            font-size:17px;
            font-weight:600;
            color:#111827;
            margin-bottom:16px;
          ">
          Les sujets les plus actifs — 30 derniers jours
        </div>

        <!-- COLUMNS -->
        <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
          <tr>

            <!-- LEFT -->
            <td valign="top" style="
                width:50%;
                padding-right:12px;
              ">
              <table width="100%" cellpadding="0" cellspacing="0">
                ${renderColumn(left)}
              </table>
            </td>

            <!-- RIGHT -->
            <td valign="top" style="
                width:50%;
              ">
              <table width="100%" cellpadding="0" cellspacing="0">
                ${renderColumn(right)}
              </table>
            </td>

          </tr>
        </table>

      </td>
    </tr>
  </table>

</td>
</tr>
`;
}
