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

};

/* ========================================================= */

export default function KnowledgeExplorerRow({

  entity,

}: Props) {

  const {
    openRightDrawer,
  } = useDrawer();

  let status = "⚪ Not built";

  if (
    entity.processed_contents >= entity.contents_count &&
    entity.contents_count > 0
  ) {

    status = "🟢 Ready";

  } else if (
    entity.processed_contents > 0
  ) {

    status = "🟡 Building";

  }

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

      <td className="px-4 py-3 text-center text-sm">

        {status}

      </td>

      <td className="px-4 py-3 text-center text-sm text-gray-600">

        {entity.processed_contents} / {entity.contents_count}

      </td>

    </tr>

  );

}
