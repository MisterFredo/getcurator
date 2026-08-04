import type {
  KnowledgeEntitySummary,
} from "@/types/knowledge";

type Props = {

  entity: KnowledgeEntitySummary;

  onOpen: (
    entity: KnowledgeEntitySummary,
  ) => void;

};

export default function KnowledgeExplorerRow({

  entity,

  onOpen,

}: Props) {

  return (

    <tr

      onClick={() =>

        onOpen(entity)

      }

      className="
        cursor-pointer
        border-b
        hover:bg-gray-50
      "

    >

      <td className="px-4 py-3 text-sm">

        {entity.entity_type}

      </td>

      <td className="px-4 py-3 font-medium">

        {entity.name}

      </td>

      <td className="px-4 py-3 text-center">

        {entity.contents_count}

      </td>

      <td className="px-4 py-3 text-center">

        {entity.users_count}

      </td>

      <td className="px-4 py-3 text-center">

        {entity.experts_count}

      </td>

      <td className="px-4 py-3 text-center">

        {

          entity.has_knowledge

            ? "🟢"

            : "⚪"

        }

      </td>

      <td className="px-4 py-3 text-center text-sm text-gray-500">

        {

          entity.last_build

            ? new Date(
                entity.last_build,
              ).toLocaleDateString()

            : "-"

        }

      </td>

    </tr>

  );

}
