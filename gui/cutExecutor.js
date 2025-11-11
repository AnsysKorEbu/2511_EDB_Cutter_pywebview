/**
 * Cut Executor Module
 *
 * Handles selecting and executing saved cut geometries on EDB.
 */

// Cut executor state
let cutExecutor = {
    selectedCutIds: new Set(),
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
            <div class="executor-cut-item ${cutExecutor.selectedCutIds.has(cut.id) ? 'selected' : ''}"
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
    cutExecutor.selectedCutIds.clear();
    cutExecutor.isExecuting = false;
}

/**
 * Select a cut for execution (toggle mode - allows multiple selection)
 * @param {string} cutId - ID of the cut to select/deselect
 */
function selectCutForExecution(cutId) {
    // Toggle selection
    if (cutExecutor.selectedCutIds.has(cutId)) {
        cutExecutor.selectedCutIds.delete(cutId);
    } else {
        cutExecutor.selectedCutIds.add(cutId);
    }

    // Update UI
    const selectedItem = document.querySelector(`.executor-cut-item[data-cut-id="${cutId}"]`);
    if (selectedItem) {
        if (cutExecutor.selectedCutIds.has(cutId)) {
            selectedItem.classList.add('selected');
        } else {
            selectedItem.classList.remove('selected');
        }
    }

    // Update execute button
    updateExecuteButton();
}

/**
 * Update execute button state and text based on selection
 */
function updateExecuteButton() {
    const executeBtn = document.getElementById('executeCutBtn');
    const count = cutExecutor.selectedCutIds.size;

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
 * Execute the selected cuts
 * Calls backend to run EDB cutting operation(s)
 */
async function executeSelectedCut() {
    if (cutExecutor.selectedCutIds.size === 0) {
        alert('Please select at least one cut to execute');
        return;
    }

    if (cutExecutor.isExecuting) {
        return; // Prevent double execution
    }

    cutExecutor.isExecuting = true;

    // Convert Set to Array
    const cutIds = Array.from(cutExecutor.selectedCutIds);
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
        // Call backend API to execute cuts
        const result = await window.pywebview.api.execute_cuts(cutIds);

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
