type Source = {
  source_id: string;
  name: string;
  domain?: string | null;
  acquisition_mode?: string | null;
};

type Props = {
  sources: Source[];
  onScan: (
    sourceId: string,
    sourceName: string
  ) => void;
};

export default function DiscoverySources({
  sources,
  onScan,
}: Props) {

  return (

    <div className="bg-white border rounded overflow-hidden">

      <div className="p-4 border-b font-semibold">
        Sources configurées
      </div>

      <table className="w-full text-sm">

        <thead>

          <tr className="bg-gray-50 border-b">

            <th className="p-3 text-left">
              Source
            </th>

            <th className="p-3 text-left">
              Mode
            </th>

            <th className="p-3 text-left">
              URL Discovery
            </th>

            <th className="p-3 text-left">
              Action
            </th>

          </tr>

        </thead>

        <tbody>

          {sources.map((source) => (

            <tr
              key={source.source_id}
              className="border-b"
            >

              <td className="p-3 font-medium">
                {source.name}
              </td>

              <td className="p-3">
                {source.acquisition_mode || "—"}
              </td>

              <td className="p-3">
                {source.domain || "—"}
              </td>

              <td className="p-3">

                <button
                  onClick={() =>
                    onScan(
                      source.source_id,
                      source.name
                    )
                  }
                  className="bg-ratecard-blue text-white px-3 py-1 rounded"
                >
                  SCAN
                </button>

              </td>

            </tr>

          ))}

        </tbody>

      </table>

    </div>

  );
}
