//* 1st fix: Add a listener to close pop-ups on Esc key pressed */
document.addEventListener('keyup', function(e) {
    if (e.key == "Escape") {
        location.hash="!";
    }
});



//* 2nd fix: Save sidebar toggling preference to localStorage */
const sidebar_toggle = document.getElementById("slide-sidebar");

async function hideSidebarNoAnim () {
  const content_container = document.getElementById("content-container");
  const sidebar_indicator = sidebar_toggle.labels[0];

  /* The transition needs to be invisible as if it was loaded that way */
  content_container.style.transitionDuration = "0s";
  sidebar_indicator.style.transitionDuration = "0s";
  
  sidebar_toggle.checked = true;

  /* We need to set a sleep because we want to reset the transition duration only once it ended*/
  await new Promise(r => setTimeout(r, 10));

  content_container.style.transitionDuration = "";
  sidebar_indicator.style.transitionDuration = "";
}


//* Save sidebar toggling preference to localStorage
let isMobile = window.innerWidth <= 750;

if (!("isSidebarToggled" in localStorage)) {
    localStorage["isSidebarToggled"] = !isMobile; // Disable by default on mobile devices
}

if (JSON.parse(localStorage["isSidebarToggled"]) && !isMobile) {
  sidebar_toggle.checked = false; // hidden sidebar
} else if (!isMobile) {
  hideSidebarNoAnim(); // hide on desktop (no animation)
} else {
  sidebar_toggle.checked = true; // hide on mobile (animation)
}

//* Triggered localStorage save on open/ close
function updateSidebarToggle () {
    localStorage["isSidebarToggled"] = !(sidebar_toggle.checked);
}
sidebar_toggle.addEventListener("change", updateSidebarToggle, false);
