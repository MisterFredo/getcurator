import KnowledgeStatCard from "./KnowledgeStatCard";

import type {
  KnowledgeDashboard as KnowledgeDashboardType,
} from "@/types/knowledge";

/* ========================================================= */

type Props = {

  dashboard: KnowledgeDashboardType;

};

/* ========================================================= */

export default function KnowledgeDashboard({

  dashboard,

}: Props) {

  return (

    <div className="grid grid-cols-2 gap-4 lg:grid-cols-6">

      <KnowledgeStatCard

        title="Companies"

        value={dashboard.companies}

      />

      <KnowledgeStatCard

        title="Topics"

        value={dashboard.topics}

      />

      <KnowledgeStatCard

        title="Solutions"

        value={dashboard.solutions}

      />

      <KnowledgeStatCard

        title="Knowledge"

        value={dashboard.knowledge_built}

      />

      <KnowledgeStatCard

        title="Users"

        value={dashboard.users}

      />

      <KnowledgeStatCard

        title="Experts"

        value={dashboard.experts}

      />

    </div>

  );

}
