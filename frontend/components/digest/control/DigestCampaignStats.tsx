"use client";

type Props = {
  generated: number;
  ready: number;
  review: number;
  failed: number;
};

type StatCardProps = {
  label: string;
  value: number;
  color: string;
};

function StatCard({
  label,
  value,
  color,
}: StatCardProps) {
  return (
    <div className="bg-white border rounded-xl p-5">

      <div className="text-sm text-gray-500">
        {label}
      </div>

      <div
        className={`mt-2 text-3xl font-semibold ${color}`}
      >
        {value}
      </div>

    </div>
  );
}

export default function DigestCampaignStats({
  generated,
  ready,
  review,
  failed,
}: Props) {

  return (

    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">

      <StatCard
        label="Generated"
        value={generated}
        color="text-blue-600"
      />

      <StatCard
        label="Ready"
        value={ready}
        color="text-green-600"
      />

      <StatCard
        label="Needs Review"
        value={review}
        color="text-amber-600"
      />

      <StatCard
        label="Failed"
        value={failed}
        color="text-red-600"
      />

    </div>

  );

}
