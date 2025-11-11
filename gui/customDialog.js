/**
 * Custom Dialog System
 * Replaces native browser alert/confirm/prompt with themed modals
 */

// Dialog state
let dialogState = {
    resolveCallback: null,
    rejectCallback: null,
    type: null // 'alert', 'confirm', 'prompt'
};

/**
 * Custom Alert
 * @param {string} message - Message to display
 * @returns {Promise<void>}
 */
function customAlert(message) {
    return new Promise((resolve) => {
        dialogState.resolveCallback = resolve;
        dialogState.type = 'alert';

        const modal = document.getElementById('customDialog');
        const title = document.getElementById('dialogTitle');
        const messageEl = document.getElementById('dialogMessage');
        const input = document.getElementById('dialogInput');
        const cancelBtn = document.getElementById('dialogCancelBtn');
        const confirmBtn = document.getElementById('dialogConfirmBtn');

        // Setup dialog
        title.textContent = 'Notice';
        messageEl.textContent = message;
        input.classList.add('hidden');
        cancelBtn.classList.add('hidden');
        confirmBtn.textContent = 'OK';

        // Show modal
        modal.classList.remove('hidden');

        // Focus confirm button
        setTimeout(() => confirmBtn.focus(), 100);
    });
}

/**
 * Custom Confirm
 * @param {string} message - Message to display
 * @returns {Promise<boolean>} - true if confirmed, false if cancelled
 */
function customConfirm(message) {
    return new Promise((resolve) => {
        dialogState.resolveCallback = resolve;
        dialogState.type = 'confirm';

        const modal = document.getElementById('customDialog');
        const title = document.getElementById('dialogTitle');
        const messageEl = document.getElementById('dialogMessage');
        const input = document.getElementById('dialogInput');
        const cancelBtn = document.getElementById('dialogCancelBtn');
        const confirmBtn = document.getElementById('dialogConfirmBtn');

        // Setup dialog
        title.textContent = 'Confirm';
        messageEl.textContent = message;
        input.classList.add('hidden');
        cancelBtn.classList.remove('hidden');
        confirmBtn.textContent = 'OK';

        // Show modal
        modal.classList.remove('hidden');

        // Focus cancel button (safer default)
        setTimeout(() => cancelBtn.focus(), 100);
    });
}

/**
 * Custom Prompt
 * @param {string} message - Message to display
 * @param {string} defaultValue - Default input value
 * @returns {Promise<string|null>} - Input value if confirmed, null if cancelled
 */
function customPrompt(message, defaultValue = '') {
    return new Promise((resolve) => {
        dialogState.resolveCallback = resolve;
        dialogState.type = 'prompt';

        const modal = document.getElementById('customDialog');
        const title = document.getElementById('dialogTitle');
        const messageEl = document.getElementById('dialogMessage');
        const input = document.getElementById('dialogInput');
        const cancelBtn = document.getElementById('dialogCancelBtn');
        const confirmBtn = document.getElementById('dialogConfirmBtn');

        // Setup dialog
        title.textContent = 'Input';
        messageEl.textContent = message;
        input.classList.remove('hidden');
        input.value = defaultValue;
        cancelBtn.classList.remove('hidden');
        confirmBtn.textContent = 'OK';

        // Show modal
        modal.classList.remove('hidden');

        // Focus input and select text
        setTimeout(() => {
            input.focus();
            input.select();
        }, 100);

        // Handle Enter key in input
        input.onkeydown = (e) => {
            if (e.key === 'Enter') {
                confirmCustomDialog();
            } else if (e.key === 'Escape') {
                closeCustomDialog();
            }
        };
    });
}

/**
 * Confirm dialog action
 */
function confirmCustomDialog() {
    const modal = document.getElementById('customDialog');
    const input = document.getElementById('dialogInput');

    if (dialogState.type === 'alert') {
        dialogState.resolveCallback();
    } else if (dialogState.type === 'confirm') {
        dialogState.resolveCallback(true);
    } else if (dialogState.type === 'prompt') {
        dialogState.resolveCallback(input.value);
    }

    // Clean up
    modal.classList.add('hidden');
    input.onkeydown = null;
    dialogState.resolveCallback = null;
    dialogState.type = null;
}

/**
 * Close/Cancel dialog
 */
function closeCustomDialog() {
    const modal = document.getElementById('customDialog');
    const input = document.getElementById('dialogInput');

    if (dialogState.type === 'alert') {
        dialogState.resolveCallback();
    } else if (dialogState.type === 'confirm') {
        dialogState.resolveCallback(false);
    } else if (dialogState.type === 'prompt') {
        dialogState.resolveCallback(null);
    }

    // Clean up
    modal.classList.add('hidden');
    input.onkeydown = null;
    dialogState.resolveCallback = null;
    dialogState.type = null;
}

// Handle ESC key globally for dialog
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('customDialog');
        if (modal && !modal.classList.contains('hidden')) {
            closeCustomDialog();
        }
    }
});
