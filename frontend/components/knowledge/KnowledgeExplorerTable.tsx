import KnowledgeExplorerRow from "./KnowledgeExplorerRow";

import type {
  KnowledgeEntitySummary,
} from "@/types/knowledge";

type Props = {

  entities: KnowledgeEntitySummary[];

  onOpen: (
    entity: KnowledgeEntitySummary,
  ) => void;

};

export default function KnowledgeExplorerTable({

  entities,

  onOpen,

}: Props) {

  return (

    <table className="min-w-full">

      <thead className="border-b bg-gray-50">

        <tr>

          <th className="px-4 py-3 text-left text-sm font-medium">
            Type
          </th>

          <th className="px-4 py-3 text-left text-sm font-medium">
            Entity
          </th>

          <th className="px-4 py-3 text-center text-sm font-medium">
            Contents
          </th>

          <th className="px-4 py-3 text-center text-sm font-medium">
            Users
          </th>

          <th className="px-4 py-3 text-center text-sm font-medium">
            Experts
          </th>

          <th className="px-4 py-3 text-center text-sm font-medium">
            Knowledge
          </th>

          <th className="px-4 py-3 text-center text-sm font-medium">
            Updated
          </th>

        </tr>

      </thead>

      <tbody>

        {

          entities.map((entity) => (

            <KnowledgeExplorerRow

              key={`${entity.entity_type}-${entity.entity_id}`}

              entity={entity}

              onOpen={onOpen}

            />

          ))

        }

      </tbody>

    </table>

  );

}
