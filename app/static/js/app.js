/**
 * BreakfastWise - Epic 1: Hotel Data Management
 * Frontend Application Controller
 */

// State Management
const state = {
  records: [],
  summary: null,
  activeFilter: 'all', // 'all', '7d', '14d', '30d', 'custom'
  startDate: '',
  endDate: '',
  searchQuery: '',
};

// DOM Elements
const elements = {
  // KPI Cards
  kpiDays: document.getElementById('kpi-days'),
  kpiOcc: document.getElementById('kpi-occ'),
  kpiCons: document.getElementById('kpi-cons'),
  kpiRate: document.getElementById('kpi-rate'),

  // Forms
  occupancyForm: document.getElementById('occupancy-form'),
  consumptionForm: document.getElementById('consumption-form'),
  occDate: document.getElementById('occ-date'),
  occCount: document.getElementById('occ-count'),
  occRooms: document.getElementById('occ-rooms'),
  occNotes: document.getElementById('occ-notes'),
  occBanner: document.getElementById('occ-banner'),

  consDate: document.getElementById('cons-date'),
  consCount: document.getElementById('cons-count'),
  consActualOcc: document.getElementById('cons-actual-occ'),
  consNotes: document.getElementById('cons-notes'),
  consBanner: document.getElementById('cons-banner'),

  // Table & Empty State
  tableContainer: document.getElementById('table-container'),
  tableBody: document.getElementById('table-body'),
  emptyState: document.getElementById('empty-state'),
  searchInput: document.getElementById('search-input'),
  recordsCountText: document.getElementById('records-count-text'),

  // Filter Buttons
  filterAll: document.getElementById('filter-all'),
  filter7d: document.getElementById('filter-7d'),
  filter14d: document.getElementById('filter-14d'),
  filter30d: document.getElementById('filter-30d'),
  filterCustomApply: document.getElementById('filter-custom-apply'),
  filterCustomReset: document.getElementById('filter-custom-reset'),
  filterStartDate: document.getElementById('filter-start-date'),
  filterEndDate: document.getElementById('filter-end-date'),

  // Action Buttons
  btnSeed: document.getElementById('btn-seed'),
  btnClear: document.getElementById('btn-clear'),
  btnRefresh: document.getElementById('btn-refresh'),
  btnEmptySeed: document.getElementById('btn-empty-seed'),

  // Modals
  editModal: document.getElementById('edit-modal'),
  editModalClose: document.getElementById('edit-modal-close'),
  editModalCancel: document.getElementById('edit-modal-cancel'),
  editForm: document.getElementById('edit-form'),
  editDate: document.getElementById('edit-date'),
  modalDateLabel: document.getElementById('modal-date-label'),
  editOcc: document.getElementById('edit-occ'),
  editRooms: document.getElementById('edit-rooms'),
  editOccNotes: document.getElementById('edit-occ-notes'),
  editCons: document.getElementById('edit-cons'),
  editActualOcc: document.getElementById('edit-actual-occ'),
  editConsNotes: document.getElementById('edit-cons-notes'),

  // Toast Container
  toastContainer: document.getElementById('toast-container'),
};

// Utilities
function showToast(title, message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  
  toast.innerHTML = `
    <div class="toast-icon">${icon}</div>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
    <button class="toast-close">&times;</button>
  `;

  elements.toastContainer.appendChild(toast);

  toast.querySelector('.toast-close').addEventListener('click', () => {
    toast.remove();
  });

  setTimeout(() => {
    if (toast.parentElement) {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 200);
    }
  }, 4500);
}

function showBanner(bannerEl, message, isError = false) {
  bannerEl.textContent = message;
  bannerEl.className = `form-banner ${isError ? 'error' : 'success'}`;
  bannerEl.style.display = 'block';
  setTimeout(() => {
    bannerEl.style.display = 'none';
  }, 5000);
}

function formatDateDisplay(isoDate) {
  try {
    const [y, m, d] = isoDate.split('-').map(Number);
    const dateObj = new Date(y, m - 1, d);
    return {
      main: dateObj.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }),
      iso: isoDate
    };
  } catch (e) {
    return { main: isoDate, iso: isoDate };
  }
}

function validateWholeNonNegative(valStr, fieldName, isRequired = false) {
  if (valStr === '' || valStr === null || valStr === undefined) {
    if (isRequired) {
      throw new Error(`${fieldName} is required.`);
    }
    return null;
  }
  valStr = valStr.toString().trim();
  if (valStr === '') {
    if (isRequired) {
      throw new Error(`${fieldName} is required.`);
    }
    return null;
  }
  if (valStr.includes('.') || valStr.includes(',')) {
    throw new Error(`${fieldName} must be a whole integer (decimals are not allowed).`);
  }
  if (!/^\d+$/.test(valStr)) {
    throw new Error(`${fieldName} must be a non-negative whole number (digits 0-9 only).`);
  }
  const parsed = Number(valStr);
  if (parsed < 0 || !Number.isSafeInteger(parsed)) {
    throw new Error(`${fieldName} must be a valid non-negative integer.`);
  }
  return parsed;
}

function setDefaultDates() {
  const today = new Date();
  const tomorrow = new Date();
  tomorrow.setDate(today.getDate() + 1);

  const formatIso = (d) => d.toISOString().split('T')[0];
  const todayStr = formatIso(today);

  if (!elements.occDate.value) {
    elements.occDate.value = formatIso(tomorrow);
  }
  if (!elements.consDate.value) {
    elements.consDate.value = todayStr;
  }
  // Restrict consumption date picker to today or earlier
  elements.consDate.max = todayStr;
}

// API Communication
async function fetchHistoricalData() {
  let url = '/api/history?';
  const params = new URLSearchParams();

  if (state.startDate) params.append('start_date', state.startDate);
  if (state.endDate) params.append('end_date', state.endDate);

  url += params.toString();

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch historical data');
    const data = await res.json();
    state.records = data.records || [];
    state.summary = data.summary || null;
    renderUI();
  } catch (err) {
    showToast('Network Error', err.message, 'error');
  }
}

// Rendering
function renderUI() {
  renderKPIs();
  renderTable();
}

function renderKPIs() {
  if (!state.summary || state.summary.total_records === 0) {
    elements.kpiDays.textContent = '0';
    elements.kpiOcc.textContent = '—';
    elements.kpiCons.textContent = '—';
    elements.kpiRate.textContent = '—';
    return;
  }

  const s = state.summary;
  elements.kpiDays.textContent = s.total_records.toString();
  elements.kpiOcc.textContent = s.avg_expected_occupancy !== null ? `${s.avg_expected_occupancy} guests` : '—';
  elements.kpiCons.textContent = s.avg_actual_consumption !== null ? `${s.avg_actual_consumption} meals` : '—';
  elements.kpiRate.textContent = s.avg_take_up_rate !== null ? `${s.avg_take_up_rate}%` : '—';
}

function renderTable() {
  let filtered = [...state.records];

  // Apply text search
  if (state.searchQuery.trim()) {
    const q = state.searchQuery.toLowerCase().trim();
    filtered = filtered.filter(r => 
      r.date.toLowerCase().includes(q) ||
      (r.occupancy_notes && r.occupancy_notes.toLowerCase().includes(q)) ||
      (r.consumption_notes && r.consumption_notes.toLowerCase().includes(q))
    );
  }

  elements.recordsCountText.textContent = `${filtered.length} record${filtered.length === 1 ? '' : 's'}`;

  // Handle Empty State
  if (filtered.length === 0) {
    elements.tableContainer.style.display = 'none';
    elements.emptyState.style.display = 'flex';
    return;
  }

  elements.tableContainer.style.display = 'block';
  elements.emptyState.style.display = 'none';

  elements.tableBody.innerHTML = filtered.map(row => {
    const dateFormatted = formatDateDisplay(row.date);
    
    // Status Badge
    let statusClass = 'occupancy-only';
    if (row.status === 'Complete') statusClass = 'complete';
    else if (row.status === 'Consumption Only') statusClass = 'consumption-only';

    // Take-up Badge
    let takeupBadge = '<span style="color: var(--neutral-400);">—</span>';
    if (row.take_up_rate !== null && row.take_up_rate !== undefined) {
      let badgeClass = 'takeup-mid';
      if (row.take_up_rate >= 80) badgeClass = 'takeup-high';
      else if (row.take_up_rate < 70) badgeClass = 'takeup-low';
      takeupBadge = `<span class="takeup-badge ${badgeClass}">${row.take_up_rate}%</span>`;
    }

    // Variance
    let varianceDisplay = '<span style="color: var(--neutral-400);">—</span>';
    if (row.variance !== null && row.variance !== undefined) {
      const sign = row.variance > 0 ? '+' : '';
      varianceDisplay = `<strong>${sign}${row.variance}</strong>`;
    }

    const notes = [row.occupancy_notes, row.consumption_notes].filter(Boolean).join(' | ') || '—';

    return `
      <tr data-date="${row.date}">
        <td>
          <div class="date-cell">
            <span>${dateFormatted.main}</span>
            <span class="date-sub">${dateFormatted.iso}</span>
          </div>
        </td>
        <td>
          ${row.expected_occupancy !== null ? `<strong>${row.expected_occupancy}</strong> guests` : '<span style="color: var(--neutral-400);">Not entered</span>'}
          ${row.total_rooms ? `<div style="font-size: 0.72rem; color: var(--neutral-400);">${row.total_rooms} rooms</div>` : ''}
        </td>
        <td>
          ${row.actual_consumption !== null ? `<strong>${row.actual_consumption}</strong> meals` : '<span style="color: var(--neutral-400);">Not recorded</span>'}
        </td>
        <td>${takeupBadge}</td>
        <td>${varianceDisplay}</td>
        <td>
          <span class="status-badge ${statusClass}">
            <span class="dot" style="width:6px;height:6px;border-radius:50%;background:currentColor;"></span>
            ${row.status}
          </span>
        </td>
        <td style="max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${notes}">
          ${notes}
        </td>
        <td>
          <div class="action-btn-group">
            <button class="action-icon-btn edit-btn" title="Edit date entries" onclick="openEditModal('${row.date}')">✎</button>
            <button class="action-icon-btn delete delete-btn" title="Delete entries for ${row.date}" onclick="deleteDateEntry('${row.date}')">🗑</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

// Story 1: Submit Expected Occupancy
elements.occupancyForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const targetDate = elements.occDate.value;
  if (!targetDate) {
    showToast('Validation Error', 'Please select a valid date.', 'error');
    return;
  }

  let count, rooms;
  try {
    count = validateWholeNonNegative(elements.occCount.value, 'Expected guests', true);
    rooms = validateWholeNonNegative(elements.occRooms.value, 'Total rooms', false);
    elements.occCount.classList.remove('is-invalid');
    elements.occRooms.classList.remove('is-invalid');
  } catch (err) {
    showToast('Validation Error', err.message, 'error');
    if (err.message.includes('Expected guests')) elements.occCount.classList.add('is-invalid');
    if (err.message.includes('Total rooms')) elements.occRooms.classList.add('is-invalid');
    return;
  }

  const notes = elements.occNotes.value.trim();

  try {
    const res = await fetch('/api/occupancy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date: targetDate,
        expected_occupancy: count,
        total_rooms: rooms,
        notes: notes
      })
    });

    const data = await res.json();
    if (!res.ok) {
      const errorMsg = data.detail || 'Failed to save expected occupancy.';
      showBanner(elements.occBanner, errorMsg, true);
      showToast('Error', errorMsg, 'error');
      return;
    }

    showBanner(elements.occBanner, `✓ Expected occupancy of ${count} guests recorded for ${targetDate}.`, false);
    showToast('Occupancy Saved', `Expected occupancy recorded for ${targetDate}.`, 'success');
    
    // Clear count and notes
    elements.occCount.value = '';
    elements.occRooms.value = '';
    elements.occNotes.value = '';

    await fetchHistoricalData();
  } catch (err) {
    showBanner(elements.occBanner, err.message, true);
    showToast('Network Error', err.message, 'error');
  }
});

// Story 2: Submit Breakfast Consumption
elements.consumptionForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const targetDate = elements.consDate.value;
  if (!targetDate) {
    showToast('Validation Error', 'Please select a valid service date.', 'error');
    return;
  }

  // Prevent recording consumption for future dates
  const todayIso = new Date().toISOString().split('T')[0];
  if (targetDate > todayIso) {
    showToast('Validation Error', `Actual breakfast consumption cannot be recorded for a future date (maximum allowed: ${todayIso}).`, 'error');
    elements.consDate.classList.add('is-invalid');
    return;
  }
  elements.consDate.classList.remove('is-invalid');

  let count, actualOcc;
  try {
    count = validateWholeNonNegative(elements.consCount.value, 'Actual breakfast meals', true);
    actualOcc = validateWholeNonNegative(elements.consActualOcc.value, 'Actual in-house guests', false);
    elements.consCount.classList.remove('is-invalid');
    if (elements.consActualOcc) elements.consActualOcc.classList.remove('is-invalid');
  } catch (err) {
    showToast('Validation Error', err.message, 'error');
    if (err.message.includes('breakfast meals')) elements.consCount.classList.add('is-invalid');
    if (err.message.includes('in-house guests')) elements.consActualOcc.classList.add('is-invalid');
    return;
  }

  const notes = elements.consNotes.value.trim();

  try {
    const res = await fetch('/api/consumption', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date: targetDate,
        actual_consumption: count,
        actual_occupancy: actualOcc,
        notes: notes
      })
    });

    const data = await res.json();
    if (!res.ok) {
      const errorMsg = data.detail || 'Failed to record breakfast consumption.';
      showBanner(elements.consBanner, errorMsg, true);
      showToast('Error', errorMsg, 'error');
      return;
    }

    showBanner(elements.consBanner, `✓ Recorded ${count} breakfast meals served on ${targetDate}.`, false);
    showToast('Consumption Recorded', `Breakfast consumption recorded for ${targetDate}.`, 'success');

    elements.consCount.value = '';
    elements.consActualOcc.value = '';
    elements.consNotes.value = '';

    await fetchHistoricalData();
  } catch (err) {
    showBanner(elements.consBanner, err.message, true);
    showToast('Network Error', err.message, 'error');
  }
});
    showBanner(elements.consBanner, err.message, true);
    showToast('Network Error', err.message, 'error');
  }
});

// Story 3: Date Filtering & Presets
function setFilterPreset(preset) {
  state.activeFilter = preset;
  [elements.filterAll, elements.filter7d, elements.filter14d, elements.filter30d].forEach(btn => {
    btn.classList.remove('active');
  });

  const today = new Date();
  const formatIso = (d) => d.toISOString().split('T')[0];

  if (preset === 'all') {
    elements.filterAll.classList.add('active');
    state.startDate = '';
    state.endDate = '';
    elements.filterStartDate.value = '';
    elements.filterEndDate.value = '';
  } else if (preset === '7d') {
    elements.filter7d.classList.add('active');
    const past = new Date();
    past.setDate(today.getDate() - 7);
    state.startDate = formatIso(past);
    state.endDate = formatIso(today);
    elements.filterStartDate.value = state.startDate;
    elements.filterEndDate.value = state.endDate;
  } else if (preset === '14d') {
    elements.filter14d.classList.add('active');
    const past = new Date();
    past.setDate(today.getDate() - 14);
    state.startDate = formatIso(past);
    state.endDate = formatIso(today);
    elements.filterStartDate.value = state.startDate;
    elements.filterEndDate.value = state.endDate;
  } else if (preset === '30d') {
    elements.filter30d.classList.add('active');
    const past = new Date();
    past.setDate(today.getDate() - 30);
    state.startDate = formatIso(past);
    state.endDate = formatIso(today);
    elements.filterStartDate.value = state.startDate;
    elements.filterEndDate.value = state.endDate;
  }

  fetchHistoricalData();
}

elements.filterAll.addEventListener('click', () => setFilterPreset('all'));
elements.filter7d.addEventListener('click', () => setFilterPreset('7d'));
elements.filter14d.addEventListener('click', () => setFilterPreset('14d'));
elements.filter30d.addEventListener('click', () => setFilterPreset('30d'));

elements.filterCustomApply.addEventListener('click', () => {
  const start = elements.filterStartDate.value;
  const end = elements.filterEndDate.value;
  if (start && end && start > end) {
    showToast('Date Range Error', 'Start date cannot be after end date.', 'error');
    return;
  }
  [elements.filterAll, elements.filter7d, elements.filter14d, elements.filter30d].forEach(btn => {
    btn.classList.remove('active');
  });
  state.startDate = start;
  state.endDate = end;
  fetchHistoricalData();
});

elements.filterCustomReset.addEventListener('click', () => {
  setFilterPreset('all');
});

elements.searchInput.addEventListener('input', (e) => {
  state.searchQuery = e.target.value;
  renderTable();
});

// Seed Sample Data
async function handleSeedData() {
  try {
    const res = await fetch('/api/history/seed?days=14', { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      showToast('Sample Data Loaded', data.message, 'success');
      await fetchHistoricalData();
    } else {
      showToast('Error', data.detail || 'Could not load sample data', 'error');
    }
  } catch (err) {
    showToast('Network Error', err.message, 'error');
  }
}

// Clear All Data (Protected with explicit typing confirmation)
async function handleClearData() {
  const promptVal = prompt(
    '⚠️ DANGER: This will permanently delete ALL historical occupancy and consumption records!\n\nTo confirm this action, please type "CLEAR" below:'
  );
  if (promptVal !== 'CLEAR') {
    showToast('Cancelled', 'Database clear action was cancelled.', 'info');
    return;
  }
  try {
    const res = await fetch('/api/history/clear', { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      showToast('Data Cleared', data.message, 'info');
      await fetchHistoricalData();
    } else {
      showToast('Error', data.detail || 'Could not clear data', 'error');
    }
  } catch (err) {
    showToast('Network Error', err.message, 'error');
  }
}

elements.btnSeed.addEventListener('click', handleSeedData);
elements.btnEmptySeed.addEventListener('click', handleSeedData);
elements.btnClear.addEventListener('click', handleClearData);
elements.btnRefresh.addEventListener('click', () => {
  fetchHistoricalData();
  showToast('Refreshed', 'Historical records updated.', 'info');
});

// Inline Edit & Delete
window.deleteDateEntry = async function(targetDate) {
  if (!confirm(`Are you sure you want to delete all records for date ${targetDate}?`)) {
    return;
  }
  try {
    const res = await fetch(`/api/history/${targetDate}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      showToast('Entry Removed', `Records for ${targetDate} deleted.`, 'success');
      await fetchHistoricalData();
    } else {
      showToast('Error', data.detail || 'Failed to delete record', 'error');
    }
  } catch (err) {
    showToast('Network Error', err.message, 'error');
  }
};

window.openEditModal = function(targetDate) {
  const row = state.records.find(r => r.date === targetDate);
  if (!row) return;

  elements.editDate.value = row.date;
  if (elements.modalDateLabel) {
    elements.modalDateLabel.textContent = row.date;
  }

  // Populate Story 1 fields
  elements.editOcc.value = row.expected_occupancy !== null ? row.expected_occupancy : '';
  elements.editRooms.value = row.total_rooms !== null ? row.total_rooms : '';
  elements.editOccNotes.value = row.occupancy_notes || '';

  // Populate Story 2 fields
  elements.editCons.value = row.actual_consumption !== null ? row.actual_consumption : '';
  elements.editActualOcc.value = row.actual_occupancy !== null ? row.actual_occupancy : '';
  elements.editConsNotes.value = row.consumption_notes || '';

  elements.editModal.classList.add('active');
};

function closeEditModal() {
  elements.editModal.classList.remove('active');
}

elements.editModalClose.addEventListener('click', closeEditModal);
elements.editModalCancel.addEventListener('click', closeEditModal);

elements.editForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const dateVal = elements.editDate.value;
  const originalRow = state.records.find(r => r.date === dateVal);

  let occVal, roomsVal, consVal, actualOccVal;
  try {
    occVal = validateWholeNonNegative(elements.editOcc.value, 'Expected guests', false);
    roomsVal = validateWholeNonNegative(elements.editRooms.value, 'Total rooms', false);
    consVal = validateWholeNonNegative(elements.editCons.value, 'Actual breakfast meals', false);
    actualOccVal = validateWholeNonNegative(elements.editActualOcc.value, 'Actual in-house guests', false);
  } catch (err) {
    showToast('Validation Error', err.message, 'error');
    return;
  }

  const occNotesVal = elements.editOccNotes.value.trim();
  const consNotesVal = elements.editConsNotes.value.trim();

  try {
    // 1. Update occupancy if entered or if it previously existed
    if (occVal !== null || (originalRow && originalRow.expected_occupancy !== null && elements.editOcc.value.trim() !== '')) {
      await fetch('/api/occupancy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: dateVal,
          expected_occupancy: occVal !== null ? occVal : 0,
          total_rooms: roomsVal,
          notes: occNotesVal
        })
      });
    }

    // 2. Update consumption if entered or if it previously existed
    if (consVal !== null || (originalRow && originalRow.actual_consumption !== null && elements.editCons.value.trim() !== '')) {
      const todayIso = new Date().toISOString().split('T')[0];
      if (dateVal > todayIso) {
        showToast('Validation Error', `Cannot record actual consumption for a future date (maximum allowed: ${todayIso}).`, 'error');
        return;
      }

      await fetch('/api/consumption', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: dateVal,
          actual_consumption: consVal !== null ? consVal : 0,
          actual_occupancy: actualOccVal,
          notes: consNotesVal
        })
      });
    }

    closeEditModal();
    showToast('Updated', `Entry for ${dateVal} updated successfully.`, 'success');
    await fetchHistoricalData();
  } catch (err) {
    showToast('Network Error', err.message, 'error');
  }
});

// App Initialization
document.addEventListener('DOMContentLoaded', () => {
  setDefaultDates();
  fetchHistoricalData();
});
