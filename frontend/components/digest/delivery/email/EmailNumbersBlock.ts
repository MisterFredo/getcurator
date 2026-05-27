import type { NewsletterNumberItem } from "@/types/newsletter";
import { escapeHtml } from "./EmailHelpers";

/* =========================================================
   FORMAT VALUE
========================================================= */

function formatValue(n: NewsletterNumberItem) {
  if (n.value === undefined || n.value === null) return "";

  const scaleMap: any = {
    thousand: "K",
    million: "M",
    millions: "M",
    billion: "Md",
    billions: "Md",
  };

  const scale = scaleMap[n.scale || ""] || "";
  const unit = n.unit || "";

  return [n.value, scale, unit]
    .filter(Boolean)
    .join(" ");
}

export function EmailNumbersBlock(numbers: NewsletterNumberItem[]) {
  if (!numbers.length) return "";

  const rows = [];
  for (let i = 0; i < numbers.length; i += 2) {
    rows.push(numbers.slice(i, i + 2));
  }

  return `
<tr>
<td style="
  padding-top:28px;
  font-family:Arial,Helvetica,sans-serif;
">
  <div style="
    font-size:11px;
    font-weight:600;
    letter-spacing:0.14em;
    text-transform:uppercase;
    color:#9CA3AF;
    margin-bottom:10px;
  ">
    Chiffres clés
  </div>
</td>
</tr>

${rows
  .map(
    (pair, index) => `
<tr>
<td style="
  padding:12px 0;
  border-bottom:${index === rows.length - 1 ? "none" : "1px solid #F3F4F6"};
">

<table width="100%" cellpadding="0" cellspacing="0">
<tr>

${pair
  .map(
    (n) => `
<td width="50%" valign="top" style="padding-right:12px;">

  <div style="
    font-size:16px;
    font-weight:700;
    color:#111827;
    margin-bottom:2px;
  ">
    ${formatValue(n)}
  </div>

  <div style="
    font-size:13px;
    color:#374151;
    line-height:1.3;
  ">
    ${escapeHtml(n.label)}
  </div>

  ${
    n.entity
      ? `<div style="
          font-size:11px;
          color:#9CA3AF;
          margin-top:2px;
        ">
          ${escapeHtml(n.entity.label)}
        </div>`
      : ""
  }

</td>
`
  )
  .join("")}

${pair.length === 1 ? `<td width="50%"></td>` : ""}

</tr>
</table>

</td>
</tr>
`
  )
  .join("")}
`;
}
