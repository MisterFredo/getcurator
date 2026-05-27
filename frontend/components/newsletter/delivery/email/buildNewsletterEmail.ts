// frontend/components/newsletter/delivery/email/buildNewsletterEmail.ts

import type {
  NewsletterNewsItem,
  HeaderConfig,
} from "@/types/newsletter";

import { EmailLayout } from "@/components/delivery/email/EmailLayout";

import { EmailHeader } from "@/components/delivery/email/EmailHeader";

import { EmailEditorialBlock } from "@/components/delivery/email/EmailEditorialBlock";

import { EmailNewsBlock } from "./EmailNewsBlock";

import { EmailBrevesBlock } from "./EmailBrevesBlock";

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

export function buildNewsletterEmail({
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

    EmailHeader(
      headerConfig
    ),

    /* ===================================================
       EDITORIAL
    =================================================== */

    editorial.trim()
      ? EmailEditorialBlock(
          editorial
        )
      : "",

    /* ===================================================
       NEWS
    =================================================== */

    news.length > 0
      ? EmailNewsBlock(
          news
        )
      : "",

    /* ===================================================
       BRÈVES
    =================================================== */

    breves.length > 0
      ? EmailBrevesBlock(
          breves
        )
      : "",

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

  return EmailLayout(
    content
  );
}
