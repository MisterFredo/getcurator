"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import DigestPreview from "@/components/digest/DigestPreview";
import { api } from "@/lib/api";
import { getDigest } from "@/lib/digest";
import type { Digest } from "@/types/digest";

type SubjectCard = {
  id: number;
  tier: "MUST" | "NICE";
  score: number;
  title: string;
  development: string;
  reason: string;
  contents: { id: string; title: string }[];
};

type SubjectPreview = {
  edition_count: number;
  candidate_count: number;
  unavailable_content_count: number;
  cards: SubjectCard[];
};

function SubjectPreviewPanel({ digestId }: { digestId: string }) {
  const [preview, setPreview] = useState<SubjectPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function generate() {
    setLoading(true);
    setError("");
    setPreview(null);
    try {
      const data = await api.post(
        "/digest/admin/digests/" + encodeURIComponent(digestId) + "/subject-preview",
        {},
      );
      setPreview(data);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Aperçu indisponible.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="space-y-4 rounded-lg border bg-white p-5">
      <h2 className="text-lg font-semibold">Digest par sujets</h2>
      <button type="button" disabled={loading} onClick={generate}
        className="rounded bg-ratecard-blue px-4 py-2 text-white disabled:opacity-50">
        {loading ? "Sélection en cours…" : "Générer l’aperçu par sujets"}
      </button>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {preview && (
        <div className="space-y-4">
          <p className="text-sm text-gray-500">
            {preview.edition_count} Éditos · {preview.candidate_count} sujets candidats ·{" "}
            {preview.cards.length} retenus
            {preview.unavailable_content_count > 0 &&
              " · " + preview.unavailable_content_count + " contenus indisponibles"}
          </p>
          {preview.cards.length === 0 && <p>Aucun sujet n’atteint le seuil de pertinence.</p>}
          {(["MUST", "NICE"] as const).map(tier => {
            const cards = preview.cards.filter(card => card.tier === tier);
            if (!cards.length) return null;
            return (
              <section key={tier} className="space-y-2">
                <h3 className="font-semibold">{tier === "MUST" ? "Must" : "Nice"}</h3>
                {cards.map(card => (
                  <article key={card.id} className="space-y-2 rounded border p-4">
                    <h4 className="font-semibold">{card.title}</h4>
                    <p className="text-sm">{card.development}</p>
                    <p className="text-sm text-gray-600">{card.reason} · {card.score}/100</p>
                    <details>
                      <summary className="cursor-pointer text-sm">
                        Contenus associés ({card.contents.length})
                      </summary>
                      <ul className="list-disc space-y-1 pl-5 pt-2 text-sm">
                        {card.contents.map(content => (
                          <li key={content.id}>
                            <Link className="text-ratecard-blue underline"
                              href={"/admin/content/edit/" + encodeURIComponent(content.id)}>
                              {content.title}
                            </Link>
                          </li>
                        ))}
                      </ul>
                    </details>
                  </article>
                ))}
              </section>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default function DigestPage() {
  const { id } = useParams<{ id: string }>();
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setDigest(null);
    getDigest(id)
      .then(data => { if (active) setDigest(data); })
      .catch(error => console.error(error))
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id]);

  if (loading || !digest) {
    return (
      <div className="rounded-lg border bg-white p-10 text-center">
        {loading ? "Loading digest..." : "Digest not found."}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SubjectPreviewPanel key={id} digestId={id} />
      <DigestPreview document={digest.document} />
    </div>
  );
}
