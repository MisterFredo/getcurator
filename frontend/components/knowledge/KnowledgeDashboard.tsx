import KnowledgeStatCard from "./KnowledgeStatCard";

export default function KnowledgeDashboard() {

  return (

    <div className="grid grid-cols-2 gap-4 lg:grid-cols-6">

      <KnowledgeStatCard

        title="Companies"

        value={0}

      />

      <KnowledgeStatCard

        title="Topics"

        value={0}

      />

      <KnowledgeStatCard

        title="Solutions"

        value={0}

      />

      <KnowledgeStatCard

        title="Knowledge"

        value={0}

      />

      <KnowledgeStatCard

        title="Users"

        value={0}

      />

      <KnowledgeStatCard

        title="Experts"

        value={0}

      />

    </div>

  );

}
