import KnowledgeExplorerRow from "./KnowledgeExplorerRow";

import type {
  KnowledgeEntitySummary,
} from "@/types/knowledge";

/* ========================================================= */

type Props = {

  entities: KnowledgeEntitySummary[];

  buildableEntities: KnowledgeEntitySummary[];

  selectedKeys: string[];

  multiBuilding: boolean;

  onToggleEntity: (
    entity: KnowledgeEntitySummary,
  ) => void;

  onSetSelection: (
    entities: KnowledgeEntitySummary[],
  ) => void;

};

/* ========================================================= */

export default function KnowledgeExplorerTable({

  entities,

  buildableEntities,

  selectedKeys,

  multiBuilding,

  onToggleEntity,

  onSetSelection,

}: Props) {

  /* =======================================================
     ENTITY KEY
  ======================================================= */

  function getEntityKey(
    entity: KnowledgeEntitySummary,
  ) {

    return (
      `${entity.entity_type}:${entity.entity_id}`
    );

  }

  /* =======================================================
     SELECT ALL STATUS
  ======================================================= */

  const allSelected =

    buildableEntities.length > 0
    &&
    buildableEntities.every(
      entity =>
        selectedKeys.includes(
          getEntityKey(
            entity,
          ),
        ),
    );

  /* =======================================================
     TOGGLE ALL
  ======================================================= */

  function handleToggleAll() {

    if (multiBuilding) {
      return;
    }

    if (allSelected) {

      onSetSelection(
        [],
      );

      return;

    }

    onSetSelection(
      buildableEntities,
    );

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <table className="min-w-full">

      <thead className="border-b bg-gray-50">

        <tr>

          {/* ================================================= */}
          {/* SELECT */}
          {/* ================================================= */}

          <th className="w-[50px] px-4 py-3 text-center">

            <input

              type="checkbox"

              checked={
                allSelected
              }

              onChange={
                handleToggleAll
              }

              disabled={
                multiBuilding
                ||
                buildableEntities.length === 0
              }

              className="h-4 w-4"

            />

          </th>

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
            Status
          </th>

          <th className="px-4 py-3 text-center text-sm font-medium">
            Progress
          </th>

        </tr>

      </thead>

      <tbody>

        {

          entities.map(
            entity => {

              const key =
                getEntityKey(
                  entity,
                );

              const isBuildable =

                entity.contents_count > 0
                &&
                entity.processed_contents <
                  entity.contents_count;

              const isSelected =
                selectedKeys.includes(
                  key,
                );

              return (

                <KnowledgeExplorerRow

                  key={
                    `${entity.entity_type}-${entity.entity_id}`
                  }

                  entity={
                    entity
                  }

                  isBuildable={
                    isBuildable
                  }

                  isSelected={
                    isSelected
                  }

                  multiBuilding={
                    multiBuilding
                  }

                  onToggle={
                    () =>
                      onToggleEntity(
                        entity,
                      )
                  }

                />

              );

            },
          )

        }

      </tbody>

    </table>

  );

}
