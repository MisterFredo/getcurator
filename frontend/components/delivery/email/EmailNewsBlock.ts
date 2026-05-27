import type { NewsletterNewsItem } from "@/types/newsletter";
import {
  buildContentImageUrl,
  escapeHtml,
  renderEmailTags,
} from "./EmailHelpers";

const PUBLIC_SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ||
  "https://ratecard.fr";

export function EmailNewsBlock(news: NewsletterNewsItem[]) {
  if (!news.length) return "";

  const rows = news
    .map((n, index) => {
      const imageUrl = buildContentImageUrl(n.visual_rect_id);
      const newsUrl = `${PUBLIC_SITE_URL}/news?news_id=${n.id}`;

      const tags = renderEmailTags({
        topics: n.topics,
        companies: n.company ? [n.company] : [],
        styles: n.news_type ? [n.news_type] : [],
      });

      return `
<tr>
<td style="
  padding:18px 0;
  border-bottom:${index === news.length - 1 ? "none" : "1px solid #F3F4F6"};
">

  <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
    <tr>

      ${
        imageUrl
          ? `
      <!-- MINI THUMB (identique brèves) -->
      <td
        width="64"
        valign="top"
        style="
          width:64px;
          padding-right:12px;
        "
      >
        <a href="${newsUrl}" target="_blank">
          <img 
            src="${imageUrl}"
            alt=""
            width="56"
            border="0"
            style="
              display:block;
              width:56px;
              height:auto;
              border-radius:6px;
            "
          />
        </a>
      </td>
      `
          : ""
      }

      <!-- TEXT -->
      <td valign="top">

        <!-- DATE -->
        <div style="
          font-size:12px;
          color:#6B7280;
          margin-bottom:4px;
        ">
          ${new Date(n.published_at).toLocaleDateString("fr-FR")}
        </div>

        <!-- TITLE -->
        <a href="${newsUrl}" target="_blank" style="text-decoration:none;">
          <div style="
            font-size:14px;
            font-weight:600;
            color:#111827;
            line-height:1.35;
            margin-bottom:4px;
          ">
            ${escapeHtml(n.title)}
          </div>
        </a>

        ${
          tags
            ? `
        <!-- TAGS -->
        <div style="margin-bottom:4px;">
          ${tags}
        </div>
        `
            : ""
        }

        ${
          n.excerpt
            ? `
        <!-- EXCERPT (SEULE DIFFÉRENCE AVEC BRÈVES) -->
        <div style="
          font-size:13px;
          color:#6B7280;
          line-height:1.4;
        ">
          ${escapeHtml(n.excerpt)}
        </div>
        `
            : ""
        }

      </td>

    </tr>
  </table>

</td>
</tr>
`;
    })
    .join("");

  return `
<tr>
<td style="padding-top:28px;">
  <div style="
    font-size:11px;
    font-weight:600;
    letter-spacing:0.14em;
    text-transform:uppercase;
    color:#9CA3AF;
    margin-bottom:10px;
  ">
    Actualités
  </div>
</td>
</tr>

${rows}
`;
}
