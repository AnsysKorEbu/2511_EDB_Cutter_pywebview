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

    // Clear previous selection when opening modal
    cutExecutor.selectedCutIds = [];
    cutExecutor.isExecuting = false;

    // Show modal
    modal.classList.remove('hidden');

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
            return;
        }

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

        // Call backend API to execute cuts with selected nets
        const result = await window.pywebview.api.execute_cuts(cutIds, selectedNets);

        if (result.success) {
            // Show success message
            const successMsg = count === 1 ? 'Cut executed successfully!' : `${count} cuts executed successfully!`;
            statusDiv.innerHTML = `
                <div class="status-success">
                    <span class="status-icon">✓</span>
                    <span>${successMsg}</span>
                </div>
            `;

            // Close modal after delay
            setTimeout(() => {
                closeCutExecutor();
            }, 2000);

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
