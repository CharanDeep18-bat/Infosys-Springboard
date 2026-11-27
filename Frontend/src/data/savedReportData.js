export function adaptSavedReport(result) {
  const date = new Date(
    result.generated_at
  ).toLocaleDateString();

  return {
    id: result.report_id,
    title: result.title,
    company: result.company_name,
    companyIds: [],
    sessionId: null,
    sessionTitle: "Financial Research",
    documentId: result.document_id,

    documentIds: [
      ...new Set([
        result.document_id,
        ...(result.citations || []).map(
          c => c.document_id
        )
      ])
    ],

    status: "Completed",
    createdAt: date,
    updatedAt: date,

    sections: result.sections.map(
      s => s.section_key
    ),

    sourceDocuments: [
      ...new Set(
        (result.citations || []).map(
          c => c.document_name
        )
      )
    ],

    summarySnippet:
      result.sections.find(
        s => s.section_key === "executive_summary"
      )?.content_markdown || "",

    generationProgress: 100,
    isDemo: false,
    hasRealPdf: true,
    content: result
  };
}