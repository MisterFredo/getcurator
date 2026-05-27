// frontend/components/delivery/email/buildEmail.ts

import type {
  NewsletterNewsItem,
  HeaderConfig,
} from "@/types/newsletter";

import { EmailLayout } from "./EmailLayout";

import { EmailHeader } from "./EmailHeader";

import { EmailNewsBlock } from "./EmailNewsBlock";

import { EmailBrevesBlock } from "./EmailBrevesBlock";

import { EmailEditorialBlock } from "./EmailEditorialBlock";

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

export function buildEmail({
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
