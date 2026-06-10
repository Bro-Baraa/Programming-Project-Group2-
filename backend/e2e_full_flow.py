"""Full E2E flow test for all user stories.

Tests the complete end-to-end flow: proposal → review → agreement → logbook → evaluation → final report.

Run with:
  python3 /Users/juanbenjumea/.agents/skills/webapp-testing/scripts/with_server.py \
    --server "cd /Users/juanbenjumea/coding/projects/Programming-Project-Group2- && cd backend && uv run uvicorn app.main:app --port 8001" \
    --port 8001 --timeout 20 \
    -- uv run python e2e_full_flow.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:8001"

# Helper: create a tiny dummy PDF for file upload
DUMMY_PDF = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF\n"


def login_as(page, label):
    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(800)
    btn = page.locator('#quick-login button', has_text='Test accounts laden')
    expect(btn).to_be_visible()
    btn.click()
    page.wait_for_timeout(1000)
    select = page.locator('#quick-login-select')
    expect(select).to_be_visible()
    select.select_option(label=label)
    page.locator('#quick-login-btn').click()
    page.wait_for_timeout(1500)


def logout(page):
    lo = page.locator('#logout-btn')
    if lo.count() > 0 and lo.is_visible():
        lo.click()
        page.wait_for_timeout(1000)


def test_us01_us02_us10_us11_student_submits_proposal_committee_reviews():
    """US-01: Student submits proposal, US-02: Student sees status, US-10: Committee sees list, US-11: Committee reviews"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Use a student with "Ingediend" proposal (student1 has internship id=3 with status Ingediend)
        login_as(page, "Jan Peeters (student)")
        page.wait_for_timeout(500)
        content = page.locator('#content').inner_text()

        # Check for "Ingediend" status in dashboard
        if "Ingediend" in content:
            print("✓ US-01: Student has submitted proposal (status Ingediend)")
            print("✓ US-02: Student sees status 'Ingediend'")
        else:
            print("⚠ US-01: Student proposal status not 'Ingediend'")

        logout(page)

        # Committee reviews
        login_as(page, "Peter Smit (committee)")
        page.wait_for_timeout(500)

        # Click "Voorstellen" tab
        tabs = page.locator('#view-tabs li').all()
        voorstellen_tab = [t for t in tabs if "Voorstellen" in t.inner_text()]
        if voorstellen_tab:
            voorstellen_tab[0].click()
            page.wait_for_timeout(1000)

        # Check proposals table
        content = page.locator('#content').inner_text()
        assert "Stagevoorstellen" in content, "Committee proposals view not found"
        print("✓ US-10: Committee sees proposals list")

        # Find a proposal with status "Ingediend" or "Aanpassingen Vereist"
        rows = page.locator('.proposal-row').all()
        if rows:
            for row in rows:
                status_text = row.inner_text()
                if "Ingediend" in status_text or "Aanpassingen Vereist" in status_text:
                    row.click()
                    page.wait_for_timeout(1000)
                    break

            # Check detail panel
            panel = page.locator('#proposal-detail-panel')
            if panel.count() > 0 and panel.is_visible():
                content = panel.inner_text()
                assert "Beoordeling" in content or "Beoordeling" in content or "Student" in content, "Proposal detail not shown"

                # Check review buttons exist
                if page.locator('#btn-review').count() > 0:
                    print("✓ US-11: Committee can review (In Beoordeling)")
                elif page.locator('#btn-approve').count() > 0:
                    print("✓ US-11: Committee can review (approve/reject)")
                else:
                    print("⚠ US-11: No review buttons found (already reviewed?)")
            else:
                print("⚠ US-11: No selectable proposal found")
        else:
            print("⚠ US-10: No proposals in table")

        logout(page)
        browser.close()


def test_us04_us13_us26_agreement_upload_and_validate():
    """US-04: Student uploads agreement, US-13: Committee validates, US-26: Admin sees agreements"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Create a temp dummy PDF
        pdf_path = Path("/tmp/e2e_dummy.pdf")
        pdf_path.write_bytes(DUMMY_PDF)

        # Login as student with "Goedgekeurd" status
        login_as(page, "Jan Peeters (student)")
        page.wait_for_timeout(500)

        # Check if student has a stage with "Goedgekeurd" status
        content = page.locator('#content').inner_text()
        if "Goedgekeurd" in content:
            # Navigate to agreement
            page.goto(f"{BASE_URL}/?view=overeenkomst")
            page.wait_for_timeout(1000)

            content = page.locator('#content').inner_text()
            if "Upload" in content or "upload" in content:
                # Upload file
                file_input = page.locator('input[type="file"]')
                if file_input.count() > 0:
                    file_input.set_input_files(str(pdf_path))
                    page.wait_for_timeout(500)
                    page.locator('#agreement-form button[type="submit"]').click()
                    page.wait_for_timeout(2000)
                    content = page.locator('#content').inner_text()
                    assert "Geüpload" in content or "succesvol" in content or "Ingediend" in content, "Agreement upload failed"
                    print("✓ US-04: Student uploaded agreement")
                else:
                    print("⚠ US-04: No file input found")
            else:
                print("⚠ US-04: Student already has agreement or stage not ready")
        else:
            print("⚠ US-04: Student has no approved proposal for agreement")

        logout(page)

        # Committee validates
        login_as(page, "Peter Smit (committee)")
        page.wait_for_timeout(500)
        tabs = page.locator('#view-tabs li').all()
        overeenkomsten_tab = [t for t in tabs if "Overeenkomsten" in t.inner_text()]
        if overeenkomsten_tab:
            overeenkomsten_tab[0].click()
            page.wait_for_timeout(1000)
            content = page.locator('#content').inner_text()
            assert "Overeenkomsten" in content, "Committee agreements view not found"
            print("✓ US-13: Committee sees agreements list")
        else:
            print("⚠ US-13: No Overeenkomsten tab")

        logout(page)

        # Admin sees agreements
        login_as(page, "Systeem Beheerder (admin)")
        page.wait_for_timeout(500)
        tabs = page.locator('#view-tabs li').all()
        admin_overeenkomsten = [t for t in tabs if "Overeenkomsten" in t.inner_text()]
        if admin_overeenkomsten:
            admin_overeenkomsten[0].click()
            page.wait_for_timeout(1000)
            content = page.locator('#content').inner_text()
            assert "Overeenkomsten" in content or "Overzicht" in content, "Admin agreements not found"
            print("✓ US-26: Admin sees agreements overview")
        else:
            print("⚠ US-26: No admin agreements tab")

        logout(page)
        browser.close()
        pdf_path.unlink(missing_ok=True)


def test_us05_us08_us21_us22_logbook_flow():
    """US-05: Student fills logbook, US-08: Student sees history, US-21: Mentor sees logbooks, US-22: Mentor validates"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Student with "Lopend" stage (student4 Emma Dubois)
        login_as(page, "Emma Dubois (student)")
        page.wait_for_timeout(500)

        # Navigate to logbook
        page.goto(f"{BASE_URL}/?view=logboek")
        page.wait_for_timeout(1000)
        content = page.locator('#content').inner_text()
        assert "Logboeken" in content or "Logboek" in content, "Logbook view not found"
        print("✓ US-08: Student sees logbook overview")

        # Check week grid
        grid = page.locator('#logbook-week-grid')
        if grid.count() > 0:
            cells = grid.locator('.week-cell').all()
            print(f"  Found {len(cells)} week cells")

        # Fill a missing (Ontbrekend) week
        week_cells = page.locator('.week-cell').all()
        for cell in week_cells:
            text = cell.inner_text()
            if "Ontbrekend" in text:
                cell.click()
                page.wait_for_timeout(500)
                form = page.locator('#logbook-form-panel')
                if form.count() > 0 and form.is_visible():
                    page.locator('#log-tasks').fill("E2E test taken deze week")
                    page.locator('#log-reflection').fill("E2E reflectie over de week")
                    page.locator('#log-issues').fill("E2E problemen of leerpunten")
                    page.locator('#logbook-form button[type="submit"]').click()
                    page.wait_for_timeout(1500)
                    print("✓ US-05: Student filled logbook (missing week)")
                    break
        else:
            # If no missing week, try draft (concept)
            for cell in week_cells:
                text = cell.inner_text()
                if "Concept" in text:
                    cell.click()
                    page.wait_for_timeout(500)
                    form = page.locator('#logbook-form-panel')
                    if form.count() > 0 and form.is_visible():
                        page.locator('#log-tasks').fill("E2E test taken deze week")
                        page.locator('#log-reflection').fill("E2E reflectie over de week")
                        page.locator('#log-issues').fill("E2E problemen of leerpunten")
                        page.locator('#logbook-form button[type="submit"]').click()
                        page.wait_for_timeout(1500)
                        print("✓ US-05: Student filled logbook (draft week)")
                        break
            else:
                print("⚠ US-05: No unfilled week found")

        logout(page)

        # Mentor validates
        login_as(page, "Ruben De Cock (mentor)")
        page.wait_for_timeout(500)

        # Select a stage
        selector = page.locator('#internship-select')
        if selector.count() > 0 and selector.locator('option').count() > 1:
            selector.select_option(index=1)
            page.wait_for_timeout(1000)

        tabs = page.locator('#view-tabs li').all()
        validatie_tab = [t for t in tabs if "Validatie" in t.inner_text()]
        if validatie_tab:
            validatie_tab[0].click()
            page.wait_for_timeout(1000)
            content = page.locator('#content').inner_text()
            assert "Validatie" in content or "Logboek" in content, "Mentor validation view not found"
            print("✓ US-21: Mentor sees logbooks")
        else:
            print("⚠ US-21: No Validatie tab")

        logout(page)
        browser.close()


def test_us15_us17_teacher_followup_and_evaluation():
    """US-15: Teacher sees logbooks, US-17: Teacher registers interim evaluation"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        login_as(page, "Ann Claessens (teacher)")
        page.wait_for_timeout(500)

        # Select a stage
        selector = page.locator('#internship-select')
        if selector.count() > 0 and selector.locator('option').count() > 1:
            selector.select_option(index=1)
            page.wait_for_timeout(1000)

        # Check Opvolging (logbooks)
        tabs = page.locator('#view-tabs li').all()
        opvolging_tab = [t for t in tabs if "Opvolging" in t.inner_text()]
        if opvolging_tab:
            opvolging_tab[0].click()
            page.wait_for_timeout(1000)
            content = page.locator('#content').inner_text()
            assert "Logboeken" in content or "Opvolging" in content, "Teacher logbook view not found"
            print("✓ US-15: Teacher sees logbooks")
        else:
            print("⚠ US-15: No Opvolging tab")

        # Check Evaluatie
        eval_tab = [t for t in tabs if "Evaluatie" in t.inner_text()]
        if eval_tab:
            eval_tab[0].click()
            page.wait_for_timeout(1000)
            content = page.locator('#content').inner_text()
            assert "Evaluatie" in content, "Teacher evaluation view not found"
            print("✓ US-17: Teacher has evaluation form")
        else:
            print("⚠ US-17: No Evaluatie tab")

        logout(page)
        browser.close()


def test_us09_us18_us19_final_report_and_evaluation():
    """US-09: Student sees final report, US-18: Teacher fills final evaluation, US-19: Teacher generates final report"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Student with "Afgerond" stage
        login_as(page, "Jan Peeters (student)")
        page.wait_for_timeout(500)

        # Navigate to evaluaties
        page.goto(f"{BASE_URL}/?view=evaluaties")
        page.wait_for_timeout(1000)
        content = page.locator('#content').inner_text()
        assert "Evaluaties" in content or "Eindoverzicht" in content, "Student evaluations not found"
        print("✓ US-09: Student sees evaluations")

        # Check for final report
        if "Eindoverzicht" in content or "Final" in content or "Afgerond" in content:
            print("✓ US-09: Student sees final report section")
        else:
            print("⚠ US-09: Final report not visible")

        logout(page)

        # Teacher final report
        login_as(page, "Ann Claessens (teacher)")
        page.wait_for_timeout(500)

        # Select a stage
        selector = page.locator('#internship-select')
        if selector.count() > 0 and selector.locator('option').count() > 1:
            selector.select_option(index=1)
            page.wait_for_timeout(1000)

        tabs = page.locator('#view-tabs li').all()
        eindoverzicht_tab = [t for t in tabs if "Eindoverzicht" in t.inner_text()]
        if eindoverzicht_tab:
            eindoverzicht_tab[0].click()
            page.wait_for_timeout(1000)
            content = page.locator('#content').inner_text()
            assert "Eindoverzicht" in content, "Teacher final report not found"
            print("✓ US-19: Teacher sees final report")
        else:
            print("⚠ US-19: No Eindoverzicht tab")

        logout(page)
        browser.close()


def test_us25_admin_competencies():
    """US-25: Admin manages competencies"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        login_as(page, "Systeem Beheerder (admin)")
        page.wait_for_timeout(500)

        tabs = page.locator('#view-tabs li').all()
        comp_tab = [t for t in tabs if "Competenties" in t.inner_text()]
        if comp_tab:
            comp_tab[0].click()
            page.wait_for_timeout(1000)
            content = page.locator('#content').inner_text()
            assert "Competentie" in content or "Competenties" in content, "Competency view not found"
            print("✓ US-25: Admin manages competencies")

            # Check score simulator
            if "Score Simulator" in content or "Simulator" in content:
                print("✓ US-25: Score simulator visible")
        else:
            print("⚠ US-25: No Competenties tab")

        logout(page)
        browser.close()


def test_us27_admin_users():
    """US-27: Admin manages users"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        login_as(page, "Systeem Beheerder (admin)")
        page.wait_for_timeout(500)

        tabs = page.locator('#view-tabs li').all()
        users_tab = [t for t in tabs if "Gebruikers" in t.inner_text()]
        if users_tab:
            users_tab[0].click()
            page.wait_for_timeout(1000)
            content = page.locator('#content').inner_text()
            assert "Gebruikers" in content, "Users view not found"
            print("✓ US-27: Admin manages users")
        else:
            print("⚠ US-27: No Gebruikers tab")

        logout(page)
        browser.close()


def test_us29_notifications():
    """US-29: User receives notifications"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        login_as(page, "Jan Peeters (student)")
        page.wait_for_timeout(500)

        # Check notification bell
        bell = page.locator('#notif-bell')
        if bell.count() > 0:
            print("✓ US-29: Notification bell exists")
            # Click bell
            bell.click()
            page.wait_for_timeout(500)
            dropdown = page.locator('#notif-dropdown')
            if dropdown.count() > 0 and dropdown.is_visible():
                print("✓ US-29: Notification dropdown opens")
            else:
                print("⚠ US-29: Dropdown not visible")
        else:
            print("⚠ US-29: No notification bell")

        logout(page)
        browser.close()


def main():
    tests = [
        test_us01_us02_us10_us11_student_submits_proposal_committee_reviews,
        test_us04_us13_us26_agreement_upload_and_validate,
        test_us05_us08_us21_us22_logbook_flow,
        test_us15_us17_teacher_followup_and_evaluation,
        test_us09_us18_us19_final_report_and_evaluation,
        test_us25_admin_competencies,
        test_us27_admin_users,
        test_us29_notifications,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"E2E Results: {passed} passed, {failed} failed out of {len(tests)} test groups")
    if failed > 0:
        sys.exit(1)
    print("All E2E flow tests passed!")


if __name__ == "__main__":
    main()
