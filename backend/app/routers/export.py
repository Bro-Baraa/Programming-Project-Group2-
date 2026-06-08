"""
Export router — genereert een PDF-rapport voor een stage.

Toegankelijk voor: docenten, mentors, commissieleden, admins.
Studenten kunnen hun eigen stage NIET exporteren (privacy + scope).

Endpoint:
    GET /internships/{internship_id}/export/pdf

Geeft een PDF terug als download (geen bestand op schijf opgeslagen).
"""

import io
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Internship, Logbook, Evaluation, EvaluationRule, User
from app.auth import get_current_active_user
from app.services.common import ensure_internship_access
from app.services.evaluations import calculate_evaluation_score
from app.services.audit import log_event

# ReportLab imports — voor het bouwen van de PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

router = APIRouter(prefix="/internships", tags=["export"])

# Rollen die een PDF-export mogen aanvragen
ALLOWED_ROLES = {"teacher", "mentor", "committee", "admin"}


@router.get("/{internship_id}/export/pdf")
def export_internship_pdf(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Exporteer alle stagegegevens als PDF.
    Bevat: studentinfo, bedrijf, voorstel, overeenkomst, logboeken en evaluaties.
    """

    # --- 1. Toegangscontrole ---
    if current_user.role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Alleen docenten, mentors en admins kunnen een PDF exporteren."
        )

    # --- 2. Stage ophalen met alle relaties in één query (efficiënter) ---
    internship = (
        db.query(Internship)
        .options(
            joinedload(Internship.student),
            joinedload(Internship.teacher),
            joinedload(Internship.mentor),
            joinedload(Internship.company),
            joinedload(Internship.proposal),
            joinedload(Internship.agreement),
            joinedload(Internship.logbooks),
            joinedload(Internship.evaluations).joinedload(Evaluation.rules).joinedload(EvaluationRule.competency),
            joinedload(Internship.evaluations).joinedload(Evaluation.evaluator),
        )
        .filter(Internship.id == internship_id)
        .first()
    )

    if not internship:
        raise HTTPException(status_code=404, detail="Stage niet gevonden.")

    # Mentors mogen enkel hun eigen stages exporteren
    ensure_internship_access(current_user, internship, "Geen toegang tot deze stage.")

    # --- 3. PDF opbouwen in geheugen (geen bestand op schijf) ---
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # ── Kleuren rechtstreeks uit de app CSS variabelen ──
    C_INK        = colors.HexColor("#12263a")  # --ink
    C_INK_SOFT   = colors.HexColor("#425466")  # --ink-soft
    C_ACCENT     = colors.HexColor("#c73d50")  # --accent (rood, voor titel/accenten)
    C_ACCENT_2   = colors.HexColor("#00798c")  # --accent-2 (teal, voor sectiekoppen)
    C_BG_2       = colors.HexColor("#d9e6f2")  # --bg-2 (lichtblauw, tabelheaders)
    C_BORDER     = colors.HexColor("#dce5ee")  # afgeleid van --border
    C_ROW_ALT    = colors.HexColor("#f4f8fb")  # subtiele alternatieve rij
    C_GOOD       = colors.HexColor("#3c9d78")  # --good
    C_GOOD_BG    = colors.HexColor("#e8f6f1")  # --good-bg
    C_WHITE      = colors.white

    # Aangepaste stijlen voor dit rapport
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=4,
        textColor=C_ACCENT,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=13,
        spaceAfter=4,
        textColor=C_INK,
        fontName="Helvetica-Bold",
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Normal"],
        fontSize=11,
        textColor=C_WHITE,
        fontName="Helvetica-Bold",
        leading=14,
    )

    def section_heading(text):
        """Sectietitel als tabel — zo werkt padding op de achtergrond wél correct."""
        t = Table([[Paragraph(text, section_style)]], colWidths=[17 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), C_ACCENT_2),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ]))
        return t
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=8,
        textColor=C_INK_SOFT,
        spaceAfter=1,
        fontName="Helvetica-Bold",
    )
    value_style = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontSize=9,
        spaceAfter=5,
        textColor=C_INK,
    )
    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=7.5,
        textColor=C_INK_SOFT,
    )

    # Gemeenschappelijke tabelstijl
    base_table_style = TableStyle([
        # Header rij — teal achtergrond, witte tekst
        ("BACKGROUND",    (0, 0), (-1, 0),  C_BG_2),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  C_INK),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  8),
        # Data rijen
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("TEXTCOLOR",     (0, 1), (-1, -1), C_INK),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_ROW_ALT]),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        # Raster — subtiele border kleur
        ("GRID",          (0, 0), (-1, -1), 0.5, C_BORDER),
        ("LINEBELOW",     (0, 0), (-1, 0),  1,   C_ACCENT_2),  # dikke lijn onder header
    ])

    # Sleuteltabel stijl (2 kolommen: label | waarde)
    key_value_style = TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("FONTNAME",      (0, 0), (0, -1),  "Helvetica-Bold"),  # linkerkolom vet
        ("TEXTCOLOR",     (0, 0), (0, -1),  C_INK_SOFT),
        ("TEXTCOLOR",     (1, 0), (1, -1),  C_INK),
        ("GRID",          (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [C_WHITE, C_ROW_ALT]),
    ])

    # Herbruikbare stijl voor tekst binnen tabelcellen (zorgt voor word-wrap)
    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=C_INK,
    )
    cell_bold_style = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        fontName="Helvetica-Bold",
        textColor=C_INK,
    )

    # Bouw de inhoud op als een lijst van "Flowable" elementen
    story = []

    # ── Titelblok ──
    student = internship.student
    student_name = f"{student.first_name} {student.last_name}" if student else "Onbekende student"
    company_name = internship.company.name if internship.company else "-"

    story.append(Paragraph("Stage Rapport", title_style))
    story.append(Paragraph(f"{student_name} — {company_name}", subtitle_style))
    story.append(Paragraph(
        f"Gegenereerd op: {date.today().strftime('%d/%m/%Y')} | Exporteur: {current_user.first_name} {current_user.last_name} ({current_user.role})",
        small_style,
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=C_ACCENT, spaceBefore=6, spaceAfter=10))

    # ── Sectie 1: Studentinformatie ──
    story.append(Spacer(1, 14))
    story.append(section_heading("1. Studentinformatie"))
    if student:
        student_data = [
            ["Voornaam", student.first_name or "-"],
            ["Achternaam", student.last_name or "-"],
            ["E-mail", student.email or "-"],
        ]
        t = Table(student_data, colWidths=[4 * cm, 13 * cm])
        t.setStyle(key_value_style)
        story.append(t)
    else:
        story.append(Paragraph("Geen studentgegevens beschikbaar.", value_style))

    # ── Sectie 2: Stagegegevens ──
    story.append(Spacer(1, 14))
    story.append(section_heading("2. Stagegegevens"))
    teacher = internship.teacher
    mentor = internship.mentor
    internship_data = [
        ["Status", internship.status or "-"],
        ["Startdatum", str(internship.start_date) if internship.start_date else "-"],
        ["Einddatum", str(internship.end_date) if internship.end_date else "-"],
        ["Verantwoordelijk docent", f"{teacher.first_name} {teacher.last_name}" if teacher else "-"],
        ["Mentor (bedrijf)", f"{mentor.first_name} {mentor.last_name}" if mentor else "-"],
    ]
    t = Table(internship_data, colWidths=[5 * cm, 12 * cm])
    t.setStyle(key_value_style)
    story.append(t)

    # ── Sectie 3: Bedrijfsinformatie ──
    story.append(Spacer(1, 14))
    story.append(section_heading("3. Bedrijf"))
    company = internship.company
    if company:
        company_data = [
            ["Naam", company.name or "-"],
            ["Adres", company.address or "-"],
            ["Sector", company.sector or "-"],
            ["Contactpersoon", company.contact_person or "-"],
            ["Contact e-mail", company.contact_email or "-"],
        ]
        t = Table(company_data, colWidths=[4 * cm, 13 * cm])
        t.setStyle(key_value_style)
        story.append(t)
    else:
        story.append(Paragraph("Geen bedrijfsinformatie beschikbaar.", value_style))

    # ── Sectie 4: Stagevoorstel ──
    story.append(Spacer(1, 14))
    story.append(section_heading("4. Stagevoorstel"))
    story.append(Spacer(1, 6))
    proposal = internship.proposal
    if proposal:
        story.append(Paragraph(f"<b>Status:</b> {proposal.status}", value_style))
        story.append(Paragraph(f"<b>Ingediend op:</b> {proposal.submitted_at.strftime('%d/%m/%Y %H:%M') if proposal.submitted_at else '-'}", value_style))
        story.append(Paragraph("<b>Beschrijving:</b>", label_style))
        # Escape HTML-tekens in de beschrijving voor veilige rendering
        safe_description = (proposal.description or "-").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(safe_description, value_style))
        if proposal.feedback:
            story.append(Paragraph("<b>Feedback van docent:</b>", label_style))
            safe_feedback = proposal.feedback.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe_feedback, value_style))
    else:
        story.append(Paragraph("Geen stagevoorstel ingediend.", value_style))

    # ── Sectie 5: Stageovereenkomst ──
    story.append(Spacer(1, 14))
    story.append(section_heading("5. Stageovereenkomst"))
    agreement = internship.agreement
    if agreement:
        agreement_data = [
            ["Status", agreement.status or "-"],
            ["Verzekering geverifieerd", "Ja" if agreement.insurance_verified else "Nee"],
            ["Geüpload op", agreement.uploaded_at.strftime("%d/%m/%Y %H:%M") if agreement.uploaded_at else "-"],
            ["Gevalideerd op", agreement.validated_at.strftime("%d/%m/%Y %H:%M") if agreement.validated_at else "-"],
        ]
        t = Table(agreement_data, colWidths=[5 * cm, 12 * cm])
        t.setStyle(key_value_style)
        story.append(t)
    else:
        story.append(Paragraph("Geen overeenkomst ingediend.", value_style))

    # ── Sectie 6: Logboeken ──
    story.append(Spacer(1, 14))
    story.append(section_heading("6. Logboeken"))
    logbooks = sorted(internship.logbooks, key=lambda lb: lb.week_number)
    if logbooks:
        # Tabelheaders
        logbook_rows = [[
            Paragraph("Week", cell_bold_style),
            Paragraph("Status", cell_bold_style),
            Paragraph("Gevalideerd", cell_bold_style),
            Paragraph("Taken", cell_bold_style),
            Paragraph("Reflectie", cell_bold_style),
            Paragraph("Problemen", cell_bold_style),
        ]]
        for lb in logbooks:
            status_label = "Ingediend" if lb.status == "submitted" else "Concept"
            validated_label = "Ja" if lb.mentor_validated else "Nee"
            logbook_rows.append([
                Paragraph(str(lb.week_number), cell_style),
                Paragraph(status_label, cell_style),
                Paragraph(validated_label, cell_style),
                Paragraph(lb.tasks or "-", cell_style),
                Paragraph(lb.reflection or "-", cell_style),
                Paragraph(lb.issues or "-", cell_style),
            ])
        # Kolombreedte totaal = 17cm (A4 min marges)
        # Week=1cm, Status=2cm, Gevalideerd=2cm, Taken=4.5cm, Reflectie=4.5cm, Problemen=3cm
        t = Table(logbook_rows, colWidths=[1*cm, 2*cm, 2*cm, 4.5*cm, 4.5*cm, 3*cm])
        t.setStyle(base_table_style)
        story.append(t)
    else:
        story.append(Paragraph("Geen logboekweken gevonden.", value_style))

    # ── Sectie 7: Evaluaties ──
    story.append(Spacer(1, 14))
    story.append(section_heading("7. Evaluaties"))
    story.append(Spacer(1, 6))
    evaluations = internship.evaluations
    if evaluations:
        for evaluation in evaluations:
            # Evaluatieblok per evaluatie
            eval_type_label = "Tussentijds" if evaluation.eval_type == "tussentijds" else "Eindresultaat"
            finalized_label = "Afgerond" if evaluation.finalized else "Concept"
            evaluator_name = f"{evaluation.evaluator.first_name} {evaluation.evaluator.last_name}" if evaluation.evaluator else "-"

            story.append(Paragraph(
                f"<b>{eval_type_label}</b> — {finalized_label} | Beoordelaar: {evaluator_name}",
                value_style,
            ))

            # Gewogen score berekenen indien afgerond
            if evaluation.finalized and evaluation.rules:
                try:
                    score_data = calculate_evaluation_score(db, evaluation)
                    weighted = score_data.get("weighted_score")
                    if weighted is not None:
                        story.append(Paragraph(f"<b>Gewogen eindscore:</b> {weighted:.2f} / 5", value_style))
                except Exception:
                    pass  # Score berekening mislukt — gewoon overslaan

            if evaluation.comments:
                safe_comments = evaluation.comments.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(f"<b>Algemene opmerkingen:</b> {safe_comments}", value_style))

            # Competentiescores als tabel
            if evaluation.rules:
                rule_rows = [[
                    Paragraph("Competentie", cell_bold_style),
                    Paragraph("Gewicht", cell_bold_style),
                    Paragraph("Score", cell_bold_style),
                    Paragraph("Feedback evaluator", cell_bold_style),
                    Paragraph("Student beschrijving", cell_bold_style),
                ]]
                for rule in evaluation.rules:
                    comp = rule.competency
                    comp_name = comp.name if comp else "-"
                    comp_weight = f"{comp.weight}%" if comp else "-"
                    score_labels = {1: "1 - Onvoldoende", 2: "2 - Matig", 3: "3 - Voldoende", 4: "4 - Goed", 5: "5 - Uitstekend"}
                    score_label = score_labels.get(rule.score, "-") if rule.score else "-"
                    rule_rows.append([
                        Paragraph(comp_name, cell_style),
                        Paragraph(comp_weight, cell_style),
                        Paragraph(score_label, cell_style),
                        Paragraph(rule.evaluator_feedback or "-", cell_style),
                        Paragraph(rule.student_description or "-", cell_style),
                    ])
                # Kolombreedte totaal = 17cm
                # Competentie=3cm, Gewicht=1.5cm, Score=2.5cm, Feedback=5cm, Student=5cm
                t = Table(rule_rows, colWidths=[3*cm, 1.5*cm, 2.5*cm, 5*cm, 5*cm])
                t.setStyle(base_table_style)
                story.append(t)

            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("Geen evaluaties gevonden.", value_style))

    # ── PDF bouwen en terugsturen ──
    pdf.build(story)
    buffer.seek(0)

    # Exportactie loggen zodat admins kunnen zien wie wat heeft gedownload
    log_event(
        db,
        "internship.export_pdf",
        user=current_user,
        entity_type="internship",
        entity_id=internship_id,
        detail=f"PDF rapport geëxporteerd voor {student_name}",
    )

    # Bestandsnaam op basis van studentnaam en stage-ID
    safe_name = student_name.replace(" ", "_").lower()
    filename = f"stage_rapport_{safe_name}_{internship_id}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
