"use client";

import {
  useDrawer,
} from "@/contexts/DrawerContext";

import type {
  KnowledgeEntitySummary,
} from "@/types/knowledge";

/* ========================================================= */

type Props = {

  entity: KnowledgeEntitySummary;

  isBuildable: boolean;

  isSelected: boolean;

  multiBuilding: boolean;

  onToggle: () => void;

};

/* ========================================================= */

export default function KnowledgeExplorerRow({

  entity,

  isBuildable,

  isSelected,

  multiBuilding,

  onToggle,

}: Props) {

  const {
    openRightDrawer,
  } = useDrawer();

  /* =======================================================
     STATUS
  ======================================================= */

  let status =
    "⚪ Not built";

  if (
    entity.processed_contents >=
      entity.contents_count
    &&
    entity.contents_count > 0
  ) {

    status =
      "🟢 Ready";

  } else if (
    entity.processed_contents > 0
  ) {

    status =
      "🟡 Building";

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <tr

      onClick={() =>

        openRightDrawer(

          "knowledge",

          entity.entity_id,

          "silent",

          entity.entity_type,

          entity,

        )

      }

      className="
        cursor-pointer
        border-b
        hover:bg-gray-50
      "

    >

      {/* ================================================= */}
      {/* SELECT */}
      {/* ================================================= */}

      <td
        className="w-[50px] px-4 py-3 text-center"

        onClick={(e) => {
          e.stopPropagation();
        }}
      >

        <input

          type="checkbox"

          checked={
            isSelected
          }

          disabled={
            !isBuildable
            ||
            multiBuilding
          }

          onChange={() => {

            if (
              !isBuildable
              ||
              multiBuilding
            ) {
              return;
            }

            onToggle();

          }}

          className="h-4 w-4"

        />

      </td>

      {/* ================================================= */}
      {/* TYPE */}
      {/* ================================================= */}

      <td className="px-4 py-3 text-sm">

        {entity.entity_type}

      </td>

      {/* ================================================= */}
      {/* ENTITY */}
      {/* ================================================= */}

      <td className="px-4 py-3 font-medium">

        {entity.name}

      </td>

      {/* ================================================= */}
      {/* CONTENTS */}
      {/* ================================================= */}

      <td className="px-4 py-3 text-center">

        {entity.contents_count}

      </td>

      {/* ================================================= */}
      {/* USERS */}
      {/* ================================================= */}

      <td className="px-4 py-3 text-center">

        {entity.users_count}

      </td>

      {/* ================================================= */}
      {/* EXPERTS */}
      {/* ================================================= */}

      <td className="px-4 py-3 text-center">

        {entity.experts_count}

      </td>

      {/* ================================================= */}
      {/* STATUS */}
      {/* ================================================= */}

      <td className="px-4 py-3 text-center text-sm">

        {status}

      </td>

      {/* ================================================= */}
      {/* PROGRESS */}
      {/* ================================================= */}

      <td className="px-4 py-3 text-center text-sm text-gray-600">

        {entity.processed_contents}
        {" / "}
        {entity.contents_count}

      </td>

    </tr>

  );

}
