document.addEventListener('DOMContentLoaded', function() {
    function enterFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.log(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
            });
        }
    }

    // Request full-screen mode when the page loads
    enterFullscreen();

    // Optionally, you can add a listener to request full-screen mode again if the user exits full-screen mode
    document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement) {
            enterFullscreen();
        }
    });
});
