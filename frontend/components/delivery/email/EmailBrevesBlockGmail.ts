import type { NewsletterNewsItem } from "@/types/newsletter";
import {
  buildContentImageUrl,
  escapeHtml,
  renderEmailTags,
} from "./EmailHelpers";

const PUBLIC_SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ||
  "https://ratecard.fr";

export function EmailBrevesBlockGmail(
  breves: NewsletterNewsItem[]
) {
  if (!breves.length) return "";

  const rows = breves
    .map((b, index) => {
      const imageUrl = buildContentImageUrl(b.visual_rect_id);
      const breveUrl = `${PUBLIC_SITE_URL}/news?news_id=${b.id}`;
      const safeUrl = escapeHtml(breveUrl);

      const tags = renderEmailTags({
        topics: b.topics,
        companies: b.company ? [b.company] : [],
        styles: b.news_type ? [b.news_type] : [],
      });

      return `
<tr>
<td style="
  padding:16px 0;
  border-bottom:${index === breves.length - 1 ? "none" : "1px solid #F3F4F6"};
  font-family:Arial,Helvetica,sans-serif;
">

  <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
    <tr>

      ${
        imageUrl
          ? `
      <!-- MINI THUMB -->
      <td
        width="64"
        valign="top"
        style="
          width:64px;
          padding-right:12px;
        "
      >
        <a href="${safeUrl}" target="_blank" style="display:block;">
          <img 
            src="${imageUrl}"
            alt=""
            border="0"
            width="56"
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

        <!-- TITLE -->
        <a href="${safeUrl}" target="_blank" style="text-decoration:none;">
          <div style="
            font-size:14px;
            font-weight:600;
            color:#111827;
            line-height:1.35;
            margin-bottom:4px;
          ">
            ${escapeHtml(b.title)}
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
    Brèves
  </div>
</td>
</tr>

${rows}
`;
}
