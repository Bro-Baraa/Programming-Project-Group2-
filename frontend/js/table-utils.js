function enhanceTable(table, options) {
  if (!table) return;
  if (table.dataset.enhanced) return;
  table.dataset.enhanced = "true";

  const opts = options || {};
  const skipSort = opts.skipSortColumns || [];
  let searchInput = null;
  let filterSelect = null;

  if (opts.search || opts.filterColumn != null) {
    const toolbar = document.createElement("div");
    toolbar.className = "table-tools";
    toolbar.style.display = "flex";
    toolbar.style.gap = "0.5rem";
    toolbar.style.flexWrap = "wrap";
    toolbar.style.marginBottom = "0.75rem";

    if (opts.search) {
      searchInput = document.createElement("input");
      searchInput.type = "text";
      searchInput.placeholder = opts.searchPlaceholder || "Zoeken...";
      searchInput.style.flex = "1";
      searchInput.style.minWidth = "180px";
      searchInput.addEventListener("input", applyFilters);
      toolbar.appendChild(searchInput);
    }

    if (opts.filterColumn != null) {
      filterSelect = document.createElement("select");
      const allOption = document.createElement("option");
      allOption.value = "";
      allOption.textContent = opts.filterLabel || "Alle";
      filterSelect.appendChild(allOption);

      const seen = [];
      getDataRows(table).forEach(function (row) {
        const cell = row.children[opts.filterColumn];
        if (!cell) return;
        const value = cell.textContent.trim();
        if (value && seen.indexOf(value) === -1) seen.push(value);
      });
      seen.sort();
      seen.forEach(function (value) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        filterSelect.appendChild(option);
      });

      filterSelect.addEventListener("change", applyFilters);
      toolbar.appendChild(filterSelect);
    }

    table.parentNode.insertBefore(toolbar, table);
  }

  if (opts.sort) {
    table.querySelectorAll("thead th").forEach(function (th, columnIndex) {
      if (skipSort.indexOf(columnIndex) !== -1) return;
      th.style.cursor = "pointer";
      th.style.userSelect = "none";
      th.title = "Klik om te sorteren";
      th.dataset.label = th.textContent;
      th.addEventListener("click", function () {
        sortByColumn(table, columnIndex, th);
      });
    });
  }

  function getDataRows(t) {
    return Array.from(t.querySelectorAll("tbody tr")).filter(isDataRow);
  }

  function applyFilters() {
    const term = searchInput ? searchInput.value.trim().toLowerCase() : "";
    const filterValue = filterSelect ? filterSelect.value : "";

    Array.from(table.querySelectorAll("tbody tr")).forEach(function (row) {
      if (!isDataRow(row)) {
        row.style.display = "";
        return;
      }
      const matchesSearch = term === "" || row.textContent.toLowerCase().indexOf(term) !== -1;
      let matchesFilter = true;
      if (filterValue !== "" && opts.filterColumn != null) {
        const cell = row.children[opts.filterColumn];
        matchesFilter = cell && cell.textContent.trim() === filterValue;
      }
      row.style.display = matchesSearch && matchesFilter ? "" : "none";
    });
  }
}

function sortByColumn(table, columnIndex, headerCell) {
  const tbody = table.querySelector("tbody");
  if (!tbody) return;

  const rows = Array.from(tbody.querySelectorAll("tr")).filter(isDataRow);
  if (rows.length === 0) return;

  const ascending = headerCell.dataset.sortDir !== "asc";

  rows.sort(function (rowA, rowB) {
    const a = cellSortValue(rowA.children[columnIndex].textContent);
    const b = cellSortValue(rowB.children[columnIndex].textContent);
    if (a < b) return ascending ? -1 : 1;
    if (a > b) return ascending ? 1 : -1;
    return 0;
  });

  rows.forEach(function (row) {
    tbody.appendChild(row);
  });

  table.querySelectorAll("thead th").forEach(function (th) {
    if (th.dataset.label) th.textContent = th.dataset.label;
    delete th.dataset.sortDir;
  });

  headerCell.dataset.sortDir = ascending ? "asc" : "desc";
  headerCell.textContent =
    (headerCell.dataset.label || headerCell.textContent) +
    (ascending ? " \u25B2" : " \u25BC"); // ▲ of ▼
}

function cellSortValue(text) {
  const clean = text.trim();

  const dateMatch = clean.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (dateMatch) {
    return Number(dateMatch[3] + dateMatch[2] + dateMatch[1]);
  }

  if (/^-?\d/.test(clean) && !/[a-zA-Z]/.test(clean)) {
    const numberMatch = clean.match(/-?\d+(\.\d+)?/);
    if (numberMatch) return Number(numberMatch[0]);
  }

  return clean.toLowerCase();
}

function isDataRow(row) {
  if (row.children.length === 0) return false;
  if (row.querySelector("td[colspan]")) return false;
  return true;
}
