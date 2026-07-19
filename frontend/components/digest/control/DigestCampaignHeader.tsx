"use client";

type Props = {
  title: string;
  period: string;
};

export default function DigestCampaignHeader({
  title,
  period,
}: Props) {
  return (
    <div className="bg-white border rounded-xl px-6 py-5">

      <h1 className="text-2xl font-semibold text-gray-900">
        {title}
      </h1>

      <p className="mt-2 text-sm text-gray-500">
        {period}
      </p>

    </div>
  );
}
