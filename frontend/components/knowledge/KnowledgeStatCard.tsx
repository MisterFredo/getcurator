type Props = {

  title: string;

  value: number;

};

export default function KnowledgeStatCard({

  title,

  value,

}: Props) {

  return (

    <div className="rounded-lg border bg-white p-5">

      <div className="text-sm text-gray-500">

        {title}

      </div>

      <div className="mt-2 text-3xl font-semibold">

        {value}

      </div>

    </div>

  );

}
