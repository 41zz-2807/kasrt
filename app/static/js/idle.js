(function () {
  var body = document.body;
  var timeoutMs = (parseInt(body.getAttribute("data-idle-timeout") || "1800", 10) || 1800) * 1000;
  var warningMs = (parseInt(body.getAttribute("data-idle-warning") || "60", 10) || 60) * 1000;
  var state = { timer: null, interval: null, remaining: timeoutMs };

  function format(ms) {
    var total = Math.max(0, Math.ceil(ms / 1000));
    var m = Math.floor(total / 60);
    var s = total % 60;
    return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
  }

  function doLogout() {
    window.location.href = "/logout";
  }

  function tick() {
    state.remaining -= 1000;
    var el = document.getElementById("idle-countdown");
    if (el) {
      el.textContent = format(state.remaining);
    }
    if (state.remaining <= 0) {
      if (state.interval) clearInterval(state.interval);
      doLogout();
    }
  }

  function reset() {
    if (state.timer) clearTimeout(state.timer);
    if (state.interval) clearInterval(state.interval);
    state.remaining = timeoutMs;
    var el = document.getElementById("idle-countdown");
    if (el) el.textContent = format(timeoutMs);
    state.timer = setTimeout(doLogout, timeoutMs);
    if (state.remaining <= warningMs) {
      if (!state.interval) {
        state.interval = setInterval(tick, 1000);
      }
    }
  }

  function onActivity() {
    reset();
  }

  document.addEventListener("click", onActivity, { passive: true });
  document.addEventListener("touchstart", onActivity, { passive: true });
  document.addEventListener("keydown", onActivity, { passive: true });
  window.addEventListener("scroll", onActivity, { passive: true });
  window.addEventListener("focus", onActivity);

  reset();
})();
