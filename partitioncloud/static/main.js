//* Add a listener to close pop-ups on Esc key pressed
document.addEventListener('keyup', function(e) {
    if (e.key == "Escape") {
        location.hash="!";
    }
});


//* Save sidebar toggling preference to localStorage
if (!("isSidebarToggled" in localStorage)) {
    localStorage["isSidebarToggled"] = window.innerWidth > 750; // Disable by default on mobile devices
}
document.getElementById("slide-sidebar").checked = !(JSON.parse(localStorage["isSidebarToggled"])); // localStorage cannot contain booleans

// Triggered on sidebar open/ close
function updateSidebarToggle () {
    localStorage["isSidebarToggled"] = !(document.getElementById("slide-sidebar").checked);
}
document.getElementById("slide-sidebar").addEventListener("change", updateSidebarToggle, false);
