import MatchingRow from "./MatchingRow";

export default function MatchingTable({
  items,
  options,

  selected,
  setSelected,

  selectedType,
  setSelectedType,

  checked,
  setChecked,

  processing,

  applyMatch,
  ignore,
}: any) {

  return (

    <div className="border rounded overflow-hidden">

      <table className="w-full text-sm">

        <thead className="bg-gray-100 text-left">

          <tr>

            <th className="p-3 w-10">

              <input
                type="checkbox"
                onChange={(e) => {

                  const checkedAll =
                    e.target.checked;

                  const newState: any = {};

                  items.forEach((i: any) => {
                    newState[i.value] =
                      checkedAll;
                  });

                  setChecked(newState);

                }}
              />

            </th>

            <th className="p-3">
              Valeur LLM
            </th>

            <th className="p-3">
              Nb contenus
            </th>

            <th className="p-3">
              Match
            </th>

            <th className="p-3 w-40 text-right">
              Actions
            </th>

          </tr>

        </thead>

        <tbody>

          {items.map((item: any) => (

            <MatchingRow
              key={item.value}

              item={item}

              options={options}

              selected={selected}
              setSelected={setSelected}

              selectedType={selectedType}
              setSelectedType={setSelectedType}

              checked={checked}
              setChecked={setChecked}

              processing={processing}

              applyMatch={applyMatch}
              ignore={ignore}
            />

          ))}

          {items.length === 0 && (

            <tr>

              <td
                colSpan={5}
                className="
                  p-6
                  text-center
                  text-gray-400
                "
              >
                Rien à matcher
              </td>

            </tr>

          )}

        </tbody>

      </table>

    </div>

  );

}
