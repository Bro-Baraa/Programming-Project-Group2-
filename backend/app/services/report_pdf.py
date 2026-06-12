"""PDF report generation for final internship reports."""

import tempfile
from pathlib import Path

from fpdf import FPDF
from sqlalchemy.orm import Session

from app.schemas import UserResponse
from app.services.report_final import get_final_report


class _PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(18, 38, 58)
        self.cell(0, 12, "Stage Monitoring Tool - Eindrapport", ln=True, align="L")
        self.set_draw_color(0, 121, 140)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")


def _safe(text) -> str:
    return str(text) if text is not None else ""


def generate_final_report_pdf(
    db: Session,
    current_user,
    internship_id: int,
) -> tuple[Path, "UserResponse"]:
    report = get_final_report(db, current_user, internship_id)

    pdf = _PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(18, 38, 58)
    pdf.cell(0, 8, "1. Algemene Informatie", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 10)
    info_rows = [
        ("Student", f"{report.student.first_name} {report.student.last_name}"),
        ("Bedrijf", report.company_name or "Onbekend"),
        ("Periode", f"{report.start_date} tot {report.end_date}"),
        ("Status voorstel", report.proposal_status),
        ("Status overeenkomst", report.agreement_status),
    ]
    for label, value in info_rows:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(55, 6, f"{label}:", ln=0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, _safe(value), ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(18, 38, 58)
    pdf.cell(0, 8, "2. Logboek Overzicht", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Totaal aantal weken: {report.total_weeks}", ln=True)
    pdf.cell(0, 6, f"Ingediende logboeken: {report.submitted_logbooks}", ln=True)
    pdf.cell(0, 6, f"Ontbrekende logboeken: {report.missing_logbooks}", ln=True)
    pdf.ln(4)

    if report.final_evaluation:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(18, 38, 58)
        pdf.cell(0, 8, "3. Competentie-evaluatie", ln=True)
        pdf.ln(1)

        if report.weighted_final_score is not None:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(0, 121, 140)
            pdf.cell(
                0,
                8,
                f"Gewogen eindscore: {report.weighted_final_score:.2f} / 100",
                ln=True,
            )
            pdf.ln(2)

        pdf.set_fill_color(240, 248, 252)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(18, 38, 58)
        col_w = [55, 25, 20, 45, 45]
        headers = ["Competentie", "Gewicht", "Score", "Beschrijving", "Feedback"]
        for w, h in zip(col_w, headers):
            pdf.cell(w, 8, h, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        for rule in report.final_evaluation.rules:
            competency = rule.competency
            name = competency.name if competency else "Onbekend"
            weight = f"{competency.weight:.1f}%" if competency else "-"
            score = str(rule.score) if rule.score is not None else "-"
            desc = rule.student_description or "-"
            feedback = rule.evaluator_feedback or "-"

            start_x = pdf.get_x()
            start_y = pdf.get_y()
            line_height = 6

            desc_h = pdf.get_string_height(col_w[3], _safe(desc))
            feedback_h = pdf.get_string_height(col_w[4], _safe(feedback))
            row_h = max(8, desc_h, feedback_h)

            pdf.set_xy(start_x, start_y)
            pdf.cell(col_w[0], row_h, _safe(name), border=1)
            pdf.cell(col_w[1], row_h, weight, border=1, align="C")
            pdf.cell(col_w[2], row_h, score, border=1, align="C")

            pdf.multi_cell(col_w[3], line_height, _safe(desc), border=1)
            new_y = pdf.get_y()
            pdf.set_xy(start_x + sum(col_w[:4]), start_y)
            pdf.multi_cell(col_w[4], line_height, _safe(feedback), border=1)
            pdf.set_y(max(new_y, pdf.get_y()))

        pdf.ln(4)

        if report.final_evaluation.comments:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Algemene opmerkingen:", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, _safe(report.final_evaluation.comments))
            pdf.ln(2)
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 8, "Geen gefinalizeerde evaluatie beschikbaar.", ln=True)

    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(18, 38, 58)
    pdf.cell(0, 8, "4. Handtekeningen", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    sig_y = pdf.get_y()
    pdf.cell(95, 8, "Student:", ln=0)
    pdf.cell(0, 8, "Stagebegeleider:", ln=True)
    pdf.line(10, sig_y + 18, 95, sig_y + 18)
    pdf.line(105, sig_y + 18, 190, sig_y + 18)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    tmp.close()
    return Path(tmp.name), report.student
