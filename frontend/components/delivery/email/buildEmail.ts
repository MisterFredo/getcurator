import type {
  NewsletterNewsItem,
  NewsletterAnalysisItem,
  NewsletterNumberItem,
  HeaderConfig,
  TopicStat,
} from "@/types/newsletter";

import { EmailLayout } from "./EmailLayout";
import { EmailHeader } from "./EmailHeader";
import { EmailStatsBlock } from "./EmailStatsBlock";
import { EmailNewsBlock } from "./EmailNewsBlock";
import { EmailBrevesBlock } from "./EmailBrevesBlock";
import { EmailAnalysesBlock } from "./EmailAnalysesBlock";
import { EmailNumbersBlock } from "./EmailNumbersBlock";

/* 🔥 NEW */
import { EmailEditorialBlock } from "./EmailEditorialBlock";

type Props = {
  headerConfig: HeaderConfig;

  /* 🔥 NEW */
  editorialHtml?: string;

  /* 🔥 legacy fallback */
  introText?: string;

  news: NewsletterNewsItem[];
  breves: NewsletterNewsItem[];
  analyses: NewsletterAnalysisItem[];
  numbers?: NewsletterNumberItem[];
  topicStats?: TopicStat[];
};

export function buildEmail({
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
        HEADER (clean, no editorial)
    ========================== */
    EmailHeader(headerConfig),

    /* =========================
        EDITORIAL (🔥 NEW POSITION)
    ========================== */
    editorial.trim()
      ? EmailEditorialBlock(editorial)
      : "",

    /* =========================
        NUMBERS
    ========================== */
    numbers.length > 0
      ? EmailNumbersBlock(numbers)
      : "",

    /* =========================
        NEWS
    ========================== */
    news.length > 0
      ? EmailNewsBlock(news)
      : "",

    /* =========================
        BRÈVES
    ========================== */
    breves.length > 0
      ? EmailBrevesBlock(breves)
      : "",

    /* =========================
        ANALYSES
    ========================== */
    analyses.length > 0
      ? EmailAnalysesBlock(analyses)
      : "",

    /* =========================
        STATS (FIN)
    ========================== */
    headerConfig.showTopicStats && topicStats.length > 0
      ? EmailStatsBlock(topicStats)
      : "",

  ].join("");

  const content = `
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
    ${blocks}
  </table>
  `;

  return EmailLayout(content);
}
