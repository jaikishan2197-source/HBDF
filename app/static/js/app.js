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
  occGuestsIncluded: document.getElementById('occ-guests-included'),
  occGuestsOther: document.getElementById('occ-guests-other'),
  occEventCovers: document.getElementById('occ-event-covers'),
  occTotalResidentDisplay: document.getElementById('occ-total-resident-display'),
  occCount: document.getElementById('occ-count'), // fallback
  occRooms: document.getElementById('occ-rooms'),
  occNotes: document.getElementById('occ-notes'),
  occBanner: document.getElementById('occ-banner'),

  consDate: document.getElementById('cons-date'),
  consCount: document.getElementById('cons-count'),
  consActualOcc: document.getElementById('cons-actual-occ'),
  consNotes: document.getElementById('cons-notes'),
  consBanner: document.getElementById('cons-banner'),

  // Forecasting
  forecastForm: document.getElementById('forecast-form'),
  forecastDate: document.getElementById('forecast-date'),
  forecastWeekdayHint: document.getElementById('forecast-weekday-hint'),
  forecastGuestsIncluded: document.getElementById('forecast-guests-included'),
  forecastGuestsOther: document.getElementById('forecast-guests-other'),
  forecastTotalGuestsLabel: document.getElementById('forecast-total-guests-label'),
  forecastEventCovers: document.getElementById('forecast-event-covers'),
  forecastBufferSlider: document.getElementById('forecast-buffer-slider'),
  bufferValDisplay: document.getElementById('buffer-val-display'),
  forecastHoliday: document.getElementById('forecast-holiday'),
  forecastEvent: document.getElementById('forecast-event'),
  forecastEmpty: document.getElementById('forecast-empty'),
  forecastResults: document.getElementById('forecast-results'),
  forecastFormMessage: document.getElementById('forecast-form-message'),
  forecastSubmit: document.getElementById('btn-run-forecast'),
  forecastGuestValue: document.getElementById('forecast-guests-value'),
  forecastResultDate: document.getElementById('forecast-result-date'),
  forecastResidentBreakdown: document.getElementById('forecast-resident-breakdown'),
  forecastSelectedModel: document.getElementById('forecast-selected-model'),
  forecastMatchingDaysBadge: document.getElementById('forecast-matching-days-badge'),
  forecastWarningContainer: document.getElementById('forecast-warning-container'),
  calcDatesSummary: document.getElementById('calc-dates-summary'),
  calcFormulaInc: document.getElementById('calc-formula-inc'),
  calcValInc: document.getElementById('calc-val-inc'),
  calcFormulaOth: document.getElementById('calc-formula-oth'),
  calcValOth: document.getElementById('calc-val-oth'),
  calcValResident: document.getElementById('calc-val-resident'),
  calcValEvent: document.getElementById('calc-val-event'),
  calcValFinal: document.getElementById('calc-val-final'),
  btnToggleDetails: document.getElementById('btn-toggle-details'),
  calcHistoryDetails: document.getElementById('calc-history-details'),
  calcHistoryTbody: document.getElementById('calc-history-tbody'),
  calcExcludedDetails: document.getElementById('calc-excluded-details'),
  calcExcludedTbody: document.getElementById('calc-excluded-tbody'),
  forecastBufferAppliedLabel: document.getElementById('forecast-buffer-applied-label'),
  forecastModelsBody: document.getElementById('forecast-models-body'),
  forecastPortionsBody: document.getElementById('forecast-portions-body'),
  forecastResultSource: document.getElementById('forecast-result-source'),

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
  const formatLocalIso = (d) => {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };
  const todayStr = formatIso(today);
  const tomorrowStr = formatLocalIso(tomorrow);

  if (elements.occDate && !elements.occDate.value) {
    elements.occDate.value = tomorrowStr;
  }
  if (elements.forecastDate) {
    elements.forecastDate.min = tomorrowStr;
    if (!elements.forecastDate.value) elements.forecastDate.value = tomorrowStr;
  }
  if (elements.consDate && !elements.consDate.value) {
    elements.consDate.value = todayStr;
  }
  if (elements.consDate) {
    // Restrict consumption date picker to today or earlier
    elements.consDate.max = todayStr;
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[character]);
}

function renderForecast(data) {
  const dateDisplay = formatDateDisplay(data.forecast_date);
  if (elements.forecastGuestValue) elements.forecastGuestValue.textContent = data.forecasted_breakfast_guests.toLocaleString();
  if (elements.forecastResultDate) elements.forecastResultDate.textContent = `${dateDisplay.main} (${dateDisplay.iso})`;
  if (elements.forecastSelectedModel) elements.forecastSelectedModel.textContent = data.selected_model;

  // Warning banner handling
  if (data.warning && elements.forecastWarningContainer) {
    elements.forecastWarningContainer.textContent = `⚠️ Warning: ${data.warning}`;
    elements.forecastWarningContainer.style.display = 'flex';
  } else if (elements.forecastWarningContainer) {
    elements.forecastWarningContainer.style.display = 'none';
  }

  // Resident vs Uplift breakdown
  if (data.calculation_breakdown) {
    const b = data.calculation_breakdown;
    if (elements.forecastResidentBreakdown) {
      elements.forecastResidentBreakdown.textContent = `Resident Covers: ${b.resident_covers} + Event Uplift: ${data.event_expected_covers} covers`;
    }
    if (elements.forecastMatchingDaysBadge) {
      elements.forecastMatchingDaysBadge.textContent = `${b.matching_weekdays_count} matching ${b.matching_weekday_name}(s) used`;
    }

    // Transparent calculation steps
    if (elements.calcDatesSummary) {
      elements.calcDatesSummary.textContent = `${b.matching_weekdays_count} matching ${b.matching_weekday_name}(s) before ${data.forecast_date}: ${b.historical_dates_used.join(', ')}`;
    }
    if (elements.calcFormulaInc) elements.calcFormulaInc.textContent = `${b.sum_covers_included} ÷ ${b.sum_guests_included} covers/guest`;
    if (elements.calcValInc) {
      elements.calcValInc.textContent = `${b.capture_rate_included_percent}%${b.capture_rate_included_percent > 100 ? ' ⚠️' : ''}`;
      elements.calcValInc.style.color = b.capture_rate_included_percent > 100 ? '#b45309' : '';
    }
    if (elements.calcFormulaOth) elements.calcFormulaOth.textContent = `${b.sum_covers_other} ÷ ${b.sum_guests_other} covers/guest`;
    if (elements.calcValOth) {
      elements.calcValOth.textContent = `${b.capture_rate_other_percent}%${b.capture_rate_other_percent > 100 ? ' ⚠️' : ''}`;
      elements.calcValOth.style.color = b.capture_rate_other_percent > 100 ? '#b45309' : '';
    }
    if (elements.calcValResident) elements.calcValResident.textContent = `${b.resident_covers} covers`;
    if (elements.calcValEvent) elements.calcValEvent.textContent = `+${b.event_expected_covers} covers`;
    if (elements.calcValFinal) elements.calcValFinal.textContent = `${b.final_forecast_covers} covers`;

    // History detail table of eligible matching weekdays used
    if (elements.calcHistoryTbody && b.historical_days_detail && b.historical_days_detail.length > 0) {
      elements.calcHistoryTbody.innerHTML = b.historical_days_detail.map(day => `
        <tr ${day.is_anomalous ? 'style="background: #fffbeb;"' : ''}>
          <td><strong>${day.date}</strong> ${day.is_anomalous ? '<span title="' + escapeHtml(day.anomaly_reason || 'Covers exceed guests') + '" style="cursor:help;">⚠️</span>' : ''}</td>
          <td>${day.weekday_name}</td>
          <td>${day.guests_included}</td>
          <td>${day.covers_included}</td>
          <td><strong style="color:${day.capture_rate_included > 100 ? '#b45309' : '#176b5b'};">${day.capture_rate_included}%${day.capture_rate_included > 100 ? ' ⚠️' : ''}</strong></td>
          <td>${day.guests_other}</td>
          <td>${day.covers_other}</td>
          <td><strong style="color:${day.capture_rate_other > 100 ? '#b45309' : '#2563eb'};">${day.capture_rate_other}%${day.capture_rate_other > 100 ? ' ⚠️' : ''}</strong></td>
          <td>${day.event_covers}</td>
        </tr>
      `).join('');
    }

    // Excluded matching dates table
    if (elements.calcExcludedDetails && elements.calcExcludedTbody) {
      if (b.excluded_days_detail && b.excluded_days_detail.length > 0) {
        elements.calcExcludedDetails.style.display = 'block';
        elements.calcExcludedTbody.innerHTML = b.excluded_days_detail.map(d => `
          <tr style="background: #fffbeb;">
            <td><strong>${d.date}</strong></td>
            <td>${d.weekday_name}</td>
            <td>${d.guests_included !== null ? d.guests_included : '—'} / ${d.covers_included !== null ? d.covers_included : '—'}</td>
            <td>${d.guests_other !== null ? d.guests_other : '—'} / ${d.covers_other !== null ? d.covers_other : '—'}</td>
            <td style="color:#b45309; font-size:0.75rem; font-weight:600;">${escapeHtml(d.reason)}</td>
            <td><span style="background:#fef3c7; color:#92400e; font-size:0.68rem; font-weight:700; padding:0.15rem 0.4rem; border-radius:4px;">⚠️ ${escapeHtml(d.status || 'Requires Verification')}</span></td>
          </tr>
        `).join('');
      } else {
        elements.calcExcludedDetails.style.display = 'none';
      }
    }
  }

  // Food portions table
  const itemNames = { idli: 'Idli', dosa: 'Dosa', pongal: 'Pongal', poori: 'Poori', sambar: 'Sambar', bread: 'Bread' };
  if (elements.forecastPortionsBody) {
    elements.forecastPortionsBody.innerHTML = Object.entries(data.food_portions).map(([item, estimate]) => {
      const isIntegerUnit = estimate.unit === 'pieces';
      const baseDisp = isIntegerUnit ? Math.round(estimate.base_portions) : Number(estimate.base_portions).toFixed(1);
      const prepDisp = isIntegerUnit ? Math.round(estimate.estimated_portions) : Number(estimate.estimated_portions).toFixed(1);
      const diffVal = estimate.buffer_amount !== undefined && estimate.buffer_amount !== null
        ? (isIntegerUnit ? `+${Math.round(estimate.buffer_amount)}` : `+${Number(estimate.buffer_amount).toFixed(1)}`)
        : `+${estimate.buffer_percent}%`;
      const bufferBadge = `<span style="font-size:0.75rem; color:#176b5b; font-weight:600;">+${estimate.buffer_percent}% (${diffVal} ${estimate.unit})</span>`;

      return `
        <tr>
          <th scope="row">${escapeHtml(itemNames[item] || item)}</th>
          <td><span style="font-size:0.75rem; color:var(--neutral-500);">${estimate.unit || 'portions'}</span></td>
          <td>${Number(estimate.servings_per_guest).toFixed(2)}</td>
          <td>${baseDisp}</td>
          <td>${bufferBadge}</td>
          <td><strong style="color:#176b5b; font-size:0.95rem;">${prepDisp}</strong></td>
        </tr>
      `;
    }).join('');
  }

  // Comparative ML Models table
  if (elements.forecastModelsBody) {
    elements.forecastModelsBody.innerHTML = data.model_comparison.map(result => `
      <tr class="${result.model === data.selected_model ? 'is-selected' : ''}">
        <th scope="row">${escapeHtml(result.model)}${result.model === data.selected_model ? '<span class="model-best">Selected</span>' : ''}</th>
        <td>${result.predicted_guests.toLocaleString()}</td>
        <td>${Number(result.mae).toFixed(2)}</td>
        <td>${Number(result.rmse).toFixed(2)}</td>
      </tr>
    `).join('');
  }

  if (elements.forecastEmpty) elements.forecastEmpty.hidden = true;
  if (elements.forecastResults) elements.forecastResults.hidden = false;
}

// Dynamic total guests update
function updateTotalForecastGuests() {
  const incEl = elements.forecastGuestsIncluded || document.getElementById('forecast-guests-included');
  const othEl = elements.forecastGuestsOther || document.getElementById('forecast-guests-other');
  const labelEl = elements.forecastTotalGuestsLabel || document.getElementById('forecast-total-guests-label');
  const inc = parseInt((incEl && incEl.value !== undefined) ? incEl.value : 0, 10) || 0;
  const oth = parseInt((othEl && othEl.value !== undefined) ? othEl.value : 0, 10) || 0;
  if (labelEl) {
    labelEl.textContent = (inc + oth).toLocaleString();
  }
}
if (elements.forecastGuestsIncluded) elements.forecastGuestsIncluded.addEventListener('input', updateTotalForecastGuests);
if (elements.forecastGuestsOther) elements.forecastGuestsOther.addEventListener('input', updateTotalForecastGuests);

// Buffer slider update
if (elements.forecastBufferSlider) {
  elements.forecastBufferSlider.addEventListener('input', () => {
    const val = elements.forecastBufferSlider.value;
    if (elements.bufferValDisplay) elements.bufferValDisplay.textContent = `${val}%`;
    if (elements.forecastBufferAppliedLabel) elements.forecastBufferAppliedLabel.textContent = `Buffered (+${val}%)`;
  });
}

// Toggle history details table
if (elements.btnToggleDetails) {
  elements.btnToggleDetails.addEventListener('click', () => {
    if (!elements.calcHistoryDetails) return;
    const isHidden = elements.calcHistoryDetails.style.display === 'none';
    elements.calcHistoryDetails.style.display = isHidden ? 'block' : 'none';
    elements.btnToggleDetails.textContent = isHidden ? 'Hide History Table' : 'View History Table';
  });
}

// Date change weekday indicator
if (elements.forecastDate) {
  elements.forecastDate.addEventListener('change', () => {
    if (elements.forecastDate && elements.forecastDate.value && elements.forecastWeekdayHint) {
      const d = new Date(elements.forecastDate.value + 'T00:00:00');
      const dayName = d.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' });
      elements.forecastWeekdayHint.textContent = `Service day: ${dayName}`;
    }
  });
}

const forecastFormElement = elements.forecastForm || document.getElementById('forecast-form');
if (forecastFormElement) {
  forecastFormElement.addEventListener('submit', async (event) => {
    event.preventDefault();

    // Dynamically resolve all elements to protect against unmounted or modified DOM nodes
    const dateInput = elements.forecastDate || document.getElementById('forecast-date');
    const guestsIncludedInput = elements.forecastGuestsIncluded || document.getElementById('forecast-guests-included');
    const guestsOtherInput = elements.forecastGuestsOther || document.getElementById('forecast-guests-other');
    const eventCoversInput = elements.forecastEventCovers || document.getElementById('forecast-event-covers');
    const bufferSliderInput = elements.forecastBufferSlider || document.getElementById('forecast-buffer-slider');
    const holidayInput = elements.forecastHoliday || document.getElementById('forecast-holiday');
    const specialEventInput = elements.forecastEvent || document.getElementById('forecast-event');
    const messageElement = elements.forecastFormMessage || document.getElementById('forecast-form-message');
    const submitBtn = elements.forecastSubmit || document.getElementById('btn-run-forecast');

    if (messageElement) {
      messageElement.textContent = '';
      messageElement.classList.remove('is-error');
    }

    let dateValue;
    let guestsIncluded;
    let guestsOther;
    let eventExpectedCovers;
    let bufferPercent;
    const portionAssumptions = {};

    try {
      // 1. Service date validation
      if (!dateInput) {
        throw new Error('Breakfast service date input field is missing.');
      }
      dateValue = (dateInput.value || '').trim();
      if (!dateValue) {
        throw new Error('Choose a future breakfast service date.');
      }
      const today = new Date();
      const todayIso = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
      if (dateValue <= todayIso) {
        throw new Error('Choose a future breakfast service date.');
      }

      // 2. Separate resident guest categories validation (with legacy fallback)
      if (guestsIncludedInput && guestsOtherInput) {
        const incValStr = (guestsIncludedInput.value !== undefined ? guestsIncludedInput.value : '').toString().trim();
        const othValStr = (guestsOtherInput.value !== undefined ? guestsOtherInput.value : '').toString().trim();
        guestsIncluded = validateWholeNonNegative(incValStr, 'Guests with breakfast included', true);
        guestsOther = validateWholeNonNegative(othValStr, 'Guests without breakfast included', true);
      } else {
        const legacyGuestsInput = document.getElementById('forecast-guests');
        if (legacyGuestsInput && legacyGuestsInput.value !== undefined) {
          const totalVal = validateWholeNonNegative(legacyGuestsInput.value, 'Expected guests', true);
          guestsIncluded = Math.round(totalVal * 0.75);
          guestsOther = totalVal - guestsIncluded;
        } else {
          throw new Error('Resident guest input fields are missing from the form.');
        }
      }

      const totalOcc = guestsIncluded + guestsOther;
      if (totalOcc < 50 || totalOcc > 200) {
        throw new Error('Total expected occupancy (Included + Without Breakfast) must be between 50 and 200 guests.');
      }

      // 3. Event Expected Covers validation
      const eventValStr = (eventCoversInput && eventCoversInput.value !== undefined && eventCoversInput.value !== '')
        ? eventCoversInput.value
        : '0';
      eventExpectedCovers = validateWholeNonNegative(eventValStr, 'Event Expected Covers', false) || 0;

      // 4. Preparation buffer slider
      bufferPercent = (bufferSliderInput && bufferSliderInput.value !== undefined && bufferSliderInput.value !== '')
        ? parseFloat(bufferSliderInput.value)
        : 10.0;
      if (isNaN(bufferPercent) || bufferPercent < 0 || bufferPercent > 25) {
        bufferPercent = 10.0;
      }

      // 5. Portion assumption inputs
      const portionInputs = document.querySelectorAll('[data-portion-item]');
      if (portionInputs && portionInputs.length > 0) {
        portionInputs.forEach(input => {
          if (!input || input.value === undefined) return;
          const rawVal = input.value.trim();
          const itemKey = (input.dataset && input.dataset.portionItem) ? input.dataset.portionItem : 'item';
          const itemName = itemKey.charAt(0).toUpperCase() + itemKey.slice(1);
          if (rawVal === '') {
            throw new Error(`${itemName} servings per guest is required (0 to 3).`);
          }
          const val = Number(rawVal);
          if (!Number.isFinite(val) || val < 0 || val > 3) {
            throw new Error(`${itemName} servings per guest must be between 0 and 3.`);
          }
          portionAssumptions[itemKey] = val;
        });
      }
    } catch (error) {
      if (messageElement) {
        messageElement.textContent = error.message;
        messageElement.classList.add('is-error');
      } else {
        showToast('Validation Error', error.message, 'error');
      }
      return;
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Calculating forecast...';
    }
    if (messageElement) {
      messageElement.textContent = 'Querying matching historical weekdays...';
    }

    try {
      const response = await fetch('/api/forecast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          forecast_date: dateValue,
          guests_included: guestsIncluded,
          guests_other: guestsOther,
          event_expected_covers: eventExpectedCovers,
          is_holiday: holidayInput ? Boolean(holidayInput.checked) : false,
          special_event: specialEventInput ? Boolean(specialEventInput.checked) : false,
          buffer_percent: bufferPercent,
          portion_assumptions: portionAssumptions
        })
      });
      const data = await response.json();
      if (!response.ok) {
        const detail = data.detail;
        throw new Error(Array.isArray(detail) ? detail.join(' ') : detail || 'Forecast request failed.');
      }

      renderForecast(data);
      if (messageElement) {
        messageElement.textContent = 'Forecast ready.';
      }
    } catch (error) {
      if (messageElement) {
        messageElement.textContent = error.message || 'Could not generate the forecast.';
        messageElement.classList.add('is-error');
      } else {
        showToast('Forecast Error', error.message || 'Could not generate the forecast.', 'error');
      }
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span aria-hidden="true">↗</span> Forecast Breakfast Demand';
      }
    }
  });
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
          ${row.requires_verification ? `<div style="font-size: 0.68rem; font-weight: 700; color: #b45309; margin-top: 0.25rem;" title="${escapeHtml(row.verification_reason || 'Requires Verification')}">⚠️ Verification Required</div>` : ''}
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

// Dynamic total resident guests calculation for Occupancy Form
function updateOccTotalResidentGuests() {
  const inc = parseInt(elements.occGuestsIncluded ? elements.occGuestsIncluded.value : 0, 10) || 0;
  const oth = parseInt(elements.occGuestsOther ? elements.occGuestsOther.value : 0, 10) || 0;
  if (elements.occTotalResidentDisplay) {
    elements.occTotalResidentDisplay.textContent = (inc + oth).toLocaleString();
  }
}
if (elements.occGuestsIncluded) elements.occGuestsIncluded.addEventListener('input', updateOccTotalResidentGuests);
if (elements.occGuestsOther) elements.occGuestsOther.addEventListener('input', updateOccTotalResidentGuests);

// Story 1: Submit Expected Occupancy
elements.occupancyForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const targetDate = elements.occDate.value;
  if (!targetDate) {
    showToast('Validation Error', 'Please select a valid date.', 'error');
    return;
  }

  let count, guestsInc, guestsOth, eventCovers, rooms;
  try {
    if (elements.occGuestsIncluded && elements.occGuestsOther) {
      guestsInc = validateWholeNonNegative(elements.occGuestsIncluded.value, 'Guests with breakfast included', true);
      guestsOth = validateWholeNonNegative(elements.occGuestsOther.value, 'Guests without breakfast', true);
      eventCovers = validateWholeNonNegative(elements.occEventCovers ? elements.occEventCovers.value : 0, 'Event expected covers', false) || 0;
      count = guestsInc + guestsOth;
      elements.occGuestsIncluded.classList.remove('is-invalid');
      elements.occGuestsOther.classList.remove('is-invalid');
      if (elements.occEventCovers) elements.occEventCovers.classList.remove('is-invalid');
    } else {
      const occFallback = elements.occCount || document.getElementById('occ-count');
      if (occFallback && occFallback.value !== undefined) {
        count = validateWholeNonNegative(occFallback.value, 'Expected guests', true);
        occFallback.classList.remove('is-invalid');
      } else {
        throw new Error('Occupancy guest input fields are required.');
      }
    }
    rooms = validateWholeNonNegative(elements.occRooms.value, 'Total rooms', false);
    elements.occRooms.classList.remove('is-invalid');
  } catch (err) {
    showToast('Validation Error', err.message, 'error');
    if (elements.occGuestsIncluded && err.message.includes('breakfast included')) elements.occGuestsIncluded.classList.add('is-invalid');
    if (elements.occGuestsOther && err.message.includes('without breakfast')) elements.occGuestsOther.classList.add('is-invalid');
    if (elements.occCount && err.message.includes('Expected guests')) elements.occCount.classList.add('is-invalid');
    if (err.message.includes('Total rooms')) elements.occRooms.classList.add('is-invalid');
    return;
  }

  const notes = elements.occNotes.value.trim();

  try {
    const payload = {
      date: targetDate,
      expected_occupancy: count,
      total_rooms: rooms,
      notes: notes
    };
    if (guestsInc !== undefined && guestsOth !== undefined) {
      payload.guests_included = guestsInc;
      payload.guests_other = guestsOth;
      payload.event_expected_covers = eventCovers;
    }

    const res = await fetch('/api/occupancy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
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
    
    // Clear inputs
    if (elements.occGuestsIncluded) elements.occGuestsIncluded.value = '';
    if (elements.occGuestsOther) elements.occGuestsOther.value = '';
    if (elements.occEventCovers) elements.occEventCovers.value = '0';
    if (elements.occTotalResidentDisplay) elements.occTotalResidentDisplay.textContent = '0';
    if (elements.occCount) elements.occCount.value = '';
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


// ==========================================
// Epic 3: Dish Records, Waste & Accuracy
// ==========================================
const dishState = {
  records: [],
  selectedDish: 'all',
  chartDish: 'idli',
  startDate: '',
  endDate: '',
};

// Dish elements
const dishElements = {
  form: document.getElementById('dish-record-form'),
  date: document.getElementById('dish-date'),
  itemSelect: document.getElementById('dish-select-item'),
  prep: document.getElementById('dish-prep'),
  cons: document.getElementById('dish-cons'),
  disc: document.getElementById('dish-disc'),
  stockout: document.getElementById('dish-stockout'),
  notes: document.getElementById('dish-notes'),
  banner: document.getElementById('dish-banner'),
  recordsCountText: document.getElementById('dish-records-count-text'),
  tableBody: document.getElementById('dish-table-body'),
  filterPills: document.getElementById('dish-filter-pills'),
  filterStart: document.getElementById('dish-filter-start'),
  filterEnd: document.getElementById('dish-filter-end'),
  filterApply: document.getElementById('dish-filter-apply'),
  filterReset: document.getElementById('dish-filter-reset'),
  chartTitle: document.getElementById('chart-dish-title'),
  chartWrap: document.getElementById('dish-trend-svg-wrap'),
  // Accuracy elements
  accMapeBadge: document.getElementById('accuracy-mape-badge'),
  accEligibleCount: document.getElementById('acc-eligible-count'),
  accStockoutCount: document.getElementById('acc-stockout-count'),
  accZeroCount: document.getElementById('acc-zero-count'),
  accTableBody: document.getElementById('accuracy-table-body'),
  // Waste elements
  wasteTableBody: document.getElementById('waste-summary-table-body'),
  // Edit Dish Modal
  editModal: document.getElementById('edit-dish-modal'),
  editForm: document.getElementById('edit-dish-form'),
  editDate: document.getElementById('edit-dish-date'),
  editName: document.getElementById('edit-dish-name'),
  editDateLabel: document.getElementById('dish-modal-date-label'),
  editDishLabel: document.getElementById('dish-modal-dish-label'),
  editPrep: document.getElementById('edit-dish-prep'),
  editCons: document.getElementById('edit-dish-cons'),
  editDisc: document.getElementById('edit-dish-disc'),
  editStockout: document.getElementById('edit-dish-stockout'),
  editNotes: document.getElementById('edit-dish-notes'),
  editClose: document.getElementById('edit-dish-modal-close'),
  editCancel: document.getElementById('edit-dish-modal-cancel'),
};

// Set default date for dish form
function initDishFormDefaults() {
  if (dishElements.date && !dishElements.date.value) {
    dishElements.date.value = new Date().toISOString().split('T')[0];
  }
}

// Fetch all dish records with current filters
async function fetchDishRecords() {
  try {
    let url = '/api/dishes/records?';
    const params = new URLSearchParams();
    if (dishState.selectedDish && dishState.selectedDish !== 'all') {
      params.append('dish', dishState.selectedDish);
    }
    if (dishState.startDate) params.append('start_date', dishState.startDate);
    if (dishState.endDate) params.append('end_date', dishState.endDate);
    url += params.toString();

    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    dishState.records = await res.json();

    renderDishTable();
    renderDishChart();
  } catch (err) {
    console.error('Error fetching dish records:', err);
  }
}

// Render Dish Records Table
function renderDishTable() {
  if (!dishElements.tableBody) return;
  const records = dishState.records;

  if (dishElements.recordsCountText) {
    dishElements.recordsCountText.textContent = `${records.length} record${records.length !== 1 ? 's' : ''}`;
  }

  if (records.length === 0) {
    dishElements.tableBody.innerHTML = `
      <tr>
        <td colspan="10" style="text-align:center; padding: 2.5rem 1rem; color: var(--neutral-400);">
          No dish service logs found for selected criteria. Log daily observations using the form on the left.
        </td>
      </tr>
    `;
    return;
  }

  dishElements.tableBody.innerHTML = records.map(r => {
    const prep = Number(r.quantity_prepared);
    const disc = Number(r.quantity_discarded);
    const wastePct = prep > 0 ? ((disc / prep) * 100).toFixed(1) + '%' : '—';
    const stockBadge = r.stock_out
      ? `<span style="background:#fee2e2; color:#b91c1c; font-size:0.7rem; font-weight:700; padding:0.2rem 0.5rem; border-radius:4px;">⚠️ Stock-Out</span>`
      : `<span style="color:var(--neutral-400); font-size:0.75rem;">Normal</span>`;

    return `
      <tr>
        <td style="font-weight:600;">${r.date}</td>
        <td><strong style="text-transform:capitalize;">${r.dish}</strong></td>
        <td style="white-space:nowrap;"><span style="background:#fef3c7; color:#92400e; font-size:0.68rem; font-weight:700; padding:0.15rem 0.45rem; border-radius:4px; border:1px solid #fde68a;" title="Synthetic demonstration record — unverified demo data, not real hotel kitchen log">🧪 Synthetic Demo</span></td>
        <td>${r.quantity_prepared} <span style="font-size:0.72rem; color:var(--neutral-400);">${r.unit}</span></td>
        <td>${r.quantity_consumed} <span style="font-size:0.72rem; color:var(--neutral-400);">${r.unit}</span></td>
        <td style="color:#ef4444; font-weight:600;">${r.quantity_discarded} <span style="font-size:0.72rem; color:var(--neutral-400);">${r.unit}</span></td>
        <td><strong>${wastePct}</strong></td>
        <td>${stockBadge}</td>
        <td style="font-size:0.75rem; color:var(--neutral-500); max-width:180px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${escapeHtml(r.notes || '')}">
          ${escapeHtml(r.notes || '—')}
        </td>
        <td style="text-align: right; white-space: nowrap;">
          <button class="action-icon-btn" onclick="openEditDishModal('${r.date}', '${r.dish}')" title="Edit / correct entry">✏️</button>
          <button class="action-icon-btn delete" onclick="deleteDishEntry('${r.date}', '${r.dish}')" title="Delete entry">🗑</button>
        </td>
      </tr>
    `;
  }).join('');
}

// Render Interactive SVG Trend Chart
function renderDishChart() {
  if (!dishElements.chartWrap) return;
  const targetDish = dishState.chartDish || 'idli';
  if (dishElements.chartTitle) {
    dishElements.chartTitle.textContent = targetDish.charAt(0).toUpperCase() + targetDish.slice(1);
  }

  // Filter records for this dish and sort date ascending
  const dishLogs = dishState.records
    .filter(r => r.dish.toLowerCase() === targetDish.toLowerCase())
    .sort((a, b) => a.date.localeCompare(b.date));

  if (dishLogs.length === 0) {
    dishElements.chartWrap.innerHTML = `
      <div style="display:flex; align-items:center; justify-content:center; height:100%; color:var(--neutral-400); font-size:0.8rem;">
        No recorded observations for ${targetDish}. Log service records to generate trend visualization.
      </div>
    `;
    return;
  }

  const width = Math.max(540, dishLogs.length * 55);
  const height = 170;
  const pad = { top: 20, right: 30, bottom: 35, left: 45 };

  let maxQty = Math.max(...dishLogs.map(r => Math.max(r.quantity_prepared, r.quantity_consumed, r.quantity_discarded)), 10);
  maxQty = Math.ceil(maxQty * 1.15);

  const getX = (i) => pad.left + (dishLogs.length === 1 ? (width - pad.left - pad.right) / 2 : (i / (dishLogs.length - 1)) * (width - pad.left - pad.right));
  const getY = (val) => height - pad.bottom - ((val / maxQty) * (height - pad.top - pad.bottom));

  // Points
  const prepPts = dishLogs.map((r, i) => `${getX(i).toFixed(1)},${getY(r.quantity_prepared).toFixed(1)}`).join(' ');
  const consPts = dishLogs.map((r, i) => `${getX(i).toFixed(1)},${getY(r.quantity_consumed).toFixed(1)}`).join(' ');
  const discPts = dishLogs.map((r, i) => `${getX(i).toFixed(1)},${getY(r.quantity_discarded).toFixed(1)}`).join(' ');

  // Dots
  const dotsHtml = dishLogs.map((r, i) => {
    const x = getX(i);
    const yP = getY(r.quantity_prepared);
    const yC = getY(r.quantity_consumed);
    const yD = getY(r.quantity_discarded);
    const stockMarker = r.stock_out
      ? `<text x="${x}" y="${yC - 9}" font-size="11" text-anchor="middle" fill="#dc2626">⚠️</text>`
      : '';

    return `
      <circle cx="${x}" cy="${yP}" r="3.5" fill="#0284c7"><title>${r.date} Prepared: ${r.quantity_prepared} ${r.unit}</title></circle>
      <circle cx="${x}" cy="${yC}" r="3.5" fill="#10b981"><title>${r.date} Consumed: ${r.quantity_consumed} ${r.unit}</title></circle>
      <circle cx="${x}" cy="${yD}" r="3" fill="#ef4444"><title>${r.date} Discarded: ${r.quantity_discarded} ${r.unit}</title></circle>
      ${stockMarker}
      <text x="${x}" y="${height - 12}" font-size="9" text-anchor="middle" fill="#64748b">${r.date.slice(5)}</text>
    `;
  }).join('');

  // Y-axis grid
  const yTicks = [0, Math.round(maxQty * 0.5), maxQty];
  const gridHtml = yTicks.map(t => {
    const y = getY(t);
    return `
      <line x1="${pad.left}" y1="${y}" x2="${width - pad.right}" y2="${y}" stroke="#e2e8f0" stroke-dasharray="3,3" />
      <text x="${pad.left - 6}" y="${y + 3}" font-size="9" text-anchor="end" fill="#94a3b8">${t}</text>
    `;
  }).join('');

  dishElements.chartWrap.innerHTML = `
    <svg width="${width}" height="${height}" style="min-width:100%; display:block;">
      ${gridHtml}
      <line x1="${pad.left}" y1="${height - pad.bottom}" x2="${width - pad.right}" y2="${height - pad.bottom}" stroke="#cbd5e1" stroke-width="1.5" />
      <polyline points="${prepPts}" fill="none" stroke="#0284c7" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
      <polyline points="${consPts}" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
      <polyline points="${discPts}" fill="none" stroke="#ef4444" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="4,2" />
      ${dotsHtml}
    </svg>
  `;
}

// Fetch & Render Forecast Accuracy
async function fetchForecastAccuracy() {
  try {
    const res = await fetch('/api/accuracy?days=14');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (dishElements.accMapeBadge) {
      dishElements.accMapeBadge.textContent = data.mape !== null ? `MAPE: ${data.mape}%` : 'MAPE: Insufficient data';
    }
    if (dishElements.accEligibleCount) dishElements.accEligibleCount.textContent = data.eligible_days_count;
    if (dishElements.accStockoutCount) dishElements.accStockoutCount.textContent = data.excluded_stockout_days;
    if (dishElements.accZeroCount) dishElements.accZeroCount.textContent = data.zero_actual_days_excluded;

    if (dishElements.accTableBody) {
      if (!data.evaluations || data.evaluations.length === 0) {
        dishElements.accTableBody.innerHTML = `
          <tr><td colspan="7" style="text-align:center; padding:1.5rem; color:var(--neutral-400);">No service evaluations available.</td></tr>
        `;
        return;
      }

      dishElements.accTableBody.innerHTML = data.evaluations.map(e => {
        const apeText = e.absolute_percentage_error !== null ? `${e.absolute_percentage_error}%` : '—';
        const predText = e.predicted_covers !== null ? e.predicted_covers : '—';
        const errText = e.absolute_error !== null ? e.absolute_error : '—';
        let statusBadge = '';
        if (e.eligible) {
          statusBadge = `<span style="background:#d1fae5; color:#065f46; font-size:0.7rem; font-weight:700; padding:0.15rem 0.45rem; border-radius:4px;">Eligible</span>`;
        } else if (e.stock_out_occurred) {
          statusBadge = `<span style="background:#fee2e2; color:#991b1b; font-size:0.7rem; font-weight:700; padding:0.15rem 0.45rem; border-radius:4px;" title="${escapeHtml(e.ineligibility_reason || '')}">Excluded (Stock-out)</span>`;
        } else {
          statusBadge = `<span style="background:#fef3c7; color:#92400e; font-size:0.7rem; font-weight:700; padding:0.15rem 0.45rem; border-radius:4px;" title="${escapeHtml(e.ineligibility_reason || '')}">Excluded</span>`;
        }

        return `
          <tr>
            <td style="font-weight:600;">${e.date}</td>
            <td>${e.weekday}</td>
            <td><strong>${e.actual_covers}</strong></td>
            <td>${predText}</td>
            <td>${errText}</td>
            <td><strong style="color:${e.absolute_percentage_error !== null && e.absolute_percentage_error > 20 ? '#dc2626' : '#16a34a'};">${apeText}</strong></td>
            <td>${statusBadge}</td>
          </tr>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Error fetching forecast accuracy:', err);
  }
}

// Fetch & Render Waste and Shortage Analysis
async function fetchWasteAnalysis() {
  try {
    const res = await fetch('/api/waste/analysis');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (dishElements.wasteTableBody && data.dish_summaries) {
      dishElements.wasteTableBody.innerHTML = data.dish_summaries.map(s => {
        const wastePct = s.waste_percentage !== null ? `${s.waste_percentage}%` : '—';
        const simWaste = s.simulated_waste !== null ? `${s.simulated_waste} <span style="font-size:0.68rem; background:#ede9fe; color:#6d28d9; padding:0.1rem 0.35rem; border-radius:3px;">SIM</span>` : '<span style="color:var(--neutral-400);">Insufficient data</span>';
        const simShortage = s.simulated_shortage !== null ? `${s.simulated_shortage} <span style="font-size:0.68rem; background:#fee2e2; color:#991b1b; padding:0.1rem 0.35rem; border-radius:3px;">SIM</span>` : '<span style="color:var(--neutral-400);">Insufficient data</span>';

        return `
          <tr>
            <td><strong>${s.dish}</strong></td>
            <td><span style="font-size:0.75rem; color:var(--neutral-500);">${s.unit}</span></td>
            <td>${s.days_recorded}</td>
            <td>${s.total_prepared}</td>
            <td>${s.total_consumed}</td>
            <td style="color:#ef4444; font-weight:600;">${s.total_discarded}</td>
            <td><strong>${wastePct}</strong></td>
            <td>${s.stock_out_days > 0 ? `<span style="color:#dc2626; font-weight:700;">${s.stock_out_days}</span>` : '0'}</td>
            <td>${simWaste}</td>
            <td>${simShortage}</td>
          </tr>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Error fetching waste analysis:', err);
  }
}

// Log Dish Form Submit
if (dishElements.form) {
  dishElements.form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const dateVal = dishElements.date.value.trim();
    const dishVal = dishElements.itemSelect.value.trim();
    const prepVal = parseFloat(dishElements.prep.value);
    const consVal = parseFloat(dishElements.cons.value);
    const discVal = parseFloat(dishElements.disc.value);
    const stockVal = dishElements.stockout.checked;
    const notesVal = dishElements.notes.value.trim();

    if (!dateVal || !dishVal || isNaN(prepVal) || isNaN(consVal) || isNaN(discVal)) {
      showToast('Validation Error', 'Please enter valid non-negative quantities for all required fields.', 'error');
      return;
    }
    if (prepVal < 0 || consVal < 0 || discVal < 0) {
      showToast('Validation Error', 'Quantities cannot be negative.', 'error');
      return;
    }
    if ((consVal + discVal) > (prepVal + 0.01)) {
      showToast('Validation Error', `Sum of consumed (${consVal}) and discarded (${discVal}) cannot exceed prepared quantity (${prepVal}).`, 'error');
      return;
    }

    try {
      const res = await fetch('/api/dishes/records', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: dateVal,
          dish: dishVal,
          quantity_prepared: prepVal,
          quantity_consumed: consVal,
          quantity_discarded: discVal,
          stock_out: stockVal,
          notes: notesVal
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || `Server error ${res.status}`);
      }

      showToast('Saved', `Dish log for ${dishVal} on ${dateVal} saved successfully.`, 'success');
      dishElements.prep.value = '';
      dishElements.cons.value = '';
      dishElements.disc.value = '';
      dishElements.stockout.checked = false;
      dishElements.notes.value = '';

      // Refresh all views
      await fetchDishRecords();
      await fetchForecastAccuracy();
      await fetchWasteAnalysis();
    } catch (err) {
      showToast('Error', err.message, 'error');
    }
  });
}

// Open Edit Dish Modal
window.openEditDishModal = function(dateStr, dishStr) {
  const record = dishState.records.find(r => r.date === dateStr && r.dish.toLowerCase() === dishStr.toLowerCase());
  if (!record) return;

  if (dishElements.editDate) dishElements.editDate.value = record.date;
  if (dishElements.editName) dishElements.editName.value = record.dish;
  if (dishElements.editDateLabel) dishElements.editDateLabel.textContent = record.date;
  if (dishElements.editDishLabel) dishElements.editDishLabel.textContent = record.dish.toUpperCase();
  if (dishElements.editPrep) dishElements.editPrep.value = record.quantity_prepared;
  if (dishElements.editCons) dishElements.editCons.value = record.quantity_consumed;
  if (dishElements.editDisc) dishElements.editDisc.value = record.quantity_discarded;
  if (dishElements.editStockout) dishElements.editStockout.checked = Boolean(record.stock_out);
  if (dishElements.editNotes) dishElements.editNotes.value = record.notes || '';

  if (dishElements.editModal) dishElements.editModal.classList.add('active');
};

function closeEditDishModal() {
  if (dishElements.editModal) dishElements.editModal.classList.remove('active');
}

if (dishElements.editClose) dishElements.editClose.addEventListener('click', closeEditDishModal);
if (dishElements.editCancel) dishElements.editCancel.addEventListener('click', closeEditDishModal);

// Edit Dish Form Submit
if (dishElements.editForm) {
  dishElements.editForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const dateVal = dishElements.editDate.value;
    const dishVal = dishElements.editName.value;
    const prepVal = parseFloat(dishElements.editPrep.value);
    const consVal = parseFloat(dishElements.editCons.value);
    const discVal = parseFloat(dishElements.editDisc.value);
    const stockVal = dishElements.editStockout.checked;
    const notesVal = dishElements.editNotes.value.trim();

    if (isNaN(prepVal) || isNaN(consVal) || isNaN(discVal)) {
      showToast('Validation Error', 'Quantities must be valid numbers.', 'error');
      return;
    }
    if ((consVal + discVal) > (prepVal + 0.01)) {
      showToast('Validation Error', `Sum of consumed (${consVal}) and discarded (${discVal}) cannot exceed prepared (${prepVal}).`, 'error');
      return;
    }

    try {
      const res = await fetch(`/api/dishes/records/${dateVal}/${dishVal}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quantity_prepared: prepVal,
          quantity_consumed: consVal,
          quantity_discarded: discVal,
          stock_out: stockVal,
          notes: notesVal
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `Server error ${res.status}`);
      }

      closeEditDishModal();
      showToast('Updated', `Record for ${dishVal} on ${dateVal} corrected successfully.`, 'success');
      await fetchDishRecords();
      await fetchForecastAccuracy();
      await fetchWasteAnalysis();
    } catch (err) {
      showToast('Error', err.message, 'error');
    }
  });
}

// Delete Dish Entry
window.deleteDishEntry = async function(dateStr, dishStr) {
  if (!confirm(`Are you sure you want to delete the daily log for ${dishStr} on ${dateStr}?`)) return;
  try {
    const res = await fetch(`/api/dishes/records/${dateStr}/${dishStr}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    showToast('Deleted', `Record for ${dishStr} removed.`, 'success');
    await fetchDishRecords();
    await fetchForecastAccuracy();
    await fetchWasteAnalysis();
  } catch (err) {
    showToast('Error', err.message, 'error');
  }
};

// Dish Filter Events
if (dishElements.filterPills) {
  dishElements.filterPills.addEventListener('click', (e) => {
    if (e.target.classList.contains('pill-btn')) {
      dishElements.filterPills.querySelectorAll('.pill-btn').forEach(btn => btn.classList.remove('active'));
      e.target.classList.add('active');
      const selected = e.target.getAttribute('data-dish');
      dishState.selectedDish = selected;
      if (selected !== 'all') {
        dishState.chartDish = selected;
      }
      fetchDishRecords();
    }
  });
}

if (dishElements.filterApply) {
  dishElements.filterApply.addEventListener('click', () => {
    dishState.startDate = dishElements.filterStart.value;
    dishState.endDate = dishElements.filterEnd.value;
    fetchDishRecords();
  });
}

if (dishElements.filterReset) {
  dishElements.filterReset.addEventListener('click', () => {
    dishState.startDate = '';
    dishState.endDate = '';
    if (dishElements.filterStart) dishElements.filterStart.value = '';
    if (dishElements.filterEnd) dishElements.filterEnd.value = '';
    fetchDishRecords();
  });
}

// Hook into Seed and Clear buttons
const originalBtnSeed = document.getElementById('btn-seed');
if (originalBtnSeed) {
  originalBtnSeed.addEventListener('click', () => {
    setTimeout(() => {
      fetchDishRecords();
      fetchForecastAccuracy();
      fetchWasteAnalysis();
    }, 600);
  });
}

const originalBtnClear = document.getElementById('btn-clear');
if (originalBtnClear) {
  originalBtnClear.addEventListener('click', () => {
    setTimeout(() => {
      fetchDishRecords();
      fetchForecastAccuracy();
      fetchWasteAnalysis();
    }, 600);
  });
}

// App Initialization
document.addEventListener('DOMContentLoaded', () => {
  setDefaultDates();
  initDishFormDefaults();
  fetchHistoricalData();
  fetchDishRecords();
  fetchForecastAccuracy();
  fetchWasteAnalysis();
});
