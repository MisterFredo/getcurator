// frontend/components/newsletter/delivery/email/buildNewsletterEmailGmail.ts

import type {
  NewsletterNewsItem,
  HeaderConfig,
} from "@/types/newsletter";

import { EmailLayoutGmail } from "@/components/delivery/email/EmailLayoutGmail";

import { EmailHeaderGmail } from "@/components/delivery/email/EmailHeaderGmail";

import { EmailEditorialBlockGmail } from "@/components/delivery/email/EmailEditorialBlockGmail";

import { EmailSignatureGmail } from "@/components/delivery/email/EmailSignatureGmail";

import { EmailNewsBlockGmail } from "./EmailNewsBlockGmail";

import { EmailBrevesBlockGmail } from "./EmailBrevesBlockGmail";

/* ========================================================= */

type Props = {
  headerConfig: HeaderConfig;

  /* =======================================================
     EDITORIAL
  ======================================================= */

  editorialHtml?: string;

  /* fallback legacy */
  introText?: string;

  /* =======================================================
     CONTENT
  ======================================================= */

  news: NewsletterNewsItem[];

  breves: NewsletterNewsItem[];
};

/* ========================================================= */

export function buildNewsletterEmailGmail({
  headerConfig,

  editorialHtml,

  introText,

  news,

  breves,
}: Props) {

  /* =======================================================
     SOURCE UNIQUE ÉDITORIALE
  ======================================================= */

  const editorial =
    editorialHtml ||
    introText ||
    "";

  /* =======================================================
     BLOCKS
  ======================================================= */

  const blocks = [

    /* ===================================================
       HEADER
    =================================================== */

    EmailHeaderGmail(
      headerConfig
    ),

    /* ===================================================
       EDITORIAL
    =================================================== */

    editorial.trim()
      ? EmailEditorialBlockGmail(
          editorial
        )
      : "",

    /* ===================================================
       NEWS
    =================================================== */

    news.length > 0
      ? EmailNewsBlockGmail(
          news
        )
      : "",

    /* ===================================================
       BRÈVES
    =================================================== */

    breves.length > 0
      ? EmailBrevesBlockGmail(
          breves
        )
      : "",

    /* ===================================================
       SIGNATURE
    =================================================== */

    EmailSignatureGmail(),

  ].join("");

  /* =======================================================
     FINAL HTML
  ======================================================= */

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
