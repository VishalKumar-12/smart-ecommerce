// Global site behaviour: auto-dismiss flash messages
document.addEventListener("DOMContentLoaded", function () {
  var flashes = document.querySelectorAll(".flash");
  flashes.forEach(function (el) {
    setTimeout(function () {
      el.style.transition = "opacity .4s ease";
      el.style.opacity = "0";
      setTimeout(function () { el.remove(); }, 400);
    }, 3500);
  });
});
