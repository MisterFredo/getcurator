import type {
  DigestContentItem,
} from "@/types/digest";

import {
  escapeHtml,
  formatDate,
} from "@/components/delivery/email/EmailHelpers";

/* ========================================================= */

const GCS_BASE_URL =
  process.env
    .NEXT_PUBLIC_GCS_BASE_URL || "";

/* =========================================================
   CURATOR BADGE STYLES
========================================================= */

const BADGE_STYLES = {

  company: {
    bg: "#F0F7FF",
    text: "#3B82F6",
    border: "#E0ECFF",
  },

  solution: {
    bg: "#FAF5FF",
    text: "#9333EA",
    border: "#E9D5FF",
  },

  universe: {
    bg: "#F0FDF4",
    text: "#059669",
    border: "#DCFCE7",
  },

  topic: {
    bg: "#F5F5F5",
    text: "#6B7280",
    border: "#E5E7EB",
  },

  concept: {
    bg: "#FAF5FF",
    text: "#7C3AED",
    border: "#E9D5FF",
  },
};

/* =========================================================
   BADGES
========================================================= */

function renderBadges(
  items: any[],
  type:
    | "company"
    | "solution"
    | "universe"
    | "topic"
    | "concept",
) {

  if (!items?.length) {
    return "";
  }

  const style =
    BADGE_STYLES[type];

  return items
    .slice(0, 6)
    .map((item) => {

      const label =
        item?.label ||
        item?.name ||
        "";

      if (!label) {
        return "";
      }

      return `
<span style="
  display:inline-block;
  padding:3px 8px;
  margin-right:6px;
  margin-bottom:6px;
  border-radius:999px;

  background:${style.bg};
  color:${style.text};
  border:1px solid ${style.border};

  font-size:10px;
  line-height:1.2;
  font-weight:500;
  letter-spacing:0.04em;
  text-transform:uppercase;

  font-family:Arial,Helvetica,sans-serif;
">
  ${escapeHtml(label)}
</span>
`;
    })
    .join("");
}

/* =========================================================
   CONTENT BLOCK
========================================================= */

export function EmailContentBlock(
  contents: DigestContentItem[]
) {

  if (!contents.length) {
    return "";
  }

  return `

${contents.map((content) => {

  const logoUrl =
    content.primary_company_logo
      ? `${GCS_BASE_URL}/${content.primary_company_logo}`
      : null;

  return `
<tr>
<td style="
  padding:28px 0;
  border-bottom:1px solid #F3F4F6;
  font-family:Arial,Helvetica,sans-serif;
">

  ${
    logoUrl
      ? `
<div style="margin-bottom:16px;">

  <img
    src="${logoUrl}"
    alt=""
    style="
      max-height:26px;
      max-width:140px;
      display:block;
    "
  />

</div>
`
      : ""
  }

  <div style="
    font-size:22px;
    line-height:1.3;
    font-weight:700;
    color:#111827;
    margin-bottom:8px;
  ">

    <a
      href="${content.url || "#"}"
      target="_blank"
      style="
        color:#111827;
        text-decoration:none;
      "
    >
      ${escapeHtml(content.title)}
    </a>

  </div>

  ${
    content.published_at
      ? `
<div style="
  font-size:12px;
  color:#9CA3AF;
  margin-bottom:14px;
  letter-spacing:0.02em;
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
  font-size:15px;
  line-height:1.75;
  color:#374151;
  margin-bottom:18px;
">
  ${escapeHtml(content.excerpt)}
</div>
`
      : ""
  }

  <div>

    ${renderBadges(
      content.companies,
      "company"
    )}

    ${renderBadges(
      content.solutions,
      "solution"
    )}

    ${renderBadges(
      content.topics,
      "topic"
    )}

    ${renderBadges(
      content.universes,
      "universe"
    )}

    ${renderBadges(
      content.concepts,
      "concept"
    )}

  </div>

</td>
</tr>
`;
}).join("")}
`;
}
