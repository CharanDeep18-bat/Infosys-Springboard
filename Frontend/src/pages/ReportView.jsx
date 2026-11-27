import React, { useState, useEffect } from "react";
import { adaptSavedReport } from "../data/savedReportData";
import ReportsLibrary from "../components/report/ReportsLibrary";
import ReportConfigModal from "../components/report/ReportConfigModal";
import ReportPreview from "../components/report/ReportPreview";
import RenameReportModal from "../components/report/RenameReportModal";
import DeleteConfirmModal from "../components/report/DeleteConfirmModal";

import { api } from "../services/api";

export default function ReportView({
  session,
  sessions = [],
  onBack,
  initialView = "library"
}) {
  const [reports, setReports] = useState([]);
  const [currentView, setCurrentView] = useState("library");
  const [activeReport, setActiveReport] = useState(null);

  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [renameTarget, setRenameTarget] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setCurrentView("library");
  }, [initialView, session?.id]);
  useEffect(() => {
    let cancelled = false;

    async function loadReports() {
      try {
        const result = await api.listReports();

        if (!cancelled) {
          setReports(result.map(adaptSavedReport));
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err.message || "Unable to load saved reports"
          );
        }
      }
    }

    loadReports();

    return () => {
      cancelled = true;
    };
  }, []);
  async function handleCreateReport(config) {
    setError("");

    const result = await api.generateReport(
      config.documentId,
      config.comparisonDocumentIds
    );

    const newReport = adaptSavedReport(result);

    setReports(prev => [
      newReport,
      ...prev.filter(r => r.id !== newReport.id)
    ]);

    setActiveReport(newReport);
    setCurrentView("preview");
  }

  function handlePreviewReport(report) {
    setActiveReport(report);
    setCurrentView("preview");
  }

  async function handleDownloadReport(report) {
    if (!report || downloading) return;

    setDownloading(true);
    setError("");

    try {
      const blob = await api.downloadSavedReport(
        report.id
      );

      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");

      link.href = url;
      link.download =
        report.title.replace(/[^a-zA-Z0-9_-]/g, "_") + ".pdf";

      document.body.appendChild(link);
      link.click();
      link.remove();

      setTimeout(() => URL.revokeObjectURL(url), 1000);

    } catch (err) {
      setError(err.message || "PDF download failed.");
    } finally {
      setDownloading(false);
    }
  }

  async function handleRenameReport(reportId, newTitle) {
    setError("");

    try {
      const result = await api.renameReport(
        reportId,
        newTitle
      );

      const updated = adaptSavedReport(result);

      setReports(prev =>
        prev.map(r =>
          r.id === reportId ? updated : r
        )
      );

      setActiveReport(prev =>
        prev?.id === reportId ? updated : prev
      );

      setRenameTarget(null);

    } catch (err) {
      setError(
        err.message || "Unable to rename report"
      );
    }
  }

  async function handleDeleteReport(reportId) {
    setError("");

    try {
      await api.deleteReport(reportId);

      setReports(prev =>
        prev.filter(r => r.id !== reportId)
      );

      if (activeReport?.id === reportId) {
        setActiveReport(null);
        setCurrentView("library");
      }

      setDeleteTarget(null);

    } catch (err) {
      setError(
        err.message || "Unable to delete report"
      );
    }
  }

  return (
    <div className="fin-reports-module-page">
      {error && (
        <div className="p-3 text-danger">
          {error}
        </div>
      )}

      {currentView === "preview" && activeReport ? (
        <ReportPreview
          report={activeReport}
          onBackToLibrary={() => setCurrentView("library")}
          onOpenPdfExport={() =>
            handleDownloadReport(activeReport)
          }
          downloading={downloading}
        />
      ) : (
        <ReportsLibrary
          reports={reports}
          onGenerateReportClick={() =>
            setConfigModalOpen(true)
          }
          onPreviewReport={handlePreviewReport}
          onDownloadReport={handleDownloadReport}
          onRenameReport={setRenameTarget}
          onDeleteReport={setDeleteTarget}
          onRetryGeneration={() => setConfigModalOpen(true)}
        />
      )}

      <ReportConfigModal
        open={configModalOpen}
        onClose={() => setConfigModalOpen(false)}
        sessions={sessions}
        activeSession={session}
        onGenerateReport={handleCreateReport}
      />

      <RenameReportModal
        open={Boolean(renameTarget)}
        onClose={() => setRenameTarget(null)}
        report={renameTarget}
        onSave={handleRenameReport}
      />

      <DeleteConfirmModal
        open={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        report={deleteTarget}
        onConfirm={handleDeleteReport}
      />
    </div>
  );
}