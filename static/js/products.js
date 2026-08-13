
// Products listing page: live client-side filtering by category chips
document.addEventListener("DOMContentLoaded", function () {
  var chips = document.querySelectorAll("[data-category-chip]");
  chips.forEach(function (chip) {
    chip.addEventListener("click", function (e) {
      e.preventDefault();
      window.location.href = chip.getAttribute("href");
    });
  });

  var searchForm = document.querySelector("#search-form");
  if (searchForm) {
    searchForm.addEventListener("submit", function (e) {
      var input = searchForm.querySelector("input[name='q']");
      if (!input.value.trim()) e.preventDefault();
    });
  }
});

