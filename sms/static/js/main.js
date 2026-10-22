(function () {
  // Show / hide password on the login page
  var toggle = document.getElementById("pwToggle");
  var pw = document.getElementById("password");
  if (toggle && pw) {
    toggle.addEventListener("click", function () {
      var show = pw.type === "password";
      pw.type = show ? "text" : "password";
      toggle.textContent = show ? "Hide" : "Show";
      toggle.setAttribute("aria-label", show ? "Hide password" : "Show password");
    });
  }

  // Dismiss flash messages
  document.querySelectorAll(".flash-close").forEach(function (btn) {
    btn.addEventListener("click", function () {
      btn.closest(".flash").remove();
    });
  });

  // Mobile sidebar
  var menuBtn = document.getElementById("menuBtn");
  var sidebar = document.getElementById("sidebar");
  if (menuBtn && sidebar) {
    menuBtn.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });
  }

  // Forms: ask before risky actions (data-confirm="message"), then prevent double submits
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      var message = form.getAttribute("data-confirm");
      if (message && !window.confirm(message)) {
        e.preventDefault();
        return;
      }
      var btn = form.querySelector("button[type=submit]");
      if (btn) { setTimeout(function () { btn.disabled = true; }, 0); }
    });
  });
})();