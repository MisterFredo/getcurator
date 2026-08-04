type Props = {

  open: boolean;

  entity: any;

  onClose: () => void;

};

export default function KnowledgeDrawer({

  open,

}: Props) {

  if (!open) {
    return null;
  }

  return (

    <div>

      Drawer

    </div>

  );

}
