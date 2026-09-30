/* PocketSmart AI — client-side helpers */
(function () {
  "use strict";

  /* ---------- Flash messages ---------- */
  window.showFlash = function (message, category) {
    var container = document.getElementById("flashContainer");
    if (!container) return;
    var el = document.createElement("div");
    el.className = "flash flash-" + (category || "info");
    var span = document.createElement("span");
    span.textContent = message;
    var close = document.createElement("button");
    close.className = "flash-close";
    close.setAttribute("aria-label", "Dismiss");
    close.innerHTML = "&times;";
    close.addEventListener("click", function () { el.remove(); });
    el.appendChild(span);
    el.appendChild(close);
    container.appendChild(el);
    setTimeout(function () { el.remove(); }, 6000);
  };

  /* ---------- Mobile nav ---------- */
  var navToggle = document.getElementById("navToggle");
  var navLinks = document.getElementById("navLinks");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      var open = navLinks.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* ---------- Logout ---------- */
  var logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async function () {
      logoutBtn.disabled = true;
      try {
        await fetch("/api/auth/logout", { method: "POST" });
        window.location.href = "/";
      } catch (e) {
        window.showFlash("Logout failed. Please try again.", "error");
        logoutBtn.disabled = false;
      }
    });
  }

  /* ---------- Helpers ---------- */
  function setLoading(btn, loading) {
    if (!btn) return;
    var label = btn.querySelector(".btn-label");
    var spinner = btn.querySelector(".spinner");
    btn.disabled = loading;
    if (label) label.style.visibility = loading ? "hidden" : "visible";
    if (spinner) spinner.hidden = !loading;
  }

  function showError(el, message) {
    if (!el) return;
    el.textContent = message;
    el.hidden = false;
  }

  function clearError(el) { if (el) el.hidden = true; }

  function handleApiError(err) {
    if (err && err.detail) {
      if (Array.isArray(err.detail)) {
        return err.detail.map(function (d) { return d.msg; }).join(" ");
      }
      return typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
    }
    return "Something went wrong. Please try again.";
  }

  /* ---------- Auth forms (login / register) ---------- */
  window.initAuthForm = function (opts) {
    var form = document.getElementById(opts.formId);
    var errorEl = document.getElementById(opts.errorId);
    var submitBtn = document.getElementById(opts.submitBtnId);
    if (!form) return;

    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      clearError(errorEl);
      setLoading(submitBtn, true);
      var payload = {
        username: form.username.value.trim(),
        email: form.email ? form.email.value.trim() : undefined,
        password: form.password.value,
      };
      try {
        var res = await fetch(opts.apiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        var data = await res.json().catch(function () { return {}; });
        if (!res.ok) throw data;
        window.location.href = opts.successRedirect;
      } catch (err) {
        showError(errorEl, handleApiError(err));
        setLoading(submitBtn, false);
      }
    });
  };

  /* ---------- Planner forms (home / party) ---------- */
  window.initPlannerForm = function (opts) {
    var form = document.getElementById(opts.formId);
    var errorEl = document.getElementById(opts.errorId);
    var submitBtn = document.getElementById(opts.submitBtnId);
    if (!form) return;

    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      clearError(errorEl);
      setLoading(submitBtn, true);
      var fd = new FormData(form);
      try {
        var res = await fetch(opts.apiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(opts.buildPayload(fd)),
        });
        var data = await res.json().catch(function () { return {}; });
        if (!res.ok) throw data;
        window.location.href = data.redirect || "/dashboard";
      } catch (err) {
        showError(errorEl, handleApiError(err));
        setLoading(submitBtn, false);
      }
    });
  };

  /* ---------- Jewelry form (multipart, optional image) ---------- */
  window.initJewelryForm = function () {
    var form = document.getElementById("jewelryForm");
    var errorEl = document.getElementById("formError");
    var submitBtn = document.getElementById("submitBtn");
    var fileInput = document.getElementById("outfit_image");
    var preview = document.getElementById("imagePreview");
    var previewImg = document.getElementById("imagePreviewImg");
    var removeBtn = document.getElementById("removeImage");
    if (!form) return;

    if (fileInput) {
      fileInput.addEventListener("change", function () {
        var file = fileInput.files && fileInput.files[0];
        if (!file) { preview.hidden = true; return; }
        var okTypes = ["image/png", "image/jpeg", "image/webp"];
        if (okTypes.indexOf(file.type) === -1) {
          window.showFlash("Only PNG, JPG and WEBP images are allowed.", "error");
          fileInput.value = "";
          preview.hidden = true;
          return;
        }
        if (file.size > 5 * 1024 * 1024) {
          window.showFlash("Image exceeds the 5 MB limit.", "error");
          fileInput.value = "";
          preview.hidden = true;
          return;
        }
        var reader = new FileReader();
        reader.onload = function (ev) {
          previewImg.src = ev.target.result;
          preview.hidden = false;
        };
        reader.readAsDataURL(file);
      });
    }
    if (removeBtn) {
      removeBtn.addEventListener("click", function () {
        fileInput.value = "";
        preview.hidden = true;
      });
    }

    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      clearError(errorEl);
      setLoading(submitBtn, true);
      var fd = new FormData(form);
      try {
        var res = await fetch("/api/planners/jewelry", { method: "POST", body: fd });
        var data = await res.json().catch(function () { return {}; });
        if (!res.ok) throw data;
        window.location.href = data.redirect || "/dashboard";
      } catch (err) {
        showError(errorEl, handleApiError(err));
        setLoading(submitBtn, false);
      }
    });
  };
})();
