import type {
  NewsletterNewsItem,
  NewsletterAnalysisItem,
  NewsletterNumberItem,
  HeaderConfig,
  TopicStat,
} from "@/types/newsletter";

import { EmailLayoutGmail } from "./EmailLayoutGmail";
import { EmailHeaderGmail } from "./EmailHeaderGmail";
import { EmailNewsBlockGmail } from "./EmailNewsBlockGmail";
import { EmailStatsBlockGmail } from "./EmailStatsBlockGmail";
import { EmailBrevesBlockGmail } from "./EmailBrevesBlockGmail";
import { EmailAnalysesBlockGmail } from "./EmailAnalysesBlockGmail";
import { EmailNumbersBlockGmail } from "./EmailNumbersBlockGmail";
import { EmailSignatureGmail } from "./EmailSignatureGmail";

/* 🔥 NEW */
import { EmailEditorialBlockGmail } from "./EmailEditorialBlockGmail";

type Props = {
  headerConfig: HeaderConfig;

  /* 🔥 NEW */
  editorialHtml?: string;

  /* 🔁 fallback temporaire */
  introText?: string;

  news: NewsletterNewsItem[];
  breves: NewsletterNewsItem[];
  analyses: NewsletterAnalysisItem[];
  numbers?: NewsletterNumberItem[];
  topicStats?: TopicStat[];
};

export function buildEmailGmail({
  headerConfig,
  editorialHtml,
  introText,
  news,
  breves,
  analyses,
  numbers = [],
  topicStats = [],
}: Props) {

  /* 🔥 source unique */
  const editorial = editorialHtml || introText || "";

  const blocks = [

    /* =========================
        HEADER
    ========================== */
    EmailHeaderGmail(headerConfig),

    /* =========================
        EDITORIAL (🔥 NEW)
    ========================== */
    editorial.trim()
      ? EmailEditorialBlockGmail(editorial)
      : "",

    /* =========================
        NUMBERS
    ========================== */
    numbers.length > 0
      ? EmailNumbersBlockGmail(numbers)
      : "",

    /* =========================
        NEWS
    ========================== */
    news.length > 0
      ? EmailNewsBlockGmail(news)
      : "",

    /* =========================
        BRÈVES
    ========================== */
    breves.length > 0
      ? EmailBrevesBlockGmail(breves)
      : "",

    /* =========================
        ANALYSES
    ========================== */
    analyses.length > 0
      ? EmailAnalysesBlockGmail(analyses)
      : "",

    /* =========================
        STATS (FIN)
    ========================== */
    headerConfig.showTopicStats && topicStats.length > 0
      ? EmailStatsBlockGmail(topicStats)
      : "",

    /* =========================
        SIGNATURE
    ========================== */
    EmailSignatureGmail(),

  ].join("");

  const content = `
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
    ${blocks}
  </table>
  `;

  return EmailLayoutGmail(content);
}
