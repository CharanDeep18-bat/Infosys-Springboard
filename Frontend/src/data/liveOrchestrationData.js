export const PIPELINE_STAGES = [
  {
    name: "Document Agent",
    key: "DOCUMENT_AGENT_COMPLETED"
  },
  {
    name: "Extraction Agent",
    key: "EXTRACTION_COMPLETED"
  },
  {
    name: "Evidence Validation",
    key: "EVIDENCE_VALIDATION_COMPLETED"
  },
  {
    name: "Red Flag Agent",
    key: "RED_FLAGS_COMPLETED"
  },
  {
    name: "Persistence",
    key: "PIPELINE_COMPLETED"
  }
];

export function getCompletedStages(doc) {
  if (doc.processingStatus === "COMPLETED") {
    return PIPELINE_STAGES.length;
  }

  const index = PIPELINE_STAGES.findIndex(
    stage => stage.key === doc.processingStage
  );

  return index + 1;
}

export function getPipelineSummary(documents) {
  return {
    total: documents.length,
    queued: documents.filter(
      d => d.status === "Queued"
    ).length,
    processing: documents.filter(
      d => d.status === "Processing"
    ).length,
    completed: documents.filter(
      d => d.status === "Ready"
    ).length,
    failed: documents.filter(
      d => d.status === "Error"
    ).length
  };
}