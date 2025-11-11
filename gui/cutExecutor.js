/**
 * Cut Executor Module
 *
 * Handles selecting and executing saved cut geometries on EDB.
 */

// Cut executor state
let cutExecutor = {
    selectedCutId: null,
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
            <div class="executor-cut-item ${cutExecutor.selectedCutId === cut.id ? 'selected' : ''}"
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
    cutExecutor.selectedCutId = null;
    cutExecutor.isExecuting = false;
}

/**
 * Select a cut for execution
 * @param {string} cutId - ID of the cut to select
 */
function selectCutForExecution(cutId) {
    cutExecutor.selectedCutId = cutId;

    // Update UI - remove selection from all items
    document.querySelectorAll('.executor-cut-item').forEach(item => {
        item.classList.remove('selected');
    });

    // Add selection to clicked item
    const selectedItem = document.querySelector(`.executor-cut-item[data-cut-id="${cutId}"]`);
    if (selectedItem) {
        selectedItem.classList.add('selected');
    }

    // Enable execute button
    const executeBtn = document.getElementById('executeCutBtn');
    executeBtn.disabled = false;
}

/**
 * Execute the selected cut
 * Calls backend to run EDB cutting operation
 */
async function executeSelectedCut() {
    if (!cutExecutor.selectedCutId) {
        alert('Please select a cut to execute');
        return;
    }

    if (cutExecutor.isExecuting) {
        return; // Prevent double execution
    }

    cutExecutor.isExecuting = true;

    // Update UI to show execution state
    const executeBtn = document.getElementById('executeCutBtn');
    const statusDiv = document.getElementById('executorStatus');
    const originalBtnText = executeBtn.textContent;

    executeBtn.disabled = true;
    executeBtn.textContent = 'Executing...';
    statusDiv.innerHTML = `
        <div class="status-info">
            <span class="status-spinner">⏳</span>
            <span>Opening EDB and executing cut ${cutExecutor.selectedCutId}...</span>
        </div>
    `;
    statusDiv.classList.remove('hidden');

    try {
        // Call backend API to execute cut
        const result = await window.pywebview.api.execute_cut(cutExecutor.selectedCutId);

        if (result.success) {
            // Show success message
            statusDiv.innerHTML = `
                <div class="status-success">
                    <span class="status-icon">✓</span>
                    <span>Cut executed successfully!</span>
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
        console.error('Failed to execute cut:', error);

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
