"use client";

import SelectionPanelCore from "./SelectionPanelCore";
import NumbersSelectionRenderer from "./renderers/NumbersSelectionRenderer";
import BasicAnalysisRenderer from "./renderers/BasicAnalysisRenderer";

/* ========================================================= */

export default function NumbersSelectionPanel(props: any) {

  const {
    selectedItems,
    analysis,
    loading,
    onRemove,
  } = props;

  return (
    <SelectionPanelCore
      selectedCount={selectedItems.length}
      onGenerate={props.onGenerateInsight}
      onClose={props.onClose}
      loading={loading}

      labels={{
        generate: "Structurer les données",
        empty: "Sélectionne des chiffres",
      }}

      renderSelection={() => (
        <NumbersSelectionRenderer
          selectedItems={selectedItems}
          onRemove={onRemove}
        />
      )}

      renderAnalysis={() => (
        <BasicAnalysisRenderer
          analysis={analysis}
          loading={loading}
        />
      )}
    />
  );
}
