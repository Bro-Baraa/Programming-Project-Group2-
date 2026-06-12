// ============================================
// table-utils.js
// --------------------------------------------
// Kleine, herbruikbare "quality of life" hulpjes voor tabellen:
//   1. een zoekbalk          -> filtert rijen op tekst (zoeken)
//   2. een status-dropdown   -> filtert rijen op 1 kolom    (filteren)
//   3. klikbare kolomkoppen  -> sorteert de rijen           (ordenen)
//
// Belangrijk idee: dit bestand werkt op de rijen die AL in de tabel staan
// (de <tr>'s in de <tbody>). De view-bestanden bouwen die rijen op; deze
// hulpjes tonen/verbergen ze en zetten ze in een andere volgorde.
// Zo hoeft dit bestand niets te weten over hoe elke tabel zijn data ophaalt.
//
// Gebruik (zie js/app.js -> enhanceViewTables):
//   enhanceTable(document.getElementById("proposals-table"), {
//     search: true,                       // zoekbalk tonen
//     searchPlaceholder: "Zoeken...",     // tekst in de zoekbalk
//     filterColumn: 3,                    // kolomnummer voor de dropdown (0 = eerste)
//     filterLabel: "Alle statussen",      // tekst van de "toon alles" optie
//     sort: true,                         // kolomkoppen sorteerbaar maken
//     skipSortColumns: [5],               // kolommen die NIET sorteerbaar zijn (bv. "Acties")
//   });
// ============================================


// --------------------------------------------
// Hoofdfunctie: voeg zoeken/filteren/sorteren toe aan één tabel.
// --------------------------------------------
function enhanceTable(table, options) {
  // Als de tabel niet bestaat (staat niet op de pagina), doen we niets.
  if (!table) return;

  // We voegen de extra knoppen maar één keer toe. Als deze tabel al
  // "verbeterd" is, stoppen we hier zodat we geen dubbele zoekbalk krijgen.
  if (table.dataset.enhanced) return;
  table.dataset.enhanced = "true";

  // Standaardwaarden zodat we niet steeds hoeven te checken of een optie bestaat.
  const opts = options || {};
  const skipSort = opts.skipSortColumns || [];

  // We onthouden de zoekbalk en de dropdown hier, zodat applyFilters() ze
  // later kan uitlezen.
  let searchInput = null;
  let filterSelect = null;


  // --------------------------------------------
  // 1) Maak een klein balkje boven de tabel met de zoekbalk en/of dropdown.
  //    We maken het balkje alleen als we zoeken of filteren nodig hebben.
  // --------------------------------------------
  if (opts.search || opts.filterColumn != null) {
    const toolbar = document.createElement("div");
    toolbar.className = "table-tools";
    // Inline-stijl zodat we geen extra CSS hoeven toe te voegen.
    toolbar.style.display = "flex";
    toolbar.style.gap = "0.5rem";
    toolbar.style.flexWrap = "wrap";
    toolbar.style.marginBottom = "0.75rem";

    // --- zoekbalk ---
    if (opts.search) {
      searchInput = document.createElement("input");
      searchInput.type = "text";
      searchInput.placeholder = opts.searchPlaceholder || "Zoeken...";
      searchInput.style.flex = "1";
      searchInput.style.minWidth = "180px";
      // Elke keer dat de gebruiker typt, passen we de filter toe.
      searchInput.addEventListener("input", applyFilters);
      toolbar.appendChild(searchInput);
    }

    // --- status-dropdown ---
    if (opts.filterColumn != null) {
      filterSelect = document.createElement("select");

      // Eerste optie = alles tonen (lege waarde).
      const allOption = document.createElement("option");
      allOption.value = "";
      allOption.textContent = opts.filterLabel || "Alle";
      filterSelect.appendChild(allOption);

      // We zoeken alle verschillende waarden die in de gekozen kolom staan
      // en maken van elke waarde een keuze in de dropdown.
      // (We lezen de rijen die op dit moment in de tabel staan.)
      const seen = [];
      getDataRows(table).forEach(function (row) {
        const cell = row.children[opts.filterColumn];
        if (!cell) return;
        const value = cell.textContent.trim();
        if (value && seen.indexOf(value) === -1) {
          seen.push(value);
        }
      });
      seen.sort();
      seen.forEach(function (value) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        filterSelect.appendChild(option);
      });

      // Bij het kiezen van een waarde passen we de filter toe.
      filterSelect.addEventListener("change", applyFilters);
      toolbar.appendChild(filterSelect);
    }

    // Zet het balkje vlak vóór de tabel.
    table.parentNode.insertBefore(toolbar, table);
  }


  // --------------------------------------------
  // 2) Maak de kolomkoppen klikbaar om te sorteren.
  // --------------------------------------------
  if (opts.sort) {
    const headers = table.querySelectorAll("thead th");
    headers.forEach(function (th, columnIndex) {
      // Sommige kolommen willen we niet sorteren (bv. de "Acties" knoppen).
      if (skipSort.indexOf(columnIndex) !== -1) return;

      th.style.cursor = "pointer";
      th.style.userSelect = "none";
      th.title = "Klik om te sorteren";
      // Bewaar de originele koptekst, zodat we later het pijltje (▲/▼)
      // kunnen toevoegen of weghalen zonder de tekst kwijt te raken.
      th.dataset.label = th.textContent;
      th.addEventListener("click", function () {
        sortByColumn(table, columnIndex, th);
      });
    });
  }


  // --------------------------------------------
  // Hulpfunctie: geef enkel de "echte" datarijen terug.
  // Een melding-rij zoals "Laden..." of "Geen resultaten" heeft één cel die
  // over alle kolommen loopt (colspan). Die willen we overslaan.
  // --------------------------------------------
  function getDataRows(t) {
    const rows = Array.from(t.querySelectorAll("tbody tr"));
    // Enkel de echte datarijen teruggeven (melding-rijen overslaan).
    return rows.filter(isDataRow);
  }


  // --------------------------------------------
  // Hulpfunctie: toon/verberg rijen op basis van de zoektekst + de dropdown.
  // Wordt opnieuw uitgevoerd telkens de gebruiker typt of een keuze maakt.
  // --------------------------------------------
  function applyFilters() {
    const term = searchInput ? searchInput.value.trim().toLowerCase() : "";
    const filterValue = filterSelect ? filterSelect.value : "";

    Array.from(table.querySelectorAll("tbody tr")).forEach(function (row) {
      // Melding-rijen (zoals "Geen resultaten") laten we altijd staan.
      if (!isDataRow(row)) {
        row.style.display = "";
        return;
      }

      // Komt de zoektekst ergens in de rij voor?
      const matchesSearch =
        term === "" || row.textContent.toLowerCase().indexOf(term) !== -1;

      // Komt de gekozen kolom overeen met de dropdown-waarde?
      let matchesFilter = true;
      if (filterValue !== "" && opts.filterColumn != null) {
        const cell = row.children[opts.filterColumn];
        matchesFilter = cell && cell.textContent.trim() === filterValue;
      }

      // Toon de rij alleen als ze aan beide voorwaarden voldoet.
      row.style.display = matchesSearch && matchesFilter ? "" : "none";
    });
  }
}


// ============================================
// Sorteer de rijen van een tabel op één kolom.
// Klik je nog eens op dezelfde kop, dan draait de richting om
// (oplopend <-> aflopend).
// Deze functie staat buiten enhanceTable() zodat ze maar één keer bestaat.
// ============================================
function sortByColumn(table, columnIndex, headerCell) {
  const tbody = table.querySelector("tbody");
  if (!tbody) return;

  // Enkel de echte datarijen sorteren (melding-rijen overslaan).
  const rows = Array.from(tbody.querySelectorAll("tr")).filter(isDataRow);
  if (rows.length === 0) return;

  // Bepaal de nieuwe richting. We bewaren ze op de kolomkop zelf.
  // Stond ze nog niet op "asc", dan sorteren we nu oplopend.
  const ascending = headerCell.dataset.sortDir !== "asc";

  // Sorteer de rijen op de tekst in de gekozen kolom.
  rows.sort(function (rowA, rowB) {
    const a = cellSortValue(rowA.children[columnIndex].textContent);
    const b = cellSortValue(rowB.children[columnIndex].textContent);
    if (a < b) return ascending ? -1 : 1;
    if (a > b) return ascending ? 1 : -1;
    return 0;
  });

  // Zet de rijen in de nieuwe volgorde terug in de tabel.
  // appendChild verplaatst een bestaande rij (kopieert ze niet), dus
  // klik-handlers op de rijen blijven gewoon werken.
  rows.forEach(function (row) {
    tbody.appendChild(row);
  });

  // Maak eerst alle koppen "schoon" (originele tekst, geen pijltje).
  table.querySelectorAll("thead th").forEach(function (th) {
    if (th.dataset.label) th.textContent = th.dataset.label;
    delete th.dataset.sortDir;
  });

  // Zet daarna het pijltje en de richting op de aangeklikte kop.
  headerCell.dataset.sortDir = ascending ? "asc" : "desc";
  headerCell.textContent =
    (headerCell.dataset.label || headerCell.textContent) +
    (ascending ? " \u25B2" : " \u25BC"); // ▲ of ▼
}


// ============================================
// Zet de tekst van een cel om naar iets dat we kunnen vergelijken bij sorteren.
//   - een getal (bv. "42" of "30%") wordt een getal
//   - een datum dd/mm/jjjj wordt een getal jjjjmmdd (sorteert dan op tijd)
//   - al de rest wordt kleine letters (zodat A en a gelijk sorteren)
// ============================================
function cellSortValue(text) {
  const clean = text.trim();

  // Datum zoals 06/06/2026 -> 20260606
  const dateMatch = clean.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (dateMatch) {
    const day = dateMatch[1];
    const month = dateMatch[2];
    const year = dateMatch[3];
    return Number(year + month + day);
  }

  // Een getal: de tekst begint met een cijfer en bevat geen letters.
  // (Zo wordt "30%" wel een getal, maar "3 weken" niet.)
  if (/^-?\d/.test(clean) && !/[a-zA-Z]/.test(clean)) {
    const numberMatch = clean.match(/-?\d+(\.\d+)?/);
    if (numberMatch) return Number(numberMatch[0]);
  }

  // Alle andere gevallen: vergelijk als gewone (kleine-letter) tekst.
  return clean.toLowerCase();
}


// ============================================
// Is dit een "echte" datarij (en geen melding-rij zoals "Laden..."/"Geen resultaten")?
// Melding-rijen gebruiken één cel met colspan (bv. <td colspan="5">). Die slaan we over.
// We tellen dus NIET op kolomaantal: sommige tabellen hebben meer cellen dan
// kolomkoppen (bv. de overzicht-tabel die ook een Docent-kolom toont).
// ============================================
function isDataRow(row) {
  if (row.children.length === 0) return false;     // lege rij
  if (row.querySelector("td[colspan]")) return false; // melding-rij
  return true;
}
