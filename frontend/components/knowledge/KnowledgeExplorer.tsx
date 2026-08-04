import KnowledgeExplorerTable from "./KnowledgeExplorerTable";

import type {
  KnowledgeEntitySummary,
} from "@/types/knowledge";

/* ========================================================= */

type Props = {

  entities: KnowledgeEntitySummary[];

};

/* ========================================================= */

export default function KnowledgeExplorer({

  entities,

}: Props) {

  return (

    <div className="rounded-lg border bg-white">

      <KnowledgeExplorerTable

        entities={entities}

      />

    </div>

  );

}
