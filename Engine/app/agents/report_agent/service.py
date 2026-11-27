"""Report Agent — initial Milestone 3.4 implementation.

Builds an analyst-style report skeleton and generates the two sections required
for Milestone 3: Executive Summary and Key Financials. Remaining sections are
declared as planned so the Milestone 4 PDF exporter can extend the same
structure without changing the API contract.

All content is generated from stored, evidence-validated metrics and red-flag
findings. No section fabricates a financial value.
"""

from __future__ import annotations
from app.agents.comparison_agent.service import ComparisonAgentService
import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from app.agents.research_agent.service import (
    _METRIC_LABELS,
    _PERCENT_METRICS,
    _RATIO_METRICS,
    format_metric_value,
)
from app.infrastructure.database import DatabaseRepositoryInterface, get_database_repository
from app.schemas.research import AgentCitation, GeneratedReport, ReportSection

logger = logging.getLogger(__name__)

STATEMENT_TITLES = {
    "INCOME_STATEMENT": "Income Statement",
    "BALANCE_SHEET": "Balance Sheet",
    "CASH_FLOW": "Cash Flow Statement",
    "KEY_RATIOS": "Key Ratios",
}

PLANNED_SECTIONS = []

def _decimal(value: Any) -> Optional[Decimal]:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


class ReportAgentService:
    """Compiles validated agent outputs into structured report sections."""

    def __init__(self, repository: Optional[DatabaseRepositoryInterface] = None):
        self.repo = repository or get_database_repository()
        # Extensible section registry: Milestone 4 adds red_flags, comparison, outlook.
        self.section_builders = {
            "executive_summary": self._build_executive_summary,
            "key_financials": self._build_key_financials,
            "red_flags": self._build_red_flags,
            "company_comparison": self._build_company_comparison,
            "outlook": self._build_outlook,
        }

    def generate_report(
        self,
        document_id: str,
        *,
        user_id: str,
        comparison_document_ids: Optional[List[str]] = None,
    ) -> GeneratedReport:

        document_ids = list(dict.fromkeys(
            [document_id] + (comparison_document_ids or [])
        ))

        documents = []

        for doc_id in document_ids:
            doc = self.repo.get_user_document(
                document_id=doc_id,
                user_id=user_id
            )

            if not doc:
                raise ValueError("Document not found.")

            documents.append(doc)

        doc = documents[0]

        if any(
            d["workspace_id"] != doc["workspace_id"]
            for d in documents
        ):
            raise ValueError(
                "All documents must belong to the same workspace."
            )

        metrics = [
            m for m in self.repo.get_financial_metrics(document_id)
            if (m.get("citation") or {}).get("page_number")
            and (m.get("citation") or {}).get("exact_quote")
            and m.get("numeric_value") is not None
        ]

        if not metrics:
            raise ValueError(
                "No source-cited financial metrics found. "
                "Run the document analysis pipeline first."
            )

        metadata = doc.get("metadata") or {}

        company_name = (
            metadata.get("company_name")
            or doc.get("filename", "document.pdf")
            .rsplit(".", 1)[0]
            .replace("_", " ")
            .title()
        )

        fiscal_year = next(
            (
                m.get("fiscal_year")
                for m in metrics
                if m.get("fiscal_year")
            ),
            metadata.get("fiscal_year"),
        )

        findings = self.repo.get_red_flag_findings(document_id)

        context = {
            "document": doc,
            "metrics": metrics,
            "findings": findings,
            "company_name": company_name,
            "fiscal_year": int(fiscal_year) if fiscal_year else None,
            "document_ids": document_ids,
        }

        sections = [
            builder(**context)
            for builder in self.section_builders.values()
        ]

        citations = []
        seen = set()

        for section in sections:
            for citation in section.citations:
                key = (
                    citation.document_id,
                    citation.page_number,
                    citation.metric_name,
                    citation.exact_quote,
                )

                if key not in seen:
                    seen.add(key)
                    citations.append(citation)

        limitations = [
            "This report uses stored financial extraction and risk findings.",
            "Missing financial information is not estimated.",
            "Historical results do not establish future performance.",
            "The report is intended for educational research.",
        ]

        if len(metrics) < 5:
            limitations.append(
                "Limited extracted metrics restrict the analysis."
            )

        if any(m.get("is_calculated") for m in metrics):
            limitations.append(
                "Calculated ratios depend on cited financial inputs."
            )

        return GeneratedReport(
            report_id=uuid4().hex,
            document_id=document_id,
            company_name=company_name,
            fiscal_year=int(fiscal_year) if fiscal_year else None,
            title=f"{company_name} — Financial Research Report",
            generated_at=datetime.now(timezone.utc).isoformat(),
            status=(
                "COMPLETE"
                if all(s.status == "generated" for s in sections)
                else "COMPLETE_WITH_LIMITATIONS"
            ),
            sections=sections,
            planned_sections=[],
            citations=citations,
            limitations=limitations,
        )
    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_executive_summary(
        self,
        document: Dict[str, Any],
        metrics: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        company_name: str,
        fiscal_year: Optional[int],
        **_: Any,
    ) -> ReportSection:
        filename = document.get("filename", "document.pdf")
        metric_map = {m["metric_name"]: m for m in metrics}
        citations: List[AgentCitation] = []

        def describe(metric_name: str, label: Optional[str] = None) -> Optional[str]:
            metric = metric_map.get(metric_name)
            if not metric:
                return None
            citation = metric.get("citation") or {}
            page = citation.get("page_number")
            display = format_metric_value(
                metric_name,
                metric.get("numeric_value"),
                metric.get("unit", ""),
                metric.get("currency", ""),
            )
            page_text = f" (page {page})" if page is not None else ""
            if page is not None:
                citations.append(
                    AgentCitation(
                        document_id=document["document_id"],
                        document_name=filename,
                        company=company_name,
                        page_number=int(page),
                        exact_quote=str(citation.get("exact_quote") or ""),
                        metric_name=metric_name,
                        is_calculated=bool(metric.get("is_calculated")),
                    )
                )
            return f"{label or _METRIC_LABELS.get(metric_name, metric_name)} of {display}{page_text}"

        period = f"FY{fiscal_year}" if fiscal_year else "the reported period"
        lines: List[str] = [
            f"{company_name} reported its financial results for {period} in {filename}. "
            f"This summary is based only on {len(metrics)} extracted, source-cited metrics."
        ]

        performance: List[str] = []
        for metric_name in ("REVENUE", "NET_INCOME", "OPERATING_CASH_FLOW"):
            statement = describe(metric_name)
            if statement:
                performance.append(statement)
        if performance:
            lines.append("Reported performance includes " + "; ".join(performance) + ".")

        position: List[str] = []
        for metric_name in ("TOTAL_ASSETS", "TOTAL_LIABILITIES", "CURRENT_RATIO", "DEBT_TO_EQUITY"):
            statement = describe(metric_name)
            if statement:
                position.append(statement)
        if position:
            lines.append("Balance-sheet and ratio indicators include " + "; ".join(position) + ".")

        if findings:
            titles = "; ".join(
                f"{f.get('title')} ({f.get('severity')}, page {f.get('source_page')})"
                for f in findings[:4]
            )
            lines.append(
                f"The Red Flag Agent recorded {len(findings)} evidence-backed finding(s): {titles}."
            )
        else:
            lines.append(
                "The Red Flag Agent recorded no evidence-backed risk findings for this filing."
            )

        lines.append(
            "All figures above are traceable to the cited source pages. Figures not present in the "
            "document are not estimated."
        )

        return ReportSection(
            section_key="executive_summary",
            title="Executive Summary",
            status="generated",
            content_markdown="\n\n".join(lines),
            citations=citations,
        )

    def _build_key_financials(
        self,
        document: Dict[str, Any],
        metrics: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        company_name: str,
        fiscal_year: Optional[int],
        **_: Any,
    ) -> ReportSection:
        filename = document.get("filename", "document.pdf")
        citations: List[AgentCitation] = []
        lines: List[str] = [
            f"### Key Financials — {company_name}"
            + (f" (FY{fiscal_year})" if fiscal_year else ""),
            "",
        ]

        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for metric in metrics:
            grouped.setdefault(metric.get("statement_type", "INCOME_STATEMENT"), []).append(metric)

        for statement_type in ("INCOME_STATEMENT", "BALANCE_SHEET", "CASH_FLOW", "KEY_RATIOS"):
            group = grouped.get(statement_type)
            if not group:
                continue
            lines.append(f"**{STATEMENT_TITLES.get(statement_type, statement_type)}**")
            lines.append("")
            lines.append("| Metric | Reported Value | Unit | Source |")
            lines.append("| --- | --- | --- | --- |")
            for metric in group:
                metric_name = metric["metric_name"]
                citation = metric.get("citation") or {}
                page = citation.get("page_number")
                display = format_metric_value(
                    metric_name,
                    metric.get("numeric_value"),
                    metric.get("unit", ""),
                    metric.get("currency", ""),
                )
                label = _METRIC_LABELS.get(metric_name, metric_name.replace("_", " ").title())
                source = f"p. {page}" if page is not None else "Unavailable"
                if metric.get("is_calculated"):
                    source += " (calculated)"
                lines.append(
                    f"| {label} | {display} | {metric.get('currency', '')} {metric.get('unit', '')} | {source} |"
                )
                if page is not None:
                    citations.append(
                        AgentCitation(
                            document_id=document["document_id"],
                            document_name=filename,
                            company=company_name,
                            page_number=int(page),
                            exact_quote=str(citation.get("exact_quote") or ""),
                            metric_name=metric_name,
                            is_calculated=bool(metric.get("is_calculated")),
                        )
                    )
            lines.append("")

        lines.append(
            "_Only metrics extracted from the source filing are listed. Blank or missing line items "
            "are omitted rather than estimated._"
        )

        return ReportSection(
            section_key="key_financials",
            title="Key Financials",
            status="generated",
            content_markdown="\n".join(lines),
            citations=citations,
        )
    
    def _build_red_flags(
        self,
        document,
        findings,
        company_name,
        **_,
    ) -> ReportSection:

        lines = []
        citations = []

        for finding in findings:

            page = finding.get("source_page")
            evidence = finding.get("supporting_evidence")

            if not page or not evidence:
                continue

            title = finding.get("title", "Risk finding")
            severity = finding.get("severity", "Unknown")

            lines.append(
                f"### {title}\n"
                f"Severity: {severity}\n\n"
                f"{finding.get('description', '')}\n\n"
                f"Supporting evidence: {evidence}\n\n"
                f"Source: {document['filename']}, page {page}"
            )

            citations.append(
                AgentCitation(
                    document_id=document["document_id"],
                    document_name=document["filename"],
                    company=company_name,
                    page_number=int(page),
                    exact_quote=str(evidence),
                    section="red_flags",
                )
            )

        if not lines:
            lines.append(
                "No source-supported red flag findings "
                "are currently available. This does not "
                "establish that the company is risk-free."
            )

        return ReportSection(
            section_key="red_flags",
            title="Red Flags",
            status="generated" if citations else "unavailable",
            content_markdown="\n\n".join(lines),
            citations=citations,
        )

    def _build_company_comparison(
        self,
        document_ids,
        **_,
    ) -> ReportSection:

        if len(document_ids) < 2:
            return ReportSection(
                section_key="company_comparison",
                title="Company Comparison",
                status="unavailable",
                content_markdown=(
                    "Select at least two analyzed company "
                    "documents to generate a comparison."
                ),
            )

        service = ComparisonAgentService(
            repository=self.repo
        )

        comparison = service.compare_documents(
            document_ids=document_ids
        )

        valid_citations = [
            c for c in comparison.citations
            if c.page_number > 0 and c.exact_quote.strip()
        ]

        supported = {
            (c.document_id, c.metric_name)
            for c in valid_citations
        }

        lines = []
        included = 0

        for company in comparison.companies:

            lines.append(f"### {company.company_name}")

            lines.append(
                f"Reporting period: "
                f"{company.fiscal_year or 'Unavailable'}"
            )

            lines.append(
                "| Metric | Reported Value | Source |"
            )
            lines.append("| --- | --- | --- |")

            for metric in company.metrics:

                if (
                    company.document_id,
                    metric.metric_name
                ) not in supported:

                    lines.append(
                        f"| {metric.metric_name} "
                        "| Unavailable | — |"
                    )
                    continue

                label = _METRIC_LABELS.get(
                    metric.metric_name,
                    metric.metric_name
                )

                lines.append(
                    f"| {label} "
                    f"| {metric.display_value} "
                    f"| p. {metric.page_number} |"
                )

                included += 1

            lines.append("")

        lines.append("### Comparison limitations")

        for warning in comparison.warnings:
            lines.append(f"- {warning}")

        for limitation in comparison.limitations:
            lines.append(f"- {limitation}")

        return ReportSection(
            section_key="company_comparison",
            title="Company Comparison",
            status="generated" if included else "unavailable",
            content_markdown="\n".join(lines),
            citations=valid_citations,
        )
    def _build_outlook(
        self,
        document,
        metrics,
        company_name,
        **_,
    ) -> ReportSection:

        lines = [
            "The following indicators provide a historical "
            "basis for monitoring future financial performance. "
            "They are not forecasts."
        ]

        citations = []

        indicators = {
            "REVENUE": "Revenue performance",
            "NET_INCOME": "Profitability",
            "OPERATING_MARGIN": "Operating efficiency",
            "DEBT_TO_EQUITY": "Financial leverage",
            "CURRENT_RATIO": "Short-term liquidity",
            "OPERATING_CASH_FLOW": "Cash generation",
        }

        for metric in metrics:

            name = metric.get("metric_name")

            if name not in indicators:
                continue

            citation = metric.get("citation") or {}
            page = citation.get("page_number")
            quote = citation.get("exact_quote")

            if not page or not quote:
                continue

            display = format_metric_value(
                name,
                metric.get("numeric_value"),
                metric.get("unit", ""),
                metric.get("currency", ""),
            )

            lines.append(
                f"- {indicators[name]}: "
                f"{display} (page {page})."
            )

            citations.append(
                AgentCitation(
                    document_id=document["document_id"],
                    document_name=document["filename"],
                    company=company_name,
                    page_number=int(page),
                    exact_quote=str(quote),
                    metric_name=name,
                    is_calculated=bool(
                        metric.get("is_calculated")
                    ),
                    section="outlook",
                )
            )

        lines.append(
            "Future revenue, earnings, growth rates and "
            "share prices cannot be established from "
            "these historical metrics alone."
        )

        return ReportSection(
            section_key="outlook",
            title="Outlook",
            status="generated" if citations else "unavailable",
            content_markdown="\n\n".join(lines),
            citations=citations,
        )
