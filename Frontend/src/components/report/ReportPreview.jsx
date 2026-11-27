import React from "react";
import { ArrowLeft, Download, Printer } from "lucide-react";

function MarkdownContent({ content }) {
  const lines = (content || "").split("\n");
  const blocks = [];

  let index = 0;

  while (index < lines.length) {
    const line = lines[index].trim();

    if (line.startsWith("|")) {
      const rows = [];

      while (
        index < lines.length &&
        lines[index].trim().startsWith("|")
      ) {
        const cells = lines[index]
          .trim()
          .replace(/^\||\|$/g, "")
          .split("|")
          .map(cell => cell.trim());

        if (!cells.every(cell => /^[-:\s]+$/.test(cell))) {
          rows.push(cells);
        }

        index++;
      }

      if (rows.length) {
        blocks.push(
          <div
            key={index}
            className="table-scroll-wrapper"
          >
            <table className="report-table">
              <thead>
                <tr>
                  {rows[0].map((cell, i) => (
                    <th key={i}>{cell}</th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {rows.slice(1).map((row, i) => (
                  <tr key={i}>
                    {row.map((cell, j) => (
                      <td key={j}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      }

      continue;
    }

    if (line.startsWith("#")) {
      blocks.push(
        <h3 key={index} className="font-bold mt-3">
          {line.replace(/^#+\s*/, "")}
        </h3>
      );
    } else if (line) {
      blocks.push(
        <p key={index} className="report-body-text">
          {line.replace(/\*\*/g, "")}
        </p>
      );
    }

    index++;
  }

  return <>{blocks}</>;
}

export default function ReportPreview({
  report,
  onBackToLibrary,
  onOpenPdfExport,
  downloading = false
}) {
  if (!report) return null;

  const content = report.content;

  if (!content) {
    return (
      <div className="p-6">
        No verified report content is available.
      </div>
    );
  }

  return (
    <div className="report-preview-page-container">
      <div className="report-controls-bar no-print">
        <button
          className="fin-btn fin-btn-secondary"
          onClick={onBackToLibrary}
        >
          <ArrowLeft size={14} />
          Back to Reports
        </button>

        <div className="flex-row gap-2">
          <button
            className="fin-btn fin-btn-secondary"
            onClick={() => window.print()}
          >
            <Printer size={14} />
            Print
          </button>

          <button
            className="fin-btn fin-btn-primary"
            onClick={onOpenPdfExport}
            disabled={downloading}
          >
            <Download size={14} />

            {downloading
              ? "Preparing PDF..."
              : "Download PDF"}
          </button>
        </div>
      </div>

      <article
        className="analyst-report-document"
        id="printable-analyst-report"
      >
        <header className="report-doc-header">
          <span className="report-eyebrow">
            FINRESEARCH AI
          </span>

          <h1 className="report-main-title">
            {report.title}
          </h1>

          <p>Company: {content.company_name}</p>

          <p>
            Fiscal year: {content.fiscal_year || "Unavailable"}
          </p>

          <p>Generated: {content.generated_at}</p>

          <p>Status: {content.status}</p>
        </header>

        {(content.sections || []).map((section, index) => (
          <section
            key={section.section_key}
            className="report-section"
          >
            <h2 className="report-section-heading">
              {index + 1}. {section.title}
            </h2>

            {section.status !== "generated" && (
              <p className="text-warning">
                Section status: {section.status}
              </p>
            )}

            <MarkdownContent
              content={section.content_markdown}
            />

            {(section.citations || []).length > 0 && (
              <details className="mt-3">
                <summary className="font-semibold text-teal">
                  Source citations ({section.citations.length})
                </summary>

                {section.citations.map((citation, i) => (
                  <div
                    key={i}
                    className="preview-table-card mt-2 p-3"
                  >
                    <strong>
                      {citation.document_name}
                    </strong>

                    <p>Page: {citation.page_number}</p>

                    {citation.metric_name && (
                      <p>Metric: {citation.metric_name}</p>
                    )}

                    <blockquote>
                      {citation.exact_quote}
                    </blockquote>

                    {citation.is_calculated && (
                      <p>Calculated financial indicator</p>
                    )}
                  </div>
                ))}
              </details>
            )}
          </section>
        ))}

        <section className="report-section">
          <h2 className="report-section-heading">
            Limitations
          </h2>

          <ul>
            {(content.limitations || []).map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </section>
      </article>
    </div>
  );
}