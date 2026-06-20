// frontend/components/digest/delivery/email/buildDigestEmail.ts

import type {
  DigestContentItem,
} from "@/types/digest";

import type {
  HeaderConfig,
} from "@/types/newsletter";

import {
  EmailLayout,
} from "@/components/delivery/email/EmailLayout";

import {
  EmailHeader,
} from "@/components/delivery/email/EmailHeader";

import {
  EmailEditorialBlock,
} from "@/components/delivery/email/EmailEditorialBlock";

import {
  EmailContentBlock,
} from "./EmailContentBlock";

/* ========================================================= */

type Props = {
  headerConfig: HeaderConfig;

  editorialHtml?: string;

  introText?: string;

  summary?: string;

  implications?: string;

  contents: DigestContentItem[];
};

/* ========================================================= */

function analysisBlock(
  title: string,
  content?: string,
) {

  if (!content?.trim()) {
    return "";
  }

  return `
  <tr>
    <td
      style="
        padding:24px 32px 8px 32px;
        font-family:Arial,Helvetica,sans-serif;
        font-size:18px;
        font-weight:700;
        color:#111827;
      "
    >
      ${title}
    </td>
  </tr>

  <tr>
    <td
      style="
        padding:0 32px 24px 32px;
        font-family:Arial,Helvetica,sans-serif;
        font-size:14px;
        line-height:1.7;
        color:#374151;
        white-space:pre-wrap;
      "
    >
      ${content}
    </td>
  </tr>
  `;
}

/* ========================================================= */

export function buildDigestEmail({
  headerConfig,

  editorialHtml,

  introText,

  summary,

  implications,

  contents,

}: Props) {

  const editorial =
    editorialHtml ||
    introText ||
    "";

  const blocks = [

    EmailHeader(
      headerConfig
    ),

    editorial.trim()
      ? EmailEditorialBlock(
          editorial
        )
      : "",

    analysisBlock(
      "Weekly Summary",
      summary
    ),

    analysisBlock(
      "Key Implications",
      implications
    ),

    contents.length > 0
      ? EmailContentBlock(
          contents
        )
      : "",

  ].join("");

  const content = `
  <table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    role="presentation"
  >
    ${blocks}
  </table>
  `;

  return EmailLayout(
    content
  );
}
