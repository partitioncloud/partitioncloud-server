let logsEmbed = document.getElementById("logs-embed");

logsEmbed.addEventListener("load", () => {
    var cssLink = document.createElement("link");

    cssLink.href = "/static/style/logs.css";
    cssLink.rel = "stylesheet";
    cssLink.type = "text/css";

    // add css
    logsEmbed.contentDocument.head.appendChild(cssLink);

    // Scroll to bottom
    logsEmbed.contentWindow.scrollTo(0, logsEmbed.contentDocument.body.scrollHeight);
});

// check if the iframe is already loaded (happened with FF Android)
if (logsEmbed.contentDocument.readyState == "complete") {
    logsEmbed.dispatchEvent(new Event("load"));
}