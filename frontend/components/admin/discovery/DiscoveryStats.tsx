type Props = {
  total: number;
};

export default function DiscoveryStats({
  total,
}: Props) {

  return (

    <div className="bg-white border rounded p-4">

      <div className="text-sm text-gray-500">
        URLs découvertes
      </div>

      <div className="text-3xl font-semibold mt-1">
        {total}
      </div>

    </div>

  );
}
