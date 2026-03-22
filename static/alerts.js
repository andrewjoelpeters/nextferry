/**
 * Ferry Arrival Alerts — V1
 *
 * Lets the user set a notification for when the vessel assigned to their
 * sailing is X minutes away from docking at the departure terminal.
 *
 * Data flow:
 *   1. User clicks bell on a sailing → picks "notify me N min before arrival"
 *   2. Alert stored in localStorage keyed by vessel+departure
 *   3. Polling loop fetches /ferry-data every 30s
 *   4. When vessel.ArrivingTerminalName matches the departure terminal
 *      and vessel ETA − now ≤ threshold → fire browser notification
 */

(function () {
  'use strict';

  const STORAGE_KEY = 'ferry_alerts';
  const POLL_INTERVAL_MS = 30000;

  let pollTimer = null;

  // ——— Storage helpers ———

  function loadAlerts() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    } catch {
      return [];
    }
  }

  function saveAlerts(alerts) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(alerts));
  }

  function alertKey(vesselName, departure) {
    return vesselName + '|' + departure;
  }

  function findAlert(vesselName, departure) {
    return loadAlerts().find(
      (a) => a.vesselName === vesselName && a.departure === departure
    );
  }

  function addAlert(vesselName, terminal, departure, minutes) {
    let alerts = loadAlerts();
    // Remove existing for same sailing
    alerts = alerts.filter(
      (a) => !(a.vesselName === vesselName && a.departure === departure)
    );
    alerts.push({ vesselName, terminal, departure, minutes, notified: false });
    saveAlerts(alerts);
    ensurePolling();
  }

  function removeAlert(vesselName, departure) {
    let alerts = loadAlerts();
    alerts = alerts.filter(
      (a) => !(a.vesselName === vesselName && a.departure === departure)
    );
    saveAlerts(alerts);
    if (alerts.length === 0) stopPolling();
  }

  function markNotified(vesselName, departure) {
    let alerts = loadAlerts();
    const alert = alerts.find(
      (a) => a.vesselName === vesselName && a.departure === departure
    );
    if (alert) alert.notified = true;
    saveAlerts(alerts);
  }

  // ——— Notification permission ———

  async function requestPermission() {
    if (!('Notification' in window)) return false;
    if (Notification.permission === 'granted') return true;
    if (Notification.permission === 'denied') return false;
    const result = await Notification.requestPermission();
    return result === 'granted';
  }

  function sendNotification(title, body) {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({
        type: 'FERRY_ALERT',
        title,
        body,
      });
    } else if (Notification.permission === 'granted') {
      new Notification(title, { body, icon: '/static/icons/icon-192.png' });
    }
  }

  // ——— Polling ———

  function ensurePolling() {
    if (pollTimer) return;
    pollTimer = setInterval(checkAlerts, POLL_INTERVAL_MS);
    // Also check immediately
    checkAlerts();
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  async function checkAlerts() {
    const alerts = loadAlerts().filter((a) => !a.notified);
    if (alerts.length === 0) {
      stopPolling();
      return;
    }

    let vessels;
    try {
      const resp = await fetch('/ferry-data');
      vessels = await resp.json();
      if (!Array.isArray(vessels)) return;
    } catch {
      return;
    }

    const now = new Date();

    for (const alert of alerts) {
      // Clean up alerts for sailings that have already departed
      const scheduledDep = new Date(alert.departure);
      if (now - scheduledDep > 30 * 60 * 1000) {
        // More than 30 min past scheduled departure — auto-remove
        removeAlert(alert.vesselName, alert.departure);
        continue;
      }

      // Find the matching vessel
      const vessel = vessels.find(
        (v) => v.VesselName === alert.vesselName && v.InService
      );
      if (!vessel) continue;

      // Check if vessel is heading TO the user's departure terminal
      if (vessel.ArrivingTerminalName !== alert.terminal) continue;

      // Parse ETA
      if (!vessel.Eta) continue;
      const eta = parseMsDate(vessel.Eta);
      if (!eta) continue;

      const minutesAway = (eta - now) / 60000;

      if (minutesAway <= alert.minutes && minutesAway > -5) {
        const rounded = Math.max(0, Math.round(minutesAway));
        sendNotification(
          alert.vesselName + ' approaching!',
          rounded === 0
            ? alert.vesselName + ' is arriving at ' + alert.terminal + ' now!'
            : alert.vesselName +
              ' is ~' +
              rounded +
              ' min from ' +
              alert.terminal
        );
        markNotified(alert.vesselName, alert.departure);
        updateBellStates();
      }
    }
  }

  // Parse WSDOT /Date(...)/ format or ISO string
  function parseMsDate(val) {
    if (!val) return null;
    if (typeof val === 'string') {
      const m = val.match(/\/Date\((-?\d+)([+-]\d{4})?\)\//);
      if (m) return new Date(parseInt(m[1], 10));
      const d = new Date(val);
      return isNaN(d) ? null : d;
    }
    return null;
  }

  // ——— UI: Alert picker ———

  function closePickers() {
    document.querySelectorAll('.alert-picker').forEach((el) => el.remove());
  }

  window.openAlertPicker = function (btn) {
    // If a picker is already open for this button, close it
    const existing = btn.closest('.sailing-meta').querySelector('.alert-picker');
    if (existing) {
      existing.remove();
      return;
    }

    closePickers();

    const item = btn.closest('.sailing-item');
    const vesselName = item.dataset.vessel;
    const terminal = item.dataset.terminal;
    const departure = item.dataset.departure;

    if (!vesselName || !departure) return;

    const current = findAlert(vesselName, departure);

    const picker = document.createElement('div');
    picker.className = 'alert-picker';

    const title = document.createElement('div');
    title.className = 'alert-picker-title';
    title.textContent = 'Alert when ' + vesselName + ' is:';
    picker.appendChild(title);

    const options = [5, 10, 15, 20];
    options.forEach((min) => {
      const optBtn = document.createElement('button');
      optBtn.className = 'alert-picker-option';
      optBtn.textContent = min + ' min from ' + terminal;
      if (current && current.minutes === min) {
        optBtn.style.fontWeight = '700';
        optBtn.style.color = 'var(--ocean-deep)';
      }
      optBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const granted = await requestPermission();
        if (!granted) {
          showToast('Please enable notifications in your browser settings');
          closePickers();
          return;
        }
        addAlert(vesselName, terminal, departure, min);
        closePickers();
        updateBellStates();
        showToast('Alert set: ' + vesselName + ' ' + min + 'min from dock');
      });
      picker.appendChild(optBtn);
    });

    // Cancel / remove alert option
    if (current) {
      const cancelBtn = document.createElement('button');
      cancelBtn.className = 'alert-picker-cancel';
      cancelBtn.textContent = 'Remove alert';
      cancelBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        removeAlert(vesselName, departure);
        closePickers();
        updateBellStates();
        showToast('Alert removed');
      });
      picker.appendChild(cancelBtn);
    }

    btn.closest('.sailing-meta').style.position = 'relative';
    btn.closest('.sailing-meta').appendChild(picker);

    // Close when clicking outside
    setTimeout(() => {
      document.addEventListener('click', function handler(e) {
        if (!picker.contains(e.target) && e.target !== btn) {
          closePickers();
          document.removeEventListener('click', handler);
        }
      });
    }, 0);
  };

  // ——— UI: Update bell states ———

  function updateBellStates() {
    const alerts = loadAlerts();
    document.querySelectorAll('.sailing-item').forEach((item) => {
      const vessel = item.dataset.vessel;
      const departure = item.dataset.departure;
      const btn = item.querySelector('.alert-btn');
      if (!btn || !vessel || !departure) return;

      const hasAlert = alerts.some(
        (a) =>
          a.vesselName === vessel && a.departure === departure && !a.notified
      );
      btn.classList.toggle('alert-active', hasAlert);
    });
  }

  // ——— Toast ———

  function showToast(message) {
    let toast = document.querySelector('.alert-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'alert-toast';
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('visible');
    setTimeout(() => toast.classList.remove('visible'), 2500);
  }

  // ——— Init ———

  // Re-apply bell states whenever HTMX swaps in new sailing content
  document.addEventListener('htmx:afterSwap', function (e) {
    if (
      e.detail.target.id === 'sailings-content' ||
      e.detail.target.id === 'tab-content'
    ) {
      updateBellStates();
    }
  });

  // Kick off polling if there are existing alerts
  if (loadAlerts().filter((a) => !a.notified).length > 0) {
    ensurePolling();
  }

  // Initial bell state update
  updateBellStates();
})();
