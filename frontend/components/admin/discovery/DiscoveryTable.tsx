type DiscoveryItem = {
  id_discovery: string;
  source_name?: string | null;
  url: string;
  title?: string | null;
  status: string;
};

type Props = {
  items: DiscoveryItem[];

  selectedIds: string[];

  onToggle: (
    idDiscovery: string
  ) => void;

  onToggleAll: () => void;
};

export default function DiscoveryTable({
  items,
  selectedIds,
  onToggle,
  onToggleAll,
}: Props) {

  const allSelected =
    items.length > 0 &&
    selectedIds.length === items.length;

  return (

    <div className="bg-white border rounded overflow-hidden">

      <table className="w-full text-sm">

        <thead>

          <tr className="bg-gray-50 border-b">

            <th className="p-3">

              <input
                type="checkbox"
                checked={allSelected}
                onChange={onToggleAll}
              />

            </th>

            <th className="p-3 text-left">
              Source
            </th>

            <th className="p-3 text-left">
              Titre
            </th>

            <th className="p-3 text-left">
              URL
            </th>

            <th className="p-3 text-left">
              Status
            </th>

          </tr>

        </thead>

        <tbody>

          {items.map((item) => (

            <tr
              key={item.id_discovery}
              className="border-b hover:bg-gray-50"
            >

              <td className="p-3">

                <input
                  type="checkbox"
                  checked={selectedIds.includes(
                    item.id_discovery
                  )}
                  onChange={() =>
                    onToggle(
                      item.id_discovery
                    )
                  }
                />

              </td>

              <td className="p-3">
                {item.source_name}
              </td>

              <td className="p-3">
                {item.title}
              </td>

              <td className="p-3">

                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-600 hover:underline break-all"
                >
                  {item.url}
                </a>

              </td>

              <td className="p-3">
                {item.status}
              </td>

            </tr>

          ))}

        </tbody>

      </table>

    </div>

  );
}
