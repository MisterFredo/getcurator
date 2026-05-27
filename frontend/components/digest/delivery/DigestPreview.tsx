// frontend/components/digest/delivery/DigestPreview.tsx

"use client";

import NewsletterPreview from "@/components/newsletter/delivery/NewsletterPreview";

import type {
  DigestContentItem,
} from "@/types/digest";

import type {
  HeaderConfig,
  NewsletterNewsItem,
} from "@/types/newsletter";

/* ========================================================= */

type Props = {
  headerConfig: HeaderConfig;

  editorialHtml?: string;

  contents: DigestContentItem[];
};

/* =========================================================
   MAP DIGEST → NEWSLETTER
========================================================= */

function mapDigestToNewsletter(
  item: DigestContentItem
): NewsletterNewsItem {

  return {
    id: item.id,

    title:
      item.title,

    excerpt:
      item.excerpt,

    published_at:
      item.published_at,

    url:
      item.url,

    media_id:
      item.media_id,

    primary_company_logo:
      item.primary_company_logo,

    companies:
      item.companies,

    topics:
      item.topics,

    styles:
      item.styles,

    content_type:
      item.content_type,
  } as NewsletterNewsItem;
}

/* ========================================================= */

export default function DigestPreview({
  headerConfig,

  editorialHtml,

  contents,
}: Props) {

  /* =======================================================
     SPLIT CONTENTS
  ======================================================= */

  const news =
    contents
      .filter(
        (c) =>
          c.content_type ===
          "news"
      )
      .map(
        mapDigestToNewsletter
      );

  const breves =
    contents
      .filter(
        (c) =>
          c.content_type !==
          "news"
      )
      .map(
        mapDigestToNewsletter
      );

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <NewsletterPreview
      headerConfig={
        headerConfig
      }

      editorialHtml={
        editorialHtml
      }

      news={
        news
      }

      breves={
        breves
      }
    />

  );
}
