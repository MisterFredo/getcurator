// frontend/components/digest/delivery/email/buildDigestEmailGmail.ts

import type {
  DigestContentItem,
} from "@/types/digest";

import type {
  HeaderConfig,
} from "@/types/newsletter";

import {
  EmailLayoutGmail,
} from "@/components/delivery/email/EmailLayoutGmail";

import {
  EmailHeaderGmail,
} from "@/components/delivery/email/EmailHeaderGmail";

import {
  EmailEditorialBlockGmail,
} from "@/components/delivery/email/EmailEditorialBlockGmail";

import {
  EmailSignatureGmail,
} from "@/components/delivery/email/EmailSignatureGmail";

import {
  EmailContentBlockGmail,
} from "./EmailContentBlockGmail";


/* ========================================================= */

type Props = {
  headerConfig: HeaderConfig;

  editorialHtml?: string;

  introText?: string;

  contents: DigestContentItem[];
};

/* ========================================================= */

export function buildDigestEmailGmail({
  headerConfig,

  editorialHtml,

  introText,

  contents,
}: Props) {

  const editorial =
    editorialHtml ||
    introText ||
    "";

  const blocks = [

    EmailHeaderGmail(
      headerConfig
    ),

    editorial.trim()
      ? EmailEditorialBlockGmail(
          editorial
        )
      : "",

    contents.length > 0
      ? EmailContentBlockGmail(
          contents
        )
      : "",

    EmailSignatureGmail(),

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

  return EmailLayoutGmail(
    content
  );
}
