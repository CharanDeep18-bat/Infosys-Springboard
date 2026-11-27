from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.research import GeneratedReport


class ReportPDFExporter:

    def __init__(self):

        self.styles = getSampleStyleSheet()

        self.styles.add(ParagraphStyle(
            name="ReportBody",
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            spaceAfter=8,
            textColor=colors.HexColor("#334155"),
            splitLongWords=True,
        ))

        self.styles.add(ParagraphStyle(
            name="ReportHeading",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=21,
            spaceBefore=18,
            spaceAfter=10,
            textColor=colors.HexColor("#0F766E"),
            keepWithNext=True,
        ))

        self.styles.add(ParagraphStyle(
            name="ReportCitation",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            spaceAfter=8,
            textColor=colors.HexColor("#475569"),
        ))

    def paragraph(self, text, style="ReportBody"):

        return Paragraph(
            escape(str(text)),
            self.styles[style],
        )

    def build_table(self, rows, width):

        column_count = len(rows[0])

        rows = [
            [
                self.paragraph(cell)
                for cell in row
            ]
            for row in rows
            if len(row) == column_count
        ]

        table = Table(
            rows,
            colWidths=[width / column_count] * column_count,
            repeatRows=1,
            hAlign="LEFT",
        )

        table.setStyle(TableStyle([
            (
                "BACKGROUND",
                (0, 0), (-1, 0),
                colors.HexColor("#DCEFEA"),
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1), (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F8FAFC"),
                ],
            ),
            (
                "GRID",
                (0, 0), (-1, -1),
                0.4,
                colors.HexColor("#CBD5E1"),
            ),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))

        return table

    def render_markdown(self, content, story, width):

        table_rows = []

        def flush_table():

            if table_rows:
                story.append(
                    self.build_table(table_rows, width)
                )
                story.append(Spacer(1, 10))
                table_rows.clear()

        for raw_line in content.splitlines():

            line = raw_line.strip()

            if line.startswith("|"):

                cells = [
                    cell.strip()
                    for cell in line.strip("|").split("|")
                ]

                if all(
                    cell
                    and set(cell) <= set("-: ")
                    for cell in cells
                ):
                    continue

                table_rows.append(cells)
                continue

            flush_table()

            if not line:
                continue

            if line.startswith("#"):

                story.append(self.paragraph(
                    line.lstrip("#").strip(),
                    "Heading3",
                ))

            elif (
                line.startswith("**")
                and line.endswith("**")
            ):

                story.append(self.paragraph(
                    line.strip("*"),
                    "Heading3",
                ))

            elif line.startswith("- "):

                story.append(self.paragraph(
                    "• " + line[2:]
                ))

            else:

                story.append(
                    self.paragraph(line.strip("_"))
                )

        flush_table()

    def page_footer(self, canvas, doc):

        canvas.saveState()

        width, height = A4

        canvas.setStrokeColor(
            colors.HexColor("#CBD5E1")
        )

        canvas.line(42, 42, width - 42, 42)

        canvas.setFont("Helvetica", 8)

        canvas.setFillColor(
            colors.HexColor("#64748B")
        )

        canvas.drawString(
            42, 28,
            "FinResearch AI | Financial Research Report"
        )

        canvas.drawRightString(
            width - 42, 28,
            f"Page {doc.page}"
        )

        canvas.restoreState()

    def generate(self, report: GeneratedReport) -> bytes:

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=42,
            leftMargin=42,
            topMargin=45,
            bottomMargin=60,
            title=report.title,
            author="FinResearch AI",
        )

        story = []

        story.append(self.paragraph(
            "FINRESEARCH AI",
            "Heading2",
        ))

        story.append(self.paragraph(
            report.title,
            "Title",
        ))

        story.append(Spacer(1, 10))

        story.append(self.paragraph(
            f"Company: {report.company_name}"
        ))

        story.append(self.paragraph(
            f"Fiscal year: "
            f"{report.fiscal_year or 'Unavailable'}"
        ))

        story.append(self.paragraph(
            f"Generated: {report.generated_at}"
        ))

        story.append(self.paragraph(
            f"Report ID: {report.report_id}"
        ))

        story.append(self.paragraph(
            f"Status: {report.status}"
        ))

        for index, section in enumerate(
            report.sections, start=1
        ):

            story.append(self.paragraph(
                f"{index}. {section.title}",
                "ReportHeading",
            ))

            if section.status != "generated":

                story.append(self.paragraph(
                    f"Section status: {section.status}"
                ))

            self.render_markdown(
                section.content_markdown,
                story,
                doc.width,
            )

            if section.citations:

                story.append(self.paragraph(
                    "Section Sources",
                    "Heading3",
                ))

                for citation in section.citations:

                    story.append(self.paragraph(
                        f"{citation.document_name} | "
                        f"Page {citation.page_number} | "
                        f"{citation.metric_name or 'Evidence'}",
                        "ReportCitation",
                    ))

                    story.append(self.paragraph(
                        f"Evidence: {citation.exact_quote}",
                        "ReportCitation",
                    ))

                    if citation.is_calculated:

                        story.append(self.paragraph(
                            "Calculated financial indicator.",
                            "ReportCitation",
                        ))

        story.append(self.paragraph(
            "Limitations",
            "ReportHeading",
        ))

        for limitation in report.limitations:

            story.append(self.paragraph(
                "• " + limitation
            ))

        doc.build(
            story,
            onFirstPage=self.page_footer,
            onLaterPages=self.page_footer,
        )

        return buffer.getvalue()