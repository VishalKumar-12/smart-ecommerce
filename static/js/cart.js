// Cart page helpers: quantity +/- buttons submit their parent form automatically
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-qty-change]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var input = btn.parentElement.querySelector("input[name='quantity']");
      var delta = parseInt(btn.getAttribute("data-qty-change"), 10);
      var newVal = Math.max(0, parseInt(input.value || "1", 10) + delta);
      input.value = newVal;
      btn.closest("form").submit();
    });
  });
});
