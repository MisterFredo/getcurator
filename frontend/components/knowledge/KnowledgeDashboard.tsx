// frontend/components/knowledge/KnowledgeDashboard.tsx

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

        value={dashboard.total_companies}

      />

      <KnowledgeStatCard

        title="Topics"

        value={dashboard.total_topics}

      />

      <KnowledgeStatCard

        title="Solutions"

        value={dashboard.total_solutions}

      />

      <KnowledgeStatCard

        title="Knowledge"

        value={dashboard.total_knowledge}

      />

      <KnowledgeStatCard

        title="Users"

        value={dashboard.total_users}

      />

      <KnowledgeStatCard

        title="Experts"

        value={dashboard.total_experts}

      />

    </div>

  );

}
