import React, {
  useState,
  useEffect,
  useCallback
} from "react";

import {
  RefreshCw,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  Cpu
} from "lucide-react";

import Button from "../components/ui/Button";
import api from "../services/api";

import {
  PIPELINE_STAGES,
  getCompletedStages,
  getPipelineSummary
} from "../data/liveOrchestrationData";

export default function OrchestrationView({
  setPage
}) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [selectedId, setSelectedId] = useState("");

  const refreshDocuments = useCallback(async () => {
    try {
      const result = await api.listDocuments();

      setDocuments(result);
      setLastUpdated(new Date());
      setError("");

      setSelectedId(previous =>
        result.some(d => d.id === previous)
          ? previous
          : result[0]?.id || ""
      );
    } catch (err) {
      setError(
        err.message || "Unable to load processing data"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshDocuments();

    const timer = setInterval(
      refreshDocuments,
      5000
    );

    return () => clearInterval(timer);
  }, [refreshDocuments]);

  const summary = getPipelineSummary(documents);

  const selectedDocument = documents.find(
    d => d.id === selectedId
  );

  const completedStages = selectedDocument
    ? getCompletedStages(selectedDocument)
    : 0;

  const statistics = [
    {
      label: "Total Documents",
      value: summary.total
    },
    {
      label: "Queued",
      value: summary.queued
    },
    {
      label: "Processing",
      value: summary.processing
    },
    {
      label: "Completed",
      value: summary.completed
    },
    {
      label: "Failed",
      value: summary.failed
    }
  ];

  return (
    <section className="page space-y-6">

      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-main">
            Multi-Agent Orchestrator
          </h1>

          <p className="text-xs text-muted mt-1">
            Live document processing and agent coordination
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          icon={RefreshCw}
          onClick={refreshDocuments}
        >
          Refresh
        </Button>
      </div>

      {lastUpdated && (
        <p className="text-xs text-muted">
          Last updated: {lastUpdated.toLocaleTimeString()}
          {" · "}Refreshes every 5 seconds
        </p>
      )}

      {error && (
        <div className="p-3 border rounded-lg text-red-500">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {statistics.map(item => (
          <div
            key={item.label}
            className="p-4 border rounded-xl"
          >
            <p className="text-xs text-muted">
              {item.label}
            </p>

            <h2 className="text-2xl font-bold mt-2">
              {item.value}
            </h2>
          </div>
        ))}
      </div>

      {loading ? (
        <p>Loading processing information...</p>
      ) : documents.length === 0 ? (
        <div className="p-6 border rounded-xl">
          <p>No documents available for processing.</p>

          <Button
            onClick={() => setPage?.("Document Library")}
          >
            Open Document Library
          </Button>
        </div>
      ) : (
        <>
          <div className="p-4 border rounded-xl space-y-4">

            <h2 className="font-bold">
              Pipeline Execution
            </h2>

            <select
              value={selectedId}
              onChange={e => setSelectedId(e.target.value)}
              className="w-full p-2 border rounded-lg bg-transparent"
            >
              {documents.map(doc => (
                <option key={doc.id} value={doc.id}>
                  {doc.name}
                </option>
              ))}
            </select>

            {selectedDocument && (
              <>
                <p className="text-sm">
                  Status: {selectedDocument.status}
                </p>

                <p className="text-xs text-muted">
                  Current stage:{" "}
                  {selectedDocument.processingStage
                    ?.replace(/_/g, " ") ||
                    "Not recorded"}
                </p>

                <div className="space-y-3">
                  {PIPELINE_STAGES.map((stage, index) => {
                    const done = index < completedStages;

                    return (
                      <div
                        key={stage.key}
                        className="flex items-center gap-3 p-3 border rounded-lg"
                      >
                        {done ? (
                          <CheckCircle2
                            size={20}
                            className="text-green-500"
                          />
                        ) : (
                          <Clock
                            size={20}
                            className="text-muted"
                          />
                        )}

                        <div className="flex-1">
                          <p className="font-semibold text-sm">
                            {stage.name}
                          </p>

                          <p className="text-xs text-muted">
                            {done
                              ? "Completed"
                              : "Completion not recorded"}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>

          <div className="p-4 border rounded-xl space-y-3">

            <h2 className="font-bold">
              Latest Document Processing Activity
            </h2>

            {documents.map(doc => (
              <div
                key={doc.id}
                className="flex items-center gap-3 p-3 border rounded-lg"
              >
                {doc.status === "Error" ? (
                  <AlertCircle
                    size={20}
                    className="text-red-500"
                  />
                ) : doc.status === "Ready" ? (
                  <CheckCircle2
                    size={20}
                    className="text-green-500"
                  />
                ) : (
                  <FileText size={20} />
                )}

                <div className="flex-1">
                  <p className="text-sm font-semibold">
                    {doc.name}
                  </p>

                  <p className="text-xs text-muted">
                    {doc.processingStage
                      ?.replace(/_/g, " ") ||
                      "No processing stage recorded"}
                  </p>
                </div>

                <span className="text-xs font-semibold">
                  {doc.status}
                </span>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="p-4 border rounded-xl space-y-3">

        <h2 className="font-bold">
          On-Demand Research Agents
        </h2>

        {[
          ["Comparison Agent", "Company benchmarking"],
          ["Research Agent", "Source-grounded questions"],
          ["Report Agent", "Financial report generation"]
        ].map(([name, description]) => (
          <div
            key={name}
            className="flex items-center gap-3 p-3 border rounded-lg"
          >
            <Cpu size={20} />

            <div className="flex-1">
              <p className="text-sm font-semibold">
                {name}
              </p>

              <p className="text-xs text-muted">
                {description}
              </p>
            </div>

            <span className="text-xs text-muted">
              On demand
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}