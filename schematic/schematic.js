/**
 * Schematic GUI JavaScript - Full Touchstone Generator
 *
 * Handles file list display, drag-drop reordering, flip toggles,
 * enable/disable checkboxes, and configuration generation.
 */

// Global state management
let schematicState = {
    files: [],              // Array of file objects (for display order preservation)
    analysisFolder: null,
    draggedFilename: null   // Track dragged item filename
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
            // Initialize state with all files enabled by default
            schematicState.files = files.map((file, index) => ({
                filename: file.name,
                path: file.path,
                size: file.size,
                order: index + 1,
                flip: false,
                enabled: true
            }));

            // Display folder info
            const firstPath = files[0].path;
            const parentFolder = firstPath.substring(0, firstPath.lastIndexOf('\\'));
            schematicState.analysisFolder = parentFolder;
            document.getElementById('analysisFolder').textContent = parentFolder;
        } else {
            schematicState.files = [];
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
            schematicState.files = loadResult.files.map((file, index) => ({
                filename: file.name,
                path: file.path,
                size: file.size,
                order: index + 1,
                flip: false,
                enabled: true
            }));

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

    // Update order numbers based on files array position (enabled items only)
    let orderCounter = 1;
    schematicState.files.forEach(file => {
        if (file.enabled) {
            file.order = orderCounter++;
        }
    });

    // Separate enabled and disabled files, but keep their original array order
    const enabledFiles = schematicState.files.filter(f => f.enabled);
    const disabledFiles = schematicState.files.filter(f => !f.enabled);
    const displayFiles = [...enabledFiles, ...disabledFiles];

    // Generate HTML for each file
    listContainer.innerHTML = displayFiles.map((file, index) => {
        const sizeStr = formatFileSize(file.size || 0);
        const orderBadge = file.enabled ? `<div class="file-order-badge">${file.order}</div>` : '';
        const disabledClass = file.enabled ? '' : 'disabled';

        return `
            <div class="file-list-item ${disabledClass}"
                 data-filename="${file.filename}"
                 draggable="${file.enabled}"
                 ondragstart="handleDragStart(event, '${file.filename}')"
                 ondragend="handleDragEnd(event)">
                ${orderBadge}
                <div class="file-info">
                    <div class="file-name">${file.filename}</div>
                    <div class="file-size">${sizeStr}</div>
                </div>
                <div class="file-controls">
                    <label class="flip-toggle" title="Flip touchstone orientation">
                        <input type="checkbox"
                               ${file.flip ? 'checked' : ''}
                               onchange="toggleFlip('${file.filename}')"
                               ${!file.enabled ? 'disabled' : ''}>
                        <span class="toggle-label">Flip</span>
                    </label>
                    <label class="enable-checkbox" title="Include in merge">
                        <input type="checkbox"
                               ${file.enabled ? 'checked' : ''}
                               onchange="toggleEnabled('${file.filename}')">
                        <span class="checkbox-label">Enable</span>
                    </label>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Handle drag start event
 */
function handleDragStart(event, filename) {
    schematicState.draggedFilename = filename;
    event.dataTransfer.effectAllowed = 'move';
    event.target.classList.add('dragging');
}

/**
 * Handle drag end event
 */
function handleDragEnd(event) {
    event.target.classList.remove('dragging');
    schematicState.draggedFilename = null;
}

/**
 * Handle drag over event (required for drop to work)
 */
function handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';

    // Find the element being dragged over
    const draggingElement = document.querySelector('.dragging');
    if (!draggingElement) return;

    const afterElement = getDragAfterElement(event.clientY);
    const container = document.getElementById('fileList');

    if (afterElement == null) {
        container.appendChild(draggingElement);
    } else {
        container.insertBefore(draggingElement, afterElement);
    }
}

/**
 * Handle drop event
 */
function handleDrop(event) {
    event.preventDefault();

    if (!schematicState.draggedFilename) {
        return;
    }

    // Get drop target
    const targetElement = event.target.closest('.file-list-item');
    if (!targetElement) {
        return;
    }

    const targetFilename = targetElement.getAttribute('data-filename');

    if (targetFilename === schematicState.draggedFilename) {
        return;
    }

    // Find indices
    const draggedIndex = schematicState.files.findIndex(f => f.filename === schematicState.draggedFilename);
    const targetIndex = schematicState.files.findIndex(f => f.filename === targetFilename);

    if (draggedIndex === -1 || targetIndex === -1) {
        return;
    }

    // Reorder array
    const draggedItem = schematicState.files[draggedIndex];
    schematicState.files.splice(draggedIndex, 1);
    schematicState.files.splice(targetIndex, 0, draggedItem);

    // Re-render
    updateUI();
}

/**
 * Get element after current drag position
 */
function getDragAfterElement(y) {
    const draggableElements = [...document.querySelectorAll('.file-list-item:not(.dragging):not(.disabled)')];

    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;

        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
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
 * Toggle enabled state for a file
 */
function toggleEnabled(filename) {
    const file = schematicState.files.find(f => f.filename === filename);
    if (file) {
        file.enabled = !file.enabled;
        console.log(`Toggled enabled for ${filename}: ${file.enabled}`);
        updateUI();
    }
}

/**
 * Toggle all files enabled/disabled
 */
function toggleAllEnabled() {
    const allEnabled = schematicState.files.every(f => f.enabled);

    schematicState.files.forEach(file => {
        file.enabled = !allEnabled;
    });

    updateUI();
}

/**
 * Update file counts in UI
 */
function updateCounts() {
    const total = schematicState.files.length;
    const enabled = schematicState.files.filter(f => f.enabled).length;

    document.getElementById('totalFiles').textContent = total;
    document.getElementById('enabledCount').textContent = enabled;
}

/**
 * Update generate button state
 */
function updateGenerateButton() {
    const generateBtn = document.getElementById('generateBtn');
    const enabledCount = schematicState.files.filter(f => f.enabled).length;

    if (enabledCount === 0) {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generate Config';
    } else {
        generateBtn.disabled = false;
        generateBtn.textContent = `Generate Config (${enabledCount} files)`;
    }
}

/**
 * Generate configuration JSON file
 */
async function generateConfiguration() {
    const enabledFiles = schematicState.files.filter(f => f.enabled);

    if (enabledFiles.length === 0) {
        showError('No files enabled. Please enable at least one file.');
        return;
    }

    try {
        console.log('Generating configuration with files:', schematicState.files);

        const result = await window.pywebview.api.save_merge_configuration(schematicState.files);

        if (result.success) {
            showSuccess(`Configuration saved successfully!\nFile: ${result.config_file}\nEnabled files: ${result.total_enabled}`);
        } else {
            showError(`Failed to save configuration: ${result.error}`);
        }

    } catch (error) {
        console.error('Generate configuration error:', error);
        showError(`Error generating configuration: ${error.message || error}`);
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
