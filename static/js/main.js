document.addEventListener("DOMContentLoaded", function () {

    var flashes = document.querySelectorAll(".flash");

    flashes.forEach(function (el) {

        // Auto hide after 3.5 seconds
        setTimeout(function () {

            el.style.transition =
                "opacity .4s ease, transform .4s ease";

            el.style.opacity = "0";
            el.style.transform = "translateX(40px)";

            setTimeout(function () {
                el.remove();
            }, 400);

        }, 3500);

    });

});

// // Global site behaviour: auto-dismiss flash messages
// document.addEventListener("DOMContentLoaded", function () {
//   var flashes = document.querySelectorAll(".flash");
//   flashes.forEach(function (el) {
//     setTimeout(function () {
//       el.style.transition = "opacity .4s ease";
//       el.style.opacity = "0";
//       setTimeout(function () { el.remove(); }, 400);
//     }, 3500);
//   });
// });
