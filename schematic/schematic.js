/**
 * Schematic GUI JavaScript - Full Touchstone Generator
 *
 * Handles file list display, drag-drop reordering, flip toggles,
 * enable/disable checkboxes, and configuration generation.
 */

// Global state management
let schematicState = {
    files: [],              // Array of file objects
    analysisFolder: null,
    selectedFilenames: []   // Array to track selection order (for order numbering)
};

/**
 * Initialize GUI when pywebview is ready
 */
window.addEventListener('pywebviewready', async function() {
    console.log('Schematic GUI ready');
    await init();
});

/**
 * Main initialization function
 */
async function init() {
    try {
        console.log('Loading touchstone files...');

        // Get initial file list from backend
        const files = await window.pywebview.api.get_touchstone_files();
        console.log(`Found ${files.length} touchstone files:`, files);

        if (files.length > 0) {
            // Initialize state with all files
            // First file should have flip=true by default (c_ -> 0_ direction)
            schematicState.files = files.map((file, index) => ({
                filename: file.name,
                path: file.path,
                size: file.size,
                order: index + 1,
                flip: index === 0  // First file has flip=true by default
            }));

            // Auto-select all files in order
            schematicState.selectedFilenames = schematicState.files.map(f => f.filename);

            // Display folder info
            const firstPath = files[0].path;
            const parentFolder = firstPath.substring(0, firstPath.lastIndexOf('\\'));
            schematicState.analysisFolder = parentFolder;
            document.getElementById('analysisFolder').textContent = parentFolder;
        } else {
            schematicState.files = [];
            schematicState.selectedFilenames = [];
            document.getElementById('analysisFolder').textContent = 'No files found';
        }

        updateUI();

    } catch (error) {
        console.error('Failed to initialize:', error);
        showError(`Failed to load files: ${error.message || error}`);
    }
}

/**
 * Browse for Analysis folder
 */
async function browseFolder() {
    try {
        console.log('Opening folder browser...');

        const result = await window.pywebview.api.browse_analysis_folder();

        if (!result.success) {
            console.log('Folder selection cancelled:', result.error);
            return;
        }

        console.log('Selected folder:', result.folder);

        // Load files from new folder
        const loadResult = await window.pywebview.api.load_analysis_folder(result.folder);

        if (loadResult.success) {
            console.log(`Loaded ${loadResult.files.length} files`);

            // Update state with new files
            // First file should have flip=true by default (c_ -> 0_ direction)
            schematicState.files = loadResult.files.map((file, index) => ({
                filename: file.name,
                path: file.path,
                size: file.size,
                order: index + 1,
                flip: index === 0  // First file has flip=true by default
            }));

            // Auto-select all files in order
            schematicState.selectedFilenames = schematicState.files.map(f => f.filename);

            schematicState.analysisFolder = loadResult.folder;
            document.getElementById('analysisFolder').textContent = loadResult.folder;

            updateUI();

        } else {
            showError(`Failed to load folder: ${loadResult.error}`);
        }

    } catch (error) {
        console.error('Browse folder error:', error);
        showError(`Error browsing folder: ${error.message || error}`);
    }
}

/**
 * Update UI with current state
 */
function updateUI() {
    renderFileList();
    updateCounts();
    updateGenerateButton();
}

/**
 * Render file list with current state
 */
function renderFileList() {
    const listContainer = document.getElementById('fileList');

    if (schematicState.files.length === 0) {
        listContainer.innerHTML = `
            <div class="empty-state">
                <p>No files loaded</p>
                <p class="empty-hint">Click "Browse Folder" to select an Analysis folder</p>
            </div>
        `;
        return;
    }

    // Generate HTML for each file
    listContainer.innerHTML = schematicState.files.map((file, index) => {
        const sizeStr = formatFileSize(file.size || 0);

        return `
            <div class="file-list-item"
                 data-filename="${file.filename}"
                 onclick="selectFile('${file.filename}')">
                <div class="file-info">
                    <div class="file-name">${file.filename}</div>
                    <div class="file-size">${sizeStr}</div>
                </div>
                <div class="file-controls">
                    <label class="flip-toggle" title="Flip touchstone orientation" onclick="event.stopPropagation()">
                        <input type="checkbox"
                               ${file.flip ? 'checked' : ''}
                               onchange="toggleFlip('${file.filename}')">
                        <span class="toggle-label">Flip</span>
                    </label>
                </div>
            </div>
        `;
    }).join('');

    // Update order display after rendering
    updateFileOrderDisplay();
}

/**
 * Select a file for ordering (toggle mode - click to select/deselect)
 * @param {string} filename - Filename to select/deselect
 */
function selectFile(filename) {
    const index = schematicState.selectedFilenames.indexOf(filename);

    // Toggle selection
    if (index !== -1) {
        // Deselect: remove from array
        schematicState.selectedFilenames.splice(index, 1);
    } else {
        // Select: add to end of array
        schematicState.selectedFilenames.push(filename);
    }

    // Update UI
    updateFileOrderDisplay();
    updateGenerateButton();
}

/**
 * Update file order display with selection state and order badges
 */
function updateFileOrderDisplay() {
    // Get all file items
    const fileItems = document.querySelectorAll('.file-list-item');

    fileItems.forEach(item => {
        const filename = item.getAttribute('data-filename');
        const selectedIndex = schematicState.selectedFilenames.indexOf(filename);

        // Remove existing order badge
        const existingBadge = item.querySelector('.file-order-badge');
        if (existingBadge) {
            existingBadge.remove();
        }

        // Add/update selected state
        if (selectedIndex !== -1) {
            item.classList.add('selected');

            // Add order badge
            const orderBadge = document.createElement('div');
            orderBadge.className = 'file-order-badge';
            orderBadge.textContent = selectedIndex + 1;
            item.insertBefore(orderBadge, item.firstChild);
        } else {
            item.classList.remove('selected');
        }
    });
}

/**
 * Toggle flip state for a file
 */
function toggleFlip(filename) {
    const file = schematicState.files.find(f => f.filename === filename);
    if (file) {
        file.flip = !file.flip;
        console.log(`Toggled flip for ${filename}: ${file.flip}`);
    }
}

/**
 * Toggle all files selection
 */
function toggleAllSelected() {
    const allSelected = schematicState.selectedFilenames.length === schematicState.files.length;

    if (allSelected) {
        // Deselect all
        schematicState.selectedFilenames = [];
    } else {
        // Select all
        schematicState.selectedFilenames = schematicState.files.map(f => f.filename);
    }

    updateFileOrderDisplay();
    updateGenerateButton();
}

/**
 * Update file counts in UI
 */
function updateCounts() {
    const total = schematicState.files.length;
    const selected = schematicState.selectedFilenames.length;

    document.getElementById('totalFiles').textContent = total;
    document.getElementById('selectedCount').textContent = selected;
}

/**
 * Update generate button state
 */
function updateGenerateButton() {
    const generateBtn = document.getElementById('generateBtn');
    const selectedCount = schematicState.selectedFilenames.length;

    if (selectedCount === 0) {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generate Circuit';
    } else {
        generateBtn.disabled = false;
        generateBtn.textContent = `Generate Circuit (${selectedCount} files)`;
    }
}

/**
 * Generate configuration JSON file and run HFSS Circuit automatically
 */
async function generateConfiguration() {
    if (schematicState.selectedFilenames.length === 0) {
        showError('No files selected. Please select files by clicking on them.');
        return;
    }

    try {
        // Build config items in selection order
        const configItems = schematicState.selectedFilenames.map((filename, index) => {
            const file = schematicState.files.find(f => f.filename === filename);
            if (!file) return null;

            return {
                filename: file.filename,
                path: file.path,
                size: file.size,
                order: index + 1,  // Order based on selection sequence
                flip: file.flip,
                enabled: true  // All selected files are enabled
            };
        }).filter(item => item !== null);

        console.log('Generating configuration and HFSS Circuit with files:', configItems);

        // Show initial progress
        const statusSection = document.getElementById('statusSection');
        const statusMessage = document.getElementById('statusMessage');
        statusMessage.innerHTML = `
            <div class="status-info">
                <span class="status-icon">⏳</span>
                <span>Saving configuration...</span>
            </div>
        `;
        statusSection.classList.remove('hidden');

        // Step 1: Save configuration
        const configResult = await window.pywebview.api.save_merge_configuration(configItems);

        if (!configResult.success) {
            showError(`Failed to save configuration: ${configResult.error}`);
            return;
        }

        console.log('Configuration saved:', configResult.config_file);

        // Step 2: Automatically run HFSS Circuit generation
        console.log('Starting HFSS Circuit generation...');
        await runHfssCircuitGeneration();

    } catch (error) {
        console.error('Generate configuration error:', error);
        showError(`Error generating configuration: ${error.message || error}`);
    }
}

/**
 * Run HFSS Circuit generation directly (no separate GUI)
 */
async function runHfssCircuitGeneration() {
    try {
        console.log('Running HFSS Circuit generation...');

        // Update UI to show progress
        const statusSection = document.getElementById('statusSection');
        const statusMessage = document.getElementById('statusMessage');
        statusMessage.innerHTML = `
            <div class="status-info">
                <span class="status-icon">⏳</span>
                <span>Generating HFSS Circuit project...</span>
            </div>
        `;
        statusSection.classList.remove('hidden');

        // Call API to create HFSS Circuit
        const result = await window.pywebview.api.create_hfss_circuit();

        if (result.success) {
            console.log('HFSS Circuit created successfully:', result.aedt_file);

            // Show brief success message
            showSuccess(result.message || `HFSS Circuit project created successfully!\n\nFile: ${result.aedt_file}`);

            // Close window after 1 second
            setTimeout(() => {
                console.log('Closing Schematic GUI window...');
                window.pywebview.api.close_window();
            }, 1000);
        } else {
            console.error('Failed to create HFSS Circuit:', result.error);
            showError(`Failed to create HFSS Circuit:\n\n${result.error}`);
        }

    } catch (error) {
        console.error('Error during HFSS Circuit generation:', error);
        showError(`Error during HFSS Circuit generation:\n\n${error.message || error}`);
    }
}

/**
 * Show success message
 */
function showSuccess(message) {
    const statusSection = document.getElementById('statusSection');
    const statusMessage = document.getElementById('statusMessage');

    statusMessage.innerHTML = `
        <div class="status-success">
            <span class="status-icon">✓</span>
            <span>${message}</span>
        </div>
    `;
    statusSection.classList.remove('hidden');

    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusSection.classList.add('hidden');
    }, 5000);
}

/**
 * Show error message
 */
function showError(message) {
    const statusSection = document.getElementById('statusSection');
    const statusMessage = document.getElementById('statusMessage');

    statusMessage.innerHTML = `
        <div class="status-error">
            <span class="status-icon">✗</span>
            <span>${message}</span>
        </div>
    `;
    statusSection.classList.remove('hidden');
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
