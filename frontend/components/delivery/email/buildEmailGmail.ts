// frontend/components/delivery/email/buildEmailGmail.ts

import type {
  NewsletterNewsItem,
  HeaderConfig,
} from "@/types/newsletter";

import { EmailLayoutGmail } from "./EmailLayoutGmail";

import { EmailHeaderGmail } from "./EmailHeaderGmail";

import { EmailNewsBlockGmail } from "./EmailNewsBlockGmail";

import { EmailBrevesBlockGmail } from "./EmailBrevesBlockGmail";

import { EmailSignatureGmail } from "./EmailSignatureGmail";

import { EmailEditorialBlockGmail } from "./EmailEditorialBlockGmail";

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

export function buildEmailGmail({
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
