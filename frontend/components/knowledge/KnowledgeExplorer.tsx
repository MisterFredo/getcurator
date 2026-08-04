type Props = {

  entities: KnowledgeEntitySummary[];

  onOpen: (
    entity: KnowledgeEntitySummary,
  ) => void;

};

export default function KnowledgeExplorer({

  entities,

  onOpen,

}: Props) {

  return (

    <div className="rounded-lg border bg-white">

      <KnowledgeExplorerTable

        entities={entities}

        onOpen={onOpen}

      />

    </div>

  );

}
