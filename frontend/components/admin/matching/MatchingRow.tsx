type MatchOption = {
  id: string;
  label: string;
  type: "company" | "solution";
};

type Props = {
  item: any;

  options: MatchOption[];

  selected: any;
  setSelected: any;

  selectedType: any;
  setSelectedType: any;

  checked: any;
  setChecked: any;

  processing: string | null;

  applyMatch: (v: string) => void;
  ignore: (v: string) => void;
};

export default function MatchingRow({
  item,

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
}: Props) {

  return (

    <tr className="border-t">

      {/* =====================================================
          CHECK
      ===================================================== */}

      <td className="p-3">

        <input
          type="checkbox"
          checked={
            checked[item.value] || false
          }
          onChange={(e) =>
            setChecked({
              ...checked,
              [item.value]:
                e.target.checked,
            })
          }
        />

      </td>

      {/* =====================================================
          VALUE
      ===================================================== */}

      <td className="p-3 font-medium">

        <div className="flex items-center gap-2">

          <span>
            {item.value}
          </span>

          {item.type_hint === "solution" && (

            <span className="
              text-xs
              text-purple-600
              bg-purple-100
              px-2
              py-1
              rounded-full
            ">
              Solution
            </span>

          )}

          {item.type_hint === "company" && (

            <span className="
              text-xs
              text-blue-600
              bg-blue-100
              px-2
              py-1
              rounded-full
            ">
              Company
            </span>

          )}

        </div>

        {item.suggested_label && (

          <div className="
            text-xs
            text-gray-500
            mt-1
          ">

            Suggestion :
            {" "}

            <span className="font-medium">
              {item.suggested_label}
            </span>

          </div>

        )}

      </td>

      {/* =====================================================
          COUNT
      ===================================================== */}

      <td className="p-3 text-gray-500">

        {item.count}

      </td>

      {/* =====================================================
          SELECT
      ===================================================== */}

      <td className="p-3">

        <select
          className="
            border
            p-2
            rounded
            w-full
          "
          value={
            selected[item.value] || ""
          }
          onChange={(e) => {

            const selectedId =
              e.target.value;

            const option =
              options.find(
                (o) =>
                  o.id === selectedId
              );

            setSelected({
              ...selected,
              [item.value]:
                selectedId,
            });

            if (option) {

              setSelectedType({
                ...selectedType,
                [item.value]:
                  option.type,
              });

            }

          }}
        >

          <option value="">
            Sélectionner
          </option>

          {options.map((o) => (

            <option
              key={`${o.type}-${o.id}`}
              value={o.id}
            >

              [{o.type}]
              {" "}
              {o.label}

            </option>

          ))}

        </select>

      </td>

      {/* =====================================================
          ACTIONS
      ===================================================== */}

      <td className="
        p-3
        flex
        justify-end
        gap-2
      ">

        <button
          onClick={() =>
            applyMatch(item.value)
          }
          disabled={
            processing === item.value
          }
          className="
            bg-green-600
            text-white
            px-3
            py-1
            rounded
          "
        >
          MATCH
        </button>

        <button
          onClick={() =>
            ignore(item.value)
          }
          disabled={
            processing === item.value
          }
          className="
            bg-gray-400
            text-white
            px-3
            py-1
            rounded
          "
        >
          IGNORE
        </button>

      </td>

    </tr>

  );

}
