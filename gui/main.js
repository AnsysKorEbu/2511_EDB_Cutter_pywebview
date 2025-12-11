// Reload data from Python API
async function reloadData() {
    const loading = document.getElementById('loading');
    const statusText = document.getElementById('statusText');
    const reloadBtn = document.getElementById('reloadBtn');

    loading.classList.remove('hidden');
    statusText.textContent = 'Loading data from source folder...';
    reloadBtn.disabled = true;

    try {
        if (!window.pywebview) {
            throw new Error('PyWebView API not available');
        }

        // Get planes data from Python
        const planesData = await window.pywebview.api.get_planes_data();

        if (planesData.length === 0) {
            throw new Error('No planes data found in source folder');
        }

        // Get vias data from Python
        viasData = await window.pywebview.api.get_vias_data();

        // Get traces data from Python
        tracesData = await window.pywebview.api.get_traces_data();

        loadData(planesData);
        statusText.textContent = `Loaded ${planesData.length} planes, ${viasData.length} vias, and ${tracesData.length} traces successfully`;
    } catch (error) {
        console.error('Error loading data:', error);
        statusText.textContent = 'Error: ' + error.message;
        await customAlert('Error loading data: ' + error.message);
    } finally {
        loading.classList.add('hidden');
        reloadBtn.disabled = false;
    }
}

// Mouse event handlers
canvas.addEventListener('mousedown', (e) => {
    // Ignore right-click (button 2)
    if (e.button === 2) {
        return;
    }

    // Shift + Drag = Pan mode (AEDT style) - works in both normal and cut mode
    if (e.shiftKey) {
        viewState.isDragging = true;
        viewState.lastX = e.clientX;
        viewState.lastY = e.clientY;
        canvas.style.cursor = 'grabbing';
        return;
    }

    if (cutMode.enabled && cutMode.panMode) {
        // Pan mode in cut mode
        viewState.isDragging = true;
        viewState.lastX = e.clientX;
        viewState.lastY = e.clientY;
    } else if (cutMode.enabled && cutMode.activeTool) {
        handleCutMouseDown(e);
    } else {
        // Clear highlight when clicking on blank canvas area
        if (typeof cutMode !== 'undefined' && cutMode.highlightedCutId !== null) {
            clearHighlight();
        }

        viewState.isDragging = true;
        viewState.lastX = e.clientX;
        viewState.lastY = e.clientY;
    }
});

canvas.addEventListener('mousemove', (e) => {
    // Update mouse position display
    const worldPos = screenToWorld(e.offsetX, e.offsetY);
    document.getElementById('mousePos').textContent =
        `X: ${worldPos.x.toFixed(6)}, Y: ${worldPos.y.toFixed(6)}`;

    // Handle dragging (check this FIRST before cut mode drawing)
    if (viewState.isDragging) {
        const dx = e.clientX - viewState.lastX;
        const dy = e.clientY - viewState.lastY;

        viewState.offsetX += dx;
        viewState.offsetY += dy;

        viewState.lastX = e.clientX;
        viewState.lastY = e.clientY;

        render();
    }
    // Handle cut mode drawing and snapping (active when tool is selected)
    else if (cutMode.enabled && cutMode.activeTool) {
        handleCutMouseMove(e);
    }

    // Update cursor based on mode
    if (!viewState.isDragging) {
        if (cutMode.enabled && cutMode.activeTool) {
            canvas.style.cursor = 'crosshair';
        } else if (e.shiftKey) {
            canvas.style.cursor = 'grab';
        } else if (!cutMode.enabled) {
            canvas.style.cursor = 'grab';
        }
    }
});

canvas.addEventListener('mouseup', (e) => {
    // Always stop dragging on mouse up
    if (viewState.isDragging) {
        viewState.isDragging = false;
        // Restore cursor after dragging
        if (cutMode.enabled) {
            canvas.style.cursor = 'crosshair';
        } else {
            canvas.style.cursor = 'grab';
        }
    }
});

canvas.addEventListener('mouseleave', () => {
    viewState.isDragging = false;
});

// Right-click handlers
canvas.addEventListener('contextmenu', (e) => {
    if (cutMode.enabled && cutMode.activeTool === 'line' && cutMode.isDrawing) {
        // Cancel line drawing
        e.preventDefault();
        cutMode.currentCut = [];
        cutMode.isDrawing = false;
        render();
        document.getElementById('statusText').textContent = 'Line drawing cancelled - Click to start new line';
    } else if (cutMode.enabled) {
        e.preventDefault(); // Prevent context menu in cut mode
    }
});

// Global keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl + D = Fit to View (Reset View)
    if (e.ctrlKey && e.key === 'd') {
        e.preventDefault();
        resetView();
        document.getElementById('statusText').textContent = 'View reset to fit all data';
        return;
    }

    // ESC key - works globally
    if (e.key === 'Escape') {
        // Clear highlight if any
        if (typeof cutMode !== 'undefined' && cutMode.highlightedCutId !== null) {
            clearHighlight();
            return;
        }

        // Cut mode specific: cancel current cut
        if (cutMode.enabled) {
            cutMode.currentCut = [];
            cutMode.isDrawing = false;
            document.getElementById('finishCutBtn').classList.add('hidden');
            render();
            document.getElementById('statusText').textContent = 'Cut cancelled';
        }
        return;
    }

    // Cut mode specific shortcuts
    if (!cutMode.enabled) return;

    if (e.key === ' ') {
        // Toggle pan mode with Space
        e.preventDefault();
        togglePanMode();
    }
});

// Zoom with mouse wheel
canvas.addEventListener('wheel', (e) => {
    e.preventDefault();

    const mouseX = e.offsetX;
    const mouseY = e.offsetY;

    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
    const oldScale = viewState.scale;
    viewState.scale *= zoomFactor;

    // Adjust offsets to keep mouse position fixed in world coordinates
    // X axis: standard calculation
    viewState.offsetX = mouseX - (mouseX - viewState.offsetX) * (viewState.scale / oldScale);
    // Y axis: inverted because Y coordinate system is flipped
    viewState.offsetY = mouseY + (viewState.offsetY - mouseY) * (viewState.scale / oldScale);

    updateZoomLabel();
    render();
});

// Tab switching functionality
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;

            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            const tabContent = document.getElementById(`${tabName}-tab`);
            if (tabContent) {
                tabContent.classList.add('active');
            }
        });
    });
}

// Initialize NetsManager
let netsManager = null;

async function initNetsManager() {
    try {
        netsManager = new NetsManager();
        // Expose to window for access from other modules (e.g., cutExecutor.js)
        window.netsManager = netsManager;
        await netsManager.loadNetsData();
        console.log('NetsManager initialized successfully');
    } catch (error) {
        console.error('Error initializing NetsManager:', error);
    }
}

/**
 * Open Analysis GUI
 * Opens a folder browser to select a Results folder and launches the Analysis GUI
 */
async function openAnalysisGui() {
    try {
        // Use tkinter folder browser to select Results folder
        const result = await window.pywebview.api.browse_results_folder_for_analysis();

        if (result && result.success && result.folder) {
            // Launch analysis GUI with selected folder
            await window.pywebview.api.launch_analysis_gui_window(result.folder);
        }
    } catch (error) {
        console.error('Failed to open Analysis GUI:', error);
        await customAlert('Failed to open Analysis GUI: ' + (error.message || error));
    }
}

/**
 * Open Schematic GUI (Full Touchstone Generator)
 */
async function openSchematicGui() {
    try {
        console.log('Launching Schematic GUI...');
        const result = await window.pywebview.api.launch_schematic_gui_window();

        if (!result.success) {
            console.error('Failed to launch Schematic GUI:', result.error);
            await customAlert(`Failed to launch Schematic GUI: ${result.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error launching Schematic GUI:', error);
        await customAlert(`Error: ${error.message || error}`);
    }
}


// Initialize when pywebview is ready
window.addEventListener('pywebviewready', function() {
    console.log('PyWebView ready!');
    resizeCanvas();

    // Initialize tabs
    initTabs();

    // Initialize NetsManager
    initNetsManager();

    // Auto-load data on startup
    setTimeout(reloadData, 500);
});

// Initialize canvas
resizeCanvas();
