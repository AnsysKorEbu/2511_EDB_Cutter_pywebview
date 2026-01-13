/**
 * Analysis GUI JavaScript
 *
 * Handles initialization, UI updates, and analysis operations
 * for the Touchstone generator GUI.
 */

// Global state management
let analysisState = {
    aedbFiles: [],
    analyzing: false,
    completed: 0,
    total: 0,
    results: []
};

/**
 * Initialize the Analysis GUI
 * Called when pywebview is ready
 */
window.addEventListener('pywebviewready', async function() {
    console.log('Analysis GUI ready');
    await init();
});

/**
 * Main initialization function
 * Loads AEDB file list and sets up UI
 */
async function init() {
    try {
        console.log('Loading AEDB file list...');

        // Load AEDB file list from backend
        const files = await window.pywebview.api.get_aedb_list();
        console.log(`Found ${files.length} .aedb files:`, files);

        analysisState.aedbFiles = files;
        analysisState.total = files.length;

        // Display results folder info
        if (files.length > 0) {
            // Extract parent folder from first file path
            const firstPath = files[0].path;
            const parentFolder = firstPath.substring(0, firstPath.lastIndexOf('\\'));
            document.getElementById('resultsFolder').textContent = parentFolder;
        } else {
            document.getElementById('resultsFolder').textContent = 'No files found';
        }

        document.getElementById('totalDesigns').textContent = files.length;

        // Render file list
        renderFileList(files);

    } catch (error) {
        console.error('Failed to initialize:', error);

        const fileList = document.getElementById('fileList');
        fileList.innerHTML = `
            <div class="empty-state">
                <p>Failed to load design files</p>
                <p>${error.message || error}</p>
            </div>
        `;
    }
}

/**
 * Render the list of .aedb files
 * @param {Array} files - Array of file objects
 */
function renderFileList(files) {
    const listContainer = document.getElementById('fileList');

    if (files.length === 0) {
        listContainer.innerHTML = `
            <div class="empty-state">
                <p>No .aedb files found</p>
                <p>Run the cutter first to generate design files</p>
            </div>
        `;

        // Disable Analyze All button
        document.getElementById('analyzeAllBtn').disabled = true;
        return;
    }

    // Generate HTML for each file
    listContainer.innerHTML = files.map(file => {
        // Format file size
        const sizeStr = formatFileSize(file.size || 0);

        return `
            <div class="file-list-item" data-aedb="${file.name}">
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-path">${file.path} (${sizeStr})</div>
                </div>
                <div class="file-actions">
                    <label class="analysis-toggle-switch">
                        <input type="checkbox" data-aedb="${file.name}" class="analysis-type-toggle">
                        <span class="toggle-background">
                            <span class="toggle-option toggle-siwave">SIWave</span>
                            <span class="toggle-option toggle-hfss">HFSS</span>
                        </span>
                    </label>
                    <span class="status-badge status-pending">Pending</span>
                    <button class="btn-analyze" onclick="analyzeSingle('${file.name}')">
                        Analyze
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Analyze a single .aedb file
 * @param {string} aedbName - Name of the .aedb folder
 */
async function analyzeSingle(aedbName) {
    const item = document.querySelector(`[data-aedb="${aedbName}"]`);
    if (!item) {
        console.error(`File list item not found for: ${aedbName}`);
        return;
    }

    const badge = item.querySelector('.status-badge');
    const button = item.querySelector('.btn-analyze');

    // Get analysis type from toggle switch (unchecked = siwave, checked = hfss)
    const toggle = item.querySelector('.analysis-type-toggle');
    const analysisType = toggle && toggle.checked ? 'hfss' : 'siwave';

    // Update UI to analyzing state
    badge.className = 'status-badge status-analyzing';
    badge.textContent = 'Analyzing...';
    button.disabled = true;

    console.log(`Starting ${analysisType.toUpperCase()} analysis for: ${aedbName}`);

    try {
        // Call backend to run analysis (will silently use SIWave if HFSS selected)
        const result = await window.pywebview.api.analyze_single(aedbName, analysisType);
        console.log('Analysis result:', result);

        if (result.success) {
            // Success: Update badge and add to results
            badge.className = 'status-badge status-completed';
            badge.textContent = 'Completed';
            button.textContent = 'Done';

            // Add to results list
            analysisState.results.push({
                name: aedbName,
                output: result.output_file,
                size: result.file_size || 0
            });

            // Update results section
            updateResultsSection();

        } else {
            // Error: Update badge with error state
            badge.className = 'status-badge status-error';
            badge.textContent = 'Failed';
            button.disabled = false;

            console.error(`Analysis failed for ${aedbName}:`, result.error);

            // You could show an error message in the UI here
            if (result.error) {
                badge.title = result.error;
            }
        }

    } catch (error) {
        // Exception: Update badge with error state
        badge.className = 'status-badge status-error';
        badge.textContent = 'Error';
        button.disabled = false;

        console.error('Analysis error:', error);
        badge.title = error.message || error;
    }
}

/**
 * Analyze all .aedb files sequentially
 */
async function analyzeAll() {
    if (analysisState.analyzing) {
        console.log('Analysis already in progress');
        return;
    }

    if (analysisState.aedbFiles.length === 0) {
        console.log('No files to analyze');
        return;
    }

    console.log(`Starting analysis for all ${analysisState.aedbFiles.length} files`);

    // Show progress section
    const progressSection = document.getElementById('progressSection');
    progressSection.classList.remove('hidden');

    // Update state
    analysisState.analyzing = true;
    analysisState.completed = 0;

    // Disable "Analyze All" button
    const analyzeAllBtn = document.getElementById('analyzeAllBtn');
    analyzeAllBtn.disabled = true;
    analyzeAllBtn.textContent = 'Analyzing...';

    // Loop through all files
    for (const file of analysisState.aedbFiles) {
        await analyzeSingle(file.name);

        // Update progress
        analysisState.completed++;
        updateProgress();
    }

    // Reset button and state
    analyzeAllBtn.disabled = false;
    analyzeAllBtn.textContent = 'Analyze All';
    analysisState.analyzing = false;

    console.log('All analyses complete');

    // Ask user if they want to generate circuit and run
    const shouldContinue = confirm('Analysis complete! Do you want to generate circuit and run?');
    if (shouldContinue) {
        console.log('User chose to generate circuit and run');
        await launchSchematicGui();
    }
}

/**
 * Launch Schematic GUI (Touchstone Generator)
 */
async function launchSchematicGui() {
    try {
        console.log('Launching Schematic GUI...');

        const result = await window.pywebview.api.launch_schematic_gui();

        if (result.success) {
            console.log('Schematic GUI launched successfully');
            alert('Schematic GUI (Touchstone Generator) has been launched!');
        } else {
            console.error('Failed to launch Schematic GUI:', result.error);
            alert(`Failed to launch Schematic GUI: ${result.error}`);
        }
    } catch (error) {
        console.error('Error launching Schematic GUI:', error);
        alert(`Error launching Schematic GUI: ${error.message || error}`);
    }
}

/**
 * Update the progress bar and text
 */
function updateProgress() {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    const percent = (analysisState.completed / analysisState.total) * 100;
    progressBar.style.width = `${percent}%`;
    progressText.textContent = `${analysisState.completed} / ${analysisState.total} completed`;
}

/**
 * Update the results section with generated touchstone files
 */
function updateResultsSection() {
    if (analysisState.results.length === 0) return;

    const resultsSection = document.getElementById('resultsSection');
    const resultsList = document.getElementById('resultsList');

    // Show results section
    resultsSection.classList.remove('hidden');

    // Generate HTML for results
    resultsList.innerHTML = analysisState.results.map(result => {
        const sizeStr = formatFileSize(result.size);

        return `
            <div class="result-item">
                <div class="result-name">${result.name} → ${extractFileName(result.output)}</div>
                <div class="result-output">${result.output} (${sizeStr})</div>
            </div>
        `;
    }).join('');
}

/**
 * Extract filename from full path
 * @param {string} path - Full file path
 * @returns {string} Filename only
 */
function extractFileName(path) {
    if (!path) return '';
    return path.split('\\').pop().split('/').pop();
}

/**
 * Format file size in human-readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted size string
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Browse and select a different Results folder
 * Opens a folder browser dialog and reloads the GUI with selected folder
 */
async function browseFolder() {
    try {
        console.log('Opening folder browser...');

        // Open folder browser dialog
        const result = await window.pywebview.api.browse_results_folder();

        if (!result.success) {
            console.log('Folder selection cancelled or failed:', result.error);
            return;
        }

        console.log('Selected folder:', result.folder);

        // Load new folder
        const loadResult = await window.pywebview.api.load_new_folder(result.folder);

        if (loadResult.success) {
            console.log(`Loaded ${loadResult.aedb_files.length} .aedb files from new folder`);

            // Update UI with new folder info
            const parentFolder = loadResult.folder;
            document.getElementById('resultsFolder').textContent = parentFolder;
            document.getElementById('totalDesigns').textContent = loadResult.aedb_files.length;

            // Update state
            analysisState.aedbFiles = loadResult.aedb_files;
            analysisState.total = loadResult.aedb_files.length;
            analysisState.completed = 0;
            analysisState.results = [];

            // Re-render file list
            renderFileList(loadResult.aedb_files);

            // Hide progress and results sections (reset state)
            document.getElementById('progressSection').classList.add('hidden');
            document.getElementById('resultsSection').classList.add('hidden');

        } else {
            console.error('Failed to load folder:', loadResult.error);
            alert(`Failed to load folder: ${loadResult.error}`);
        }

    } catch (error) {
        console.error('Browse folder error:', error);
        alert(`Error browsing folder: ${error.message || error}`);
    }
}
