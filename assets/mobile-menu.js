(function () {
  var button = document.querySelector(".menu-toggle");
  var nav = button && document.getElementById(button.getAttribute("aria-controls"));

  if (!button || !nav) {
    return;
  }

  document.body.classList.add("menu-ready");

  function setMenuOpen(isOpen) {
    button.setAttribute("aria-expanded", String(isOpen));
    nav.classList.toggle("is-open", isOpen);
  }

  button.addEventListener("click", function () {
    setMenuOpen(button.getAttribute("aria-expanded") !== "true");
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && button.getAttribute("aria-expanded") === "true") {
      setMenuOpen(false);
      button.focus();
    }
  });
})();
