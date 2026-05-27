// frontend/components/digest/delivery/email/EmailContentBlock.ts

import type {
  DigestContentItem,
} from "@/types/digest";

import {
  escapeHtml,
  formatDate,
} from "@/components/delivery/email/EmailHelpers";

/* ========================================================= */

export function EmailContentBlock(
  contents: DigestContentItem[]
) {

  if (!contents.length) {
    return "";
  }

  return `
<tr>
<td style="padding-top:28px;">

  <div style="
    font-size:11px;
    font-weight:600;
    letter-spacing:0.14em;
    text-transform:uppercase;
    color:#9CA3AF;
    margin-bottom:14px;
    font-family:Arial,Helvetica,sans-serif;
  ">
    Contenus
  </div>

</td>
</tr>

${contents.map((content) => `
<tr>
<td style="
  padding:16px 0;
  border-bottom:1px solid #F3F4F6;
  font-family:Arial,Helvetica,sans-serif;
">

  <div style="
    font-size:18px;
    font-weight:700;
    line-height:1.3;
    color:#111827;
    margin-bottom:6px;
  ">
    ${escapeHtml(content.title)}
  </div>

  ${
    content.published_at
      ? `
<div style="
  font-size:12px;
  color:#9CA3AF;
  margin-bottom:8px;
">
  ${formatDate(content.published_at)}
</div>
`
      : ""
  }

  ${
    content.excerpt
      ? `
<div style="
  font-size:14px;
  line-height:1.6;
  color:#374151;
">
  ${escapeHtml(content.excerpt)}
</div>
`
      : ""
  }

</td>
</tr>
`).join("")}
`;
}
