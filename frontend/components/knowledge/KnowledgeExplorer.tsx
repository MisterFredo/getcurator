import KnowledgeExplorerTable from "./KnowledgeExplorerTable";

import type {
  KnowledgeEntitySummary,
} from "@/types/knowledge";

/* ========================================================= */

type CurrentBuild = {

  index: number;

  total: number;

  name: string;

};

/* ========================================================= */

type Props = {

  entities: KnowledgeEntitySummary[];

  selectedKeys: string[];

  multiBuilding: boolean;

  currentBuild: CurrentBuild | null;

  onToggleEntity: (
    entity: KnowledgeEntitySummary,
  ) => void;

  onSetSelection: (
    entities: KnowledgeEntitySummary[],
  ) => void;

  onMultiBuild: () => Promise<void>;

};

/* ========================================================= */

export default function KnowledgeExplorer({

  entities,

  selectedKeys,

  multiBuilding,

  currentBuild,

  onToggleEntity,

  onSetSelection,

  onMultiBuild,

}: Props) {

  /* =======================================================
     BUILDABLE ENTITIES
  ======================================================= */

  const buildableEntities =
    entities.filter(
      entity =>
        entity.contents_count > 0
        &&
        entity.processed_contents <
          entity.contents_count,
    );

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="rounded-lg border bg-white">

      {/* ================================================= */}
      {/* MULTI ACTIONS */}
      {/* ================================================= */}

      <div className="flex items-center justify-between border-b px-4 py-3">

        <div className="text-sm text-gray-600">

          {

            multiBuilding &&
            currentBuild ? (

              <>

                Building{" "}

                <span className="font-medium">
                  {currentBuild.index}
                  {" / "}
                  {currentBuild.total}
                </span>

                {" — "}

                <span className="font-medium">
                  {currentBuild.name}
                </span>

              </>

            ) : (

              <>

                <span className="font-medium">
                  {selectedKeys.length}
                </span>

                {" selected"}

              </>

            )

          }

        </div>

        <button

          type="button"

          onClick={
            onMultiBuild
          }

          disabled={
            multiBuilding
            ||
            selectedKeys.length === 0
          }

          className="
            rounded
            bg-ratecard-green
            px-4
            py-2
            text-sm
            text-white
            disabled:opacity-50
          "

        >

          {

            multiBuilding
              ? "Building..."
              : "Build selected — Auto Continue"

          }

        </button>

      </div>

      {/* ================================================= */}
      {/* TABLE */}
      {/* ================================================= */}

      <KnowledgeExplorerTable

        entities={
          entities
        }

        buildableEntities={
          buildableEntities
        }

        selectedKeys={
          selectedKeys
        }

        multiBuilding={
          multiBuilding
        }

        onToggleEntity={
          onToggleEntity
        }

        onSetSelection={
          onSetSelection
        }

      />

    </div>

  );

}
