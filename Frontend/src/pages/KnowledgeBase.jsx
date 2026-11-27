import React, {
  useState,
  useEffect,
  useMemo
} from "react";

import {
  Database,
  Search,
  RefreshCw,
  FileText,
  Layers,
  CheckCircle2
} from "lucide-react";

import Button from "../components/ui/Button";
import api from "../services/api";
import RetrievalPreview from "./RetrievalPreview";

export default function KnowledgeBase({
  sessions = [],
  activeSession,
  setActiveSession,
  setPage,
  initialTab = "indexing"
}) {
  const [documents, setDocuments] = useState([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  const [activeTab, setActiveTab] = useState(
    initialTab === "retrieval"
      ? "retrieval"
      : "indexing"
  );

  useEffect(() => {
    let cancelled = false;
    let timer;

    async function loadDocuments() {
      try {
        const result = await api.listDocuments();

        if (!cancelled) {
          setDocuments(result);
          setError("");
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err.message || "Unable to load Knowledge Base"
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
          timer = setTimeout(loadDocuments, 5000);
        }
      }
    }

    loadDocuments();

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [refreshKey]);

  const indexedDocuments = documents.filter(
    doc => doc.indexed
  );

  const totalChunks = indexedDocuments.reduce(
    (sum, doc) => sum + (Number(doc.chunkCount) || 0),
    0
  );

  const processingCount = documents.filter(
    doc => ["Queued", "Processing"].includes(doc.status)
  ).length;

  const failedCount = documents.filter(
    doc => doc.status === "Error"
  ).length;

  const filteredDocuments = useMemo(() => {
    const search = query.toLowerCase().trim();

    return documents.filter(doc => {
      const matchesSearch = [
        doc.name,
        doc.company,
        doc.ticker
      ].some(value =>
        String(value || "")
          .toLowerCase()
          .includes(search)
      );

      const matchesStatus =
        status === "all" ||
        doc.status === status;

      return matchesSearch && matchesStatus;
    });
  }, [documents, query, status]);

  const selectedDocument = documents.find(
    doc => doc.id === selectedId
  );

  const statistics = [
    ["Indexed Documents", indexedDocuments.length],
    ["Indexed Chunks", totalChunks],
    ["Processing / Queued", processingCount],
    ["Failed Documents", failedCount]
  ];

  return (
    <section className="page space-y-6">

      <div className="flex items-center justify-between flex-wrap gap-3">

        <div>
          <h1 className="text-2xl font-bold text-main">
            Knowledge Base
          </h1>

          <p className="text-xs text-muted mt-1">
            Embedding generation and vector database
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          icon={RefreshCw}
          onClick={() => setRefreshKey(v => v + 1)}
        >
          Refresh
        </Button>

      </div>

      {error && (
        <div className="p-3 border rounded-lg text-red-500">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">

        {statistics.map(([label, value]) => (
          <div
            key={label}
            className="p-4 border rounded-xl"
          >
            <p className="text-xs text-muted">
              {label}
            </p>

            <h2 className="text-2xl font-bold mt-2">
              {value.toLocaleString()}
            </h2>
          </div>
        ))}

      </div>

      <div className="flex gap-3 flex-wrap">

        <Button
          onClick={() => setActiveTab("indexing")}
        >
          Document Index
        </Button>

        <Button
          onClick={() => setActiveTab("retrieval")}
        >
          Retrieval Preview
        </Button>

      </div>

      {activeTab === "retrieval" ? (
        <RetrievalPreview
          sessions={sessions}
          activeSession={activeSession}
          setActiveSession={setActiveSession}
          setPage={setPage}
        />
      ) : (
        <>

          <div className="flex gap-3 flex-wrap">

            <div className="flex items-center gap-2 border rounded-lg p-2 flex-1">

              <Search size={16} />

              <input
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search documents or companies..."
                className="bg-transparent outline-none w-full"
              />

            </div>

            <select
              value={status}
              onChange={e => setStatus(e.target.value)}
              className="p-2 border rounded-lg bg-transparent"
            >
              {[
                "all",
                "Ready",
                "Indexed",
                "Queued",
                "Processing",
                "Uploaded",
                "Cancelled",
                "Error"
              ].map(value => (
                <option key={value} value={value}>
                  {value === "all" ? "All statuses" : value}
                </option>
              ))}
            </select>

          </div>

          {loading ? (
            <p>Loading Knowledge Base...</p>
          ) : filteredDocuments.length === 0 ? (
            <div className="p-6 border rounded-xl">

              <Database size={28} />

              <p className="mt-3">
                No matching documents available.
              </p>

            </div>
          ) : (
            <div className="overflow-x-auto border rounded-xl">

              <table className="w-full text-sm">

                <thead>
                  <tr className="border-b text-left">
                    {[
                      "Document",
                      "Company",
                      "Chunks",
                      "Vector Index",
                      "Status",
                      "Action"
                    ].map(label => (
                      <th key={label} className="p-3">
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody>

                  {filteredDocuments.map(doc => (
                    <tr key={doc.id} className="border-b">

                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <FileText size={16} />
                          {doc.name}
                        </div>
                      </td>

                      <td className="p-3">
                        {doc.company || "Not available"}
                      </td>

                      <td className="p-3">
                        {doc.chunkCount ?? "Not available"}
                      </td>

                      <td className="p-3">
                        {doc.indexed ? (
                          <span className="flex items-center gap-1 text-green-500">
                            <CheckCircle2 size={15} />
                            Indexed
                          </span>
                        ) : (
                          "Not indexed"
                        )}
                      </td>

                      <td className="p-3">
                        {doc.status}
                      </td>

                      <td className="p-3">
                        <Button
                          size="sm"
                          onClick={() => setSelectedId(doc.id)}
                        >
                          Details
                        </Button>
                      </td>

                    </tr>
                  ))}

                </tbody>

              </table>

            </div>
          )}

          {selectedDocument && (
            <div className="p-5 border rounded-xl space-y-3">

              <div className="flex justify-between items-center">

                <h2 className="font-bold flex items-center gap-2">
                  <Layers size={18} />
                  Document Index Details
                </h2>

                <Button
                  size="sm"
                  onClick={() => setSelectedId("")}
                >
                  Close
                </Button>

              </div>

              {[
                ["Document", selectedDocument.name],
                ["Company", selectedDocument.company],
                ["Document Type", selectedDocument.docType],
                ["File Size", selectedDocument.fileSize],
                ["Chunk Count", selectedDocument.chunkCount],
                ["Embedding Model", selectedDocument.embeddingModel],
                ["Checksum", selectedDocument.checksum],
                ["Workspace", selectedDocument.workspaceId],
                ["Processing Status", selectedDocument.status],
                ["Current Stage", selectedDocument.processingStage]
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="grid grid-cols-2 gap-3 border-b pb-2 text-sm"
                >
                  <span className="text-muted">
                    {label}
                  </span>

                  <span className="break-all">
                    {value ?? "Not available"}
                  </span>
                </div>
              ))}

            </div>
          )}

        </>
      )}

    </section>
  );
}