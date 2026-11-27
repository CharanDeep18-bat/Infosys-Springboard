import React, { useState, useEffect } from "react";
import { X, FileCheck2, Sparkles } from "lucide-react";
import { api } from "../../services/api";

export default function ReportConfigModal({
  open,
  onClose,
  sessions = [],
  activeSession,
  onGenerateReport
}) {
  const [sessionId, setSessionId] = useState("");
  const [documents, setDocuments] = useState([]);
  const [primaryId, setPrimaryId] = useState("");
  const [comparisonIds, setComparisonIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (open) {
      setSessionId(activeSession?.id || "");
      setError("");
    }
  }, [open, activeSession?.id]);

  useEffect(() => {
    if (!open) return;

    let cancelled = false;

    setDocuments([]);
    setPrimaryId("");
    setComparisonIds([]);
    setLoading(true);
    setError("");

    async function loadDocuments() {
      try {
        const docs = await api.listDocuments();

        const session = sessions.find(
          s => s.id === sessionId
        );

        const ids = new Set(
          (session?.documents || []).map(
            d => typeof d === "string" ? d : d.id
          )
        );

        const filtered = docs.filter(d =>
          d.status === "Ready" &&
          (!sessionId || ids.has(d.id))
        );

        if (!cancelled) {
          setDocuments(filtered);
          setPrimaryId(filtered[0]?.id || "");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || "Unable to load documents.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadDocuments();

    return () => {
      cancelled = true;
    };
  }, [open, sessionId, sessions]);

  function toggleComparison(id) {
    setComparisonIds(prev =>
      prev.includes(id)
        ? prev.filter(x => x !== id)
        : prev.length < 10
          ? [...prev, id]
          : prev
    );
  }

  async function handleSubmit() {
    if (!primaryId || submitting) return;

    setSubmitting(true);
    setError("");

    try {
      await onGenerateReport({
        documentId: primaryId,
        comparisonDocumentIds: comparisonIds.filter(
          id => id !== primaryId
        ),
        sessionId
      });

      onClose();
    } catch (err) {
      setError(err.message || "Report generation failed.");
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) return null;

  return (
    <div className="fin-modal-overlay">
      <div className="fin-report-config-modal-card">
        <div className="modal-header-row">
          <h3 className="text-base font-bold text-main">
            <FileCheck2 size={20} />
            Configure Research Report
          </h3>

          <button
            className="modal-close-btn"
            onClick={onClose}
            disabled={submitting}
          >
            <X size={18} />
          </button>
        </div>

        <div className="modal-body-scroll config-form-body">
          <div className="config-form-group">
            <label className="config-label">
              Research Session
            </label>

            <select
              className="fin-select w-full"
              value={sessionId}
              disabled={submitting}
              onChange={e => setSessionId(e.target.value)}
            >
              <option value="">All my documents</option>

              {sessions.map(s => (
                <option key={s.id} value={s.id}>
                  {s.title}
                </option>
              ))}
            </select>
          </div>

          <div className="config-form-group mt-3">
            <label className="config-label">
              Primary Financial Document
            </label>

            {loading ? (
              <p>Loading documents...</p>
            ) : documents.length === 0 ? (
              <p className="text-muted">
                No indexed documents available.
                Upload and analyze a financial document first.
              </p>
            ) : (
              <select
                className="fin-select w-full"
                value={primaryId}
                disabled={submitting}
                onChange={e => {
                  setPrimaryId(e.target.value);
                  setComparisonIds(prev =>
                    prev.filter(id => id !== e.target.value)
                  );
                }}
              >
                {documents.map(doc => (
                  <option key={doc.id} value={doc.id}>
                    {doc.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="config-form-group mt-3">
            <label className="config-label">
              Comparison Documents (Optional)
            </label>

            {documents
              .filter(doc => doc.id !== primaryId)
              .map(doc => (
                <label
                  key={doc.id}
                  className="config-doc-item"
                >
                  <input
                    type="checkbox"
                    checked={comparisonIds.includes(doc.id)}
                    disabled={submitting}
                    onChange={() => toggleComparison(doc.id)}
                  />

                  <span>{doc.name}</span>
                </label>
              ))}
          </div>

          <div className="config-form-group mt-3">
            <label className="config-label">
              Report Sections
            </label>

            {[
              "Executive Summary",
              "Key Financials",
              "Red Flags",
              "Company Comparison",
              "Outlook"
            ].map(section => (
              <div key={section} className="config-doc-item">
                {section}
              </div>
            ))}

            <p className="text-xs text-muted">
              Sections without sufficient evidence will be
              marked unavailable.
            </p>
          </div>

          {error && (
            <p className="text-danger mt-3">
              {error}
            </p>
          )}
        </div>

        <div className="modal-footer-row">
          <button
            className="fin-btn fin-btn-secondary"
            onClick={onClose}
            disabled={submitting}
          >
            Cancel
          </button>

          <button
            className="fin-btn fin-btn-primary"
            disabled={loading || submitting || !primaryId}
            onClick={handleSubmit}
          >
            <Sparkles size={14} />

            {submitting
              ? "Generating Report..."
              : "Generate Report"}
          </button>
        </div>
      </div>
    </div>
  );
}