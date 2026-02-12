/**
 * Cut Executor Module
 *
 * Handles selecting and executing saved cut geometries on EDB.
 */

// Cut executor state
let cutExecutor = {
    selectedCutIds: [],  // Changed from Set to Array to preserve selection order
    isExecuting: false
};

/**
 * Open cut executor modal
 * Loads and displays the list of saved cuts for execution
 */
async function openCutExecutor() {
    const modal = document.getElementById('cutExecutorModal');
    const cutListContainer = document.getElementById('executorCutList');

    // Show modal
    modal.classList.remove('hidden');

    // Auto-load latest SSS file
    try {
        const sssResult = await window.pywebview.api.get_latest_sss_file();
        const sssPathElement = document.getElementById('sssFilePath');

        if (sssResult.success && sssResult.sss_file) {
            const filename = sssResult.sss_file.split(/[/\\]/).pop();
            sssPathElement.textContent = filename;
            sssPathElement.title = sssResult.sss_file;
        } else {
            sssPathElement.textContent = 'No file selected';
            sssPathElement.title = '';
        }
    } catch (error) {
        console.error('Failed to load latest SSS file:', error);
    }

    // Load cut list
    try {
        const cuts = await window.pywebview.api.get_cut_list();

        if (cuts.length === 0) {
            cutListContainer.innerHTML = `
                <div class="empty-state">
                    <p>No cuts available</p>
                    <p class="empty-hint">Create cuts using Cut Mode first</p>
                </div>
            `;
            // Clear selection only when there are no cuts
            cutExecutor.selectedCutIds = [];
            cutExecutor.isExecuting = false;
            return;
        }

        // Auto-select all cuts in order when opening modal
        cutExecutor.selectedCutIds = cuts.map(cut => cut.id);
        cutExecutor.isExecuting = false;

        // Generate cut list HTML
        cutListContainer.innerHTML = cuts.map(cut => `
            <div class="executor-cut-item"
                 data-cut-id="${cut.id}"
                 onclick="selectCutForExecution('${cut.id}')">
                <div class="executor-cut-header">
                    <span class="executor-cut-id">${cut.id}</span>
                    <span class="executor-cut-type">${cut.type}</span>
                </div>
                <div class="executor-cut-info">
                    <span class="executor-cut-points">${cut.point_count || 0} points</span>
                    <span class="executor-cut-timestamp">${formatTimestamp(cut.timestamp)}</span>
                </div>
            </div>
        `).join('');

        // Update UI to show all cuts are selected
        updateCutOrderDisplay();

        // Update execute button state
        updateExecuteButton();

    } catch (error) {
        console.error('Failed to load cut list:', error);
        cutListContainer.innerHTML = `
            <div class="error-state">
                <p>Failed to load cuts</p>
                <p class="error-hint">${error.message || error}</p>
            </div>
        `;
    }
}

/**
 * Close cut executor modal
 */
function closeCutExecutor() {
    const modal = document.getElementById('cutExecutorModal');
    modal.classList.add('hidden');
    cutExecutor.selectedCutIds = [];
    cutExecutor.isExecuting = false;
}

/**
 * Select a cut for execution (toggle mode - allows multiple selection with order tracking)
 * @param {string} cutId - ID of the cut to select/deselect
 */
function selectCutForExecution(cutId) {
    const index = cutExecutor.selectedCutIds.indexOf(cutId);

    // Toggle selection
    if (index !== -1) {
        // Deselect: remove from array
        cutExecutor.selectedCutIds.splice(index, 1);
    } else {
        // Select: add to end of array
        cutExecutor.selectedCutIds.push(cutId);
    }

    // Update all cut items UI (for selection state and order badges)
    updateCutOrderDisplay();

    // Update execute button
    updateExecuteButton();
}

/**
 * Update execute button state and text based on selection
 */
function updateExecuteButton() {
    const executeBtn = document.getElementById('executeCutBtn');
    const count = cutExecutor.selectedCutIds.length;

    if (count === 0) {
        executeBtn.disabled = true;
        executeBtn.textContent = 'Execute';
    } else if (count === 1) {
        executeBtn.disabled = false;
        executeBtn.textContent = 'Execute (1 cut)';
    } else {
        executeBtn.disabled = false;
        executeBtn.textContent = `Execute (${count} cuts)`;
    }
}

/**
 * Update cut order display with selection state and order badges
 */
function updateCutOrderDisplay() {
    // Get all cut items
    const cutItems = document.querySelectorAll('.executor-cut-item');

    cutItems.forEach(item => {
        const cutId = item.getAttribute('data-cut-id');
        const index = cutExecutor.selectedCutIds.indexOf(cutId);

        // Remove existing badge if any
        const existingBadge = item.querySelector('.executor-cut-order-badge');
        if (existingBadge) {
            existingBadge.remove();
        }

        if (index !== -1) {
            // Selected: add selected class and order badge
            item.classList.add('selected');

            // Create order badge
            const orderBadge = document.createElement('div');
            orderBadge.className = 'executor-cut-order-badge';
            orderBadge.textContent = index + 1; // 1-based numbering
            item.appendChild(orderBadge);
        } else {
            // Not selected: remove selected class
            item.classList.remove('selected');
        }
    });
}

/**
 * Execute the selected cuts in the order they were selected
 * Calls backend to run EDB cutting operation(s)
 */
async function executeSelectedCut() {
    if (cutExecutor.selectedCutIds.length === 0) {
        await customAlert('Please select at least one cut to execute');
        return;
    }

    if (cutExecutor.isExecuting) {
        return; // Prevent double execution
    }

    cutExecutor.isExecuting = true;

    // Use the array directly (already in selection order)
    const cutIds = cutExecutor.selectedCutIds;
    const count = cutIds.length;

    // Update UI to show execution state
    const executeBtn = document.getElementById('executeCutBtn');
    const statusDiv = document.getElementById('executorStatus');
    const originalBtnText = executeBtn.textContent;

    executeBtn.disabled = true;
    executeBtn.textContent = 'Executing...';

    const cutIdsText = count === 1 ? cutIds[0] : `${count} cuts`;
    statusDiv.innerHTML = `
        <div class="status-info">
            <span class="status-spinner">⏳</span>
            <span>Opening EDB and executing ${cutIdsText}...</span>
        </div>
    `;
    statusDiv.classList.remove('hidden');

    try {
        // Collect selected nets from netsManager
        let selectedNets = { signal: [], power: [] };
        if (window.netsManager) {
            selectedNets = window.netsManager.getSelectedNetsByType();
            console.log('[DEBUG] Selected nets from GUI:', selectedNets);
            console.log('[DEBUG] Signal nets count:', selectedNets.signal.length);
            console.log('[DEBUG] Power nets count:', selectedNets.power.length);
            console.log('[DEBUG] Reference layer:', selectedNets.reference_layer);
        } else {
            console.log('[DEBUG] netsManager not found');
        }

        // Validate reference layer selection (required)
        if (!selectedNets.reference_layer) {
            statusDiv.innerHTML = `
                <div class="status-error">
                    <span class="status-icon">⚠</span>
                    <span>Please select a Reference Layer for Gap Ports in the Nets tab</span>
                </div>
            `;
            statusDiv.classList.remove('hidden');
            executeBtn.disabled = false;
            executeBtn.textContent = originalBtnText;
            cutExecutor.isExecuting = false;
            return;
        }

        // Check if SSS file is selected (user may have cleared it with X button)
        const sssPathElement = document.getElementById('sssFilePath');
        const sssSelected = sssPathElement && sssPathElement.textContent !== 'No file selected';

        // Call backend API to execute cuts with selected nets and SSS flag
        const result = await window.pywebview.api.execute_cuts(cutIds, selectedNets, sssSelected);

        if (result.success) {
            // Show success message
            const successMsg = count === 1 ? 'Cut executed successfully!' : `${count} cuts executed successfully!`;
            statusDiv.innerHTML = `
                <div class="status-success">
                    <span class="status-icon">✓</span>
                    <span>${successMsg}</span>
                </div>
            `;

            // Store results folder for stackup extractor processing
            if (result.results_folder) {
                sectionSelector.resultsFolder = result.results_folder;
            }

            // Prompt to open analysis GUI if results folder is available
            if (result.results_folder) {
                setTimeout(async () => {
                    const openAnalysis = await customConfirm('Cutting complete! Open Analysis GUI to generate Touchstone files?');
                    if (openAnalysis) {
                        await window.pywebview.api.launch_analysis_gui_window(result.results_folder);
                    }
                    closeCutExecutor();
                }, 1500);
            } else {
                // Close modal after delay if no results folder
                setTimeout(() => {
                    closeCutExecutor();
                }, 2000);
            }

        } else {
            // Show error message
            statusDiv.innerHTML = `
                <div class="status-error">
                    <span class="status-icon">✗</span>
                    <span>Execution failed: ${result.error || 'Unknown error'}</span>
                </div>
            `;
            executeBtn.disabled = false;
            executeBtn.textContent = originalBtnText;
            cutExecutor.isExecuting = false;
        }

    } catch (error) {
        console.error('Failed to execute cuts:', error);

        // Show error message
        statusDiv.innerHTML = `
            <div class="status-error">
                <span class="status-icon">✗</span>
                <span>Execution failed: ${error.message || error}</span>
            </div>
        `;

        executeBtn.disabled = false;
        executeBtn.textContent = originalBtnText;
        cutExecutor.isExecuting = false;
    }
}

/**
 * Format timestamp for display
 * @param {string} timestamp - ISO timestamp string
 * @returns {string} Formatted timestamp
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';

    try {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;

        return date.toLocaleDateString();
    } catch (e) {
        return timestamp;
    }
}

/**
 * Process stackup data from Excel file
 * Extracts layer materials, heights, and Dk/Df values
 */
async function processStackup() {
    const processBtn = document.getElementById('processStackupBtn');
    const statusDiv = document.getElementById('stackupStatus');
    const originalBtnText = processBtn.innerHTML;

    // Disable button and show processing state
    processBtn.disabled = true;
    processBtn.innerHTML = '<span>⏳ Processing...</span>';

    statusDiv.innerHTML = `
        <div class="status-info">
            <span class="status-spinner">⏳</span>
            <span>Processing stackup data from Excel file...</span>
        </div>
    `;
    statusDiv.classList.remove('hidden');

    try {
        // Call backend API to process stackup
        const result = await window.pywebview.api.process_stackup();

        if (result.success) {
            // Show success message with summary
            const summary = result.summary;
            statusDiv.innerHTML = `
                <div class="status-success">
                    <span class="status-icon">✓</span>
                    <div>
                        <div><strong>Stackup processed successfully!</strong></div>
                        <div style="margin-top: 8px; font-size: 0.9em;">
                            <div>• Total layers: ${summary.total_layers}</div>
                            <div>• Total height: ${summary.total_height}μm</div>
                            <div>• Materials: ${summary.materials.length} types</div>
                            <div style="margin-top: 4px; color: #666;">
                                ${summary.materials.join(', ')}
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Re-enable button after delay
            setTimeout(() => {
                processBtn.disabled = false;
                processBtn.innerHTML = originalBtnText;
            }, 2000);

        } else {
            // Show error message
            statusDiv.innerHTML = `
                <div class="status-error">
                    <span class="status-icon">✗</span>
                    <span>Processing failed: ${result.error || 'Unknown error'}</span>
                </div>
            `;
            processBtn.disabled = false;
            processBtn.innerHTML = originalBtnText;
        }

    } catch (error) {
        console.error('Failed to process stackup:', error);

        // Show error message
        statusDiv.innerHTML = `
            <div class="status-error">
                <span class="status-icon">✗</span>
                <span>Processing failed: ${error.message || error}</span>
            </div>
        `;

        processBtn.disabled = false;
        processBtn.innerHTML = originalBtnText;
    }
}
