/**
 * Main application initialization for pywebview
 */

let renderer;
let uiController;
let polygonSelector;

// Wait for pywebview to be ready
window.addEventListener('pywebviewready', () => {
    console.log('pywebview ready, initializing application...');
    initializeApp();
});

// Fallback: if pywebviewready doesn't fire, wait for DOMContentLoaded + delay
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM ready');

    // Check if pywebview is already available
    if (typeof pywebview !== 'undefined' && typeof pywebview.api !== 'undefined') {
        console.log('pywebview already available, initializing...');
        initializeApp();
    } else {
        // Wait a bit longer for pywebview to be ready
        console.log('Waiting for pywebview...');
        let attempts = 0;
        const checkInterval = setInterval(() => {
            attempts++;
            if (typeof pywebview !== 'undefined' && typeof pywebview.api !== 'undefined') {
                console.log('pywebview now available, initializing...');
                clearInterval(checkInterval);
                initializeApp();
            } else if (attempts > 50) {
                console.error('pywebview not available after 5 seconds');
                clearInterval(checkInterval);
                alert('Failed to initialize pywebview API');
            }
        }, 100);
    }
});

async function initializeApp() {
    try {
        console.log('Initializing EDB Cutter...');

        // Create renderer
        renderer = new EDBRenderer('canvas-container');
        console.log('Renderer created');

        // Create UI controller
        uiController = new UIController(renderer);
        console.log('UI controller created');

        // Create polygon selector
        polygonSelector = new PolygonSelector(renderer, uiController);
        console.log('Polygon selector created');

        // Make globally accessible
        window.polygonSelector = polygonSelector;

        // Setup button handlers
        setupButtonHandlers();

        // Load EDB data
        console.log('Loading EDB data...');
        await renderer.loadData();
        console.log('Application initialized successfully');

        uiController.showMessage('EDB 로드 완료', 'success');
    } catch (error) {
        console.error('Error initializing application:', error);
        alert('애플리케이션 초기화 오류: ' + error.message);
    }
}

function setupButtonHandlers() {
    // Select mode button
    const btnSelectMode = document.getElementById('btn-select-mode');
    if (btnSelectMode) {
        btnSelectMode.onclick = () => {
            polygonSelector.startDrawing();
        };
    }

    // Clear button
    const btnClear = document.getElementById('btn-clear');
    if (btnClear) {
        btnClear.onclick = () => {
            polygonSelector.cancelDrawing();
            uiController.disableCutButton();
        };
    }

    // Fit view button
    const btnFit = document.getElementById('btn-fit');
    if (btnFit) {
        btnFit.onclick = () => {
            renderer.fitToView();
        };
    }

    // Cut button
    const btnCut = document.getElementById('btn-cut');
    if (btnCut) {
        btnCut.onclick = async () => {
            await polygonSelector.executeCut();
        };
    }
}
