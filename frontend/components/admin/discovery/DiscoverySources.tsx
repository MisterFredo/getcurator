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

      {/* =====================================================
          HEADER
      ====================================================== */}

      <div className="p-4 border-b font-semibold">
        Sources configurées
      </div>


      {/* =====================================================
          TABLE
      ====================================================== */}

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
              Domaine
            </th>

            <th className="p-3 text-left">
              Action
            </th>

          </tr>

        </thead>


        <tbody>

          {sources.length === 0 ? (

            <tr>

              <td
                colSpan={4}
                className="p-6 text-center text-gray-400"
              >
                Aucune source configurée.
              </td>

            </tr>

          ) : (

            sources.map((source) => {

              const acquisitionMode = (
                source.acquisition_mode || ""
              ).toUpperCase();

              const isManual =
                acquisitionMode === "MANUAL";

              return (

                <tr
                  key={source.source_id}
                  className="border-b last:border-b-0"
                >

                  {/* =========================================
                      SOURCE
                  ========================================== */}

                  <td className="p-3 font-medium">

                    {source.name}

                  </td>


                  {/* =========================================
                      ACQUISITION MODE
                  ========================================== */}

                  <td className="p-3">

                    {acquisitionMode || "—"}

                  </td>


                  {/* =========================================
                      DOMAIN
                  ========================================== */}

                  <td className="p-3">

                    {source.domain || "—"}

                  </td>


                  {/* =========================================
                      ACTION
                  ========================================== */}

                  <td className="p-3">

                    {isManual ? (

                      <span className="text-gray-400">
                        —
                      </span>

                    ) : (

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

                    )}

                  </td>

                </tr>

              );

            })

          )}

        </tbody>

      </table>

    </div>

  );

}
