"""Extraction Agent Service.

Coordinates extraction of financial metrics, persistence in ai_financial_metrics,
and audit trail tracking in ai_agent_runs.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.extraction_agent.extractor import MetricExtractor
from app.infrastructure.database import DatabaseRepositoryInterface, get_database_repository
from app.infrastructure.vector_store import VectorStoreInterface, get_vector_store
from app.schemas.agents import ExtractedFinancials, ExtractedMetric
from app.infrastructure.vector_store.ownership import (
    get_owned_document_chunks
)
logger = logging.getLogger(__name__)


class ExtractionAgentService:
    """Production service coordinating structured financial information extraction."""

    def __init__(
        self,
        repository: Optional[DatabaseRepositoryInterface] = None,
        vector_store: Optional[VectorStoreInterface] = None,
        extractor: Optional[MetricExtractor] = None,
    ):
        self.repo = repository or get_database_repository()
        self.vector_store = vector_store or get_vector_store()
        self.extractor = extractor or MetricExtractor()

    def extract_document_financials(
        self,
        document_id: str,
        session_id: Optional[str] = None,
        chunks: Optional[List[Dict[str, Any]]] = None,
        *,
        user_id: str,
    ) -> ExtractedFinancials:

        
        """Execute full financial extraction pipeline for a document."""

        document = self.repo.get_user_document(
            document_id, user_id
        )

        if not document:
            raise ValueError("Document not found.")
        logger.info("Starting financial extraction for document: %s", document_id)
        doc = self.repo.get_document_by_id(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found in database.")

        filename = doc.get("filename", "document.pdf")
        company_name = doc.get("metadata", {}).get("company_name")

        # 1. Gather document chunks (from argument or vector store retrieval)
        doc_chunks = chunks
        if not doc_chunks:
            doc_chunks = get_owned_document_chunks(
                repository=self.repo,
                vector_store=self.vector_store,
                document_id=document_id,
                user_id=user_id
            )
            
        # 2. Execute extraction
        financials = self.extractor.extract_from_chunks(
            document_id=document_id,
            filename=filename,
            chunks=doc_chunks or [],
            company_name=company_name,
        )

        # 3. Persist extracted metrics to repository
        metrics_to_store: List[Dict[str, Any]] = []
        all_metrics: Dict[str, ExtractedMetric] = {}
        all_metrics.update(financials.income_statement)
        all_metrics.update(financials.balance_sheet)
        all_metrics.update(financials.cash_flow)
        all_metrics.update(financials.ratios)

        for name, m in all_metrics.items():
            metrics_to_store.append({
                "metric_name": m.name,
                "source_label": m.raw_text,
                "numeric_value": str(m.value),
                "currency": m.currency,
                "unit": m.unit,
                "period_type": m.period.value,
                "fiscal_year": m.fiscal_year,
                "statement_type": "KEY_RATIOS" if m.is_calculated else ("INCOME_STATEMENT" if name in financials.income_statement else "BALANCE_SHEET"),
                "is_calculated": m.is_calculated,
                "formula": m.formula,
                "is_consolidated": m.is_consolidated,
                "citation": {
                    "document_id": m.citation.document_id,
                    "page_number": m.citation.page_number,
                    "exact_quote": m.citation.exact_quote,
                    "table_index": m.citation.table_index,
                },
            })

        stored_count = self.repo.store_financial_metrics(document_id, metrics_to_store)
        logger.info("Successfully persisted %d financial metrics for document %s", stored_count, document_id)

        # 4. Record agent run in ai_agent_runs
        self.repo.record_agent_run(
            document_id=document_id,
            session_id=session_id,
            agent_name="EXTRACTION_AGENT",
            status="COMPLETED",
            input_payload={"chunks_count": len(doc_chunks or [])},
            output_payload={"metrics_extracted": len(all_metrics)},
        )

        return financials

    def get_extracted_financials(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored financial metrics for document structured by statement."""
        metrics = self.repo.get_financial_metrics(document_id)
        if not metrics:
            return None

        doc = self.repo.get_document_by_id(document_id)
        income_stmt = {}
        balance_sheet = {}
        cash_flow = {}
        ratios = {}

        for m in metrics:
            st = m.get("statement_type", "")
            name = m["metric_name"]
            if st == "INCOME_STATEMENT":
                income_stmt[name] = m
            elif st == "BALANCE_SHEET":
                balance_sheet[name] = m
            elif st == "CASH_FLOW":
                cash_flow[name] = m
            elif st == "KEY_RATIOS" or m.get("is_calculated"):
                ratios[name] = m
            else:
                income_stmt[name] = m

        company_name = ""
        if doc and doc.get("metadata"):
            company_name = doc.get("metadata", {}).get("company_name", "")

        return {
            "document_id": document_id,
            "filename": doc.get("filename") if doc else "",
            "company_name": company_name,
            "total_metrics": len(metrics),
            "metrics": {m["metric_name"]: m for m in metrics},
            "income_statement": income_stmt,
            "balance_sheet": balance_sheet,
            "cash_flow": cash_flow,
            "ratios": ratios,
        }

