/**
 * Initial GUI - Settings Configuration
 */

// State management
const state = {
    edbPath: '',
    edbVersion: '',
    grpc: true,
    overwrite: false,
    versions: {},
    isValid: false
};

// Initialize on page load
window.addEventListener('pywebviewready', async function() {
    console.log('Initial GUI ready');
    await loadPreviousSettings();
    await loadAnsysVersions();
});

/**
 * Load previous settings from config
 */
async function loadPreviousSettings() {
    try {
        const previousSettings = await pywebview.api.load_previous_settings();

        if (previousSettings && Object.keys(previousSettings).length > 0) {
            console.log('Loading previous settings:', previousSettings);

            // Set state from previous settings
            if (previousSettings.edb_path) {
                state.edbPath = previousSettings.edb_path;
                document.getElementById('edbPath').value = previousSettings.edb_path;
            }

            if (previousSettings.edb_version) {
                state.edbVersion = previousSettings.edb_version;
            }

            if (previousSettings.grpc !== undefined) {
                state.grpc = previousSettings.grpc;
                document.getElementById('grpc').checked = previousSettings.grpc;
            }

            if (previousSettings.overwrite !== undefined) {
                state.overwrite = previousSettings.overwrite;
                document.getElementById('overwrite').checked = previousSettings.overwrite;
            }
        }
    } catch (error) {
        console.error('Error loading previous settings:', error);
    }
}

/**
 * Load available ANSYS versions from environment
 */
async function loadAnsysVersions() {
    try {
        showLoading('Detecting ANSYS versions...');

        const versions = await pywebview.api.get_ansys_versions();
        state.versions = versions;

        const versionSelect = document.getElementById('edbVersion');
        const versionHint = document.getElementById('versionHint');

        if (Object.keys(versions).length === 0) {
            versionSelect.innerHTML = '<option value="">No ANSYS versions detected</option>';
            versionHint.textContent = 'No ANSYSEM_ROOT environment variables found';
            versionHint.style.color = '#f48771';
        } else {
            // Populate dropdown
            versionSelect.innerHTML = '<option value="">Select a version...</option>';

            for (const [version, path] of Object.entries(versions)) {
                const option = document.createElement('option');
                option.value = version;
                option.textContent = `ANSYS ${version}`;
                versionSelect.appendChild(option);
            }

            // Select version: previously saved version if exists, otherwise first version
            if (state.edbVersion && versions[state.edbVersion]) {
                versionSelect.value = state.edbVersion;
            } else {
                const firstVersion = Object.keys(versions)[0];
                versionSelect.value = firstVersion;
                state.edbVersion = firstVersion;
            }

            versionHint.textContent = `Found ${Object.keys(versions).length} installed version(s)`;
            versionHint.style.color = '#6e6e6e';

            // Validate after loading
            validateSettings();
        }

        hideLoading();
    } catch (error) {
        console.error('Error loading ANSYS versions:', error);
        hideLoading();
        alert('Error detecting ANSYS versions: ' + error);
    }
}

/**
 * Browse for .aedb folder
 */
async function browseFolder() {
    try {
        let path = await pywebview.api.select_edb_folder();

        if (path) {
            // Clean path: remove edb.def if present and trailing slashes
            if (path.endsWith('edb.def')) {
                // Extract parent folder
                const parts = path.split(/[/\\]/);
                parts.pop(); // Remove 'edb.def'
                path = parts.join('\\');
            }

            // Remove trailing slashes
            path = path.replace(/[/\\]+$/, '');

            state.edbPath = path;
            document.getElementById('edbPath').value = path;
            validateSettings();
        } else {
            alert('Please select a valid .aedb folder');
        }
    } catch (error) {
        console.error('Error selecting folder:', error);
        alert('Error selecting folder: ' + error);
    }
}

/**
 * Validate current settings
 */
async function validateSettings() {
    // Update state from UI
    state.edbVersion = document.getElementById('edbVersion').value;
    state.grpc = document.getElementById('grpc').checked;
    state.overwrite = document.getElementById('overwrite').checked;

    // Skip validation if no path selected yet
    if (!state.edbPath) {
        updateValidationUI({
            valid: false,
            status: 'error',
            message: 'Please select an EDB path to continue'
        });
        return;
    }

    try {
        const result = await pywebview.api.validate_settings(
            state.edbPath,
            state.edbVersion,
            state.grpc
        );

        state.isValid = result.valid;
        updateValidationUI(result);

    } catch (error) {
        console.error('Validation error:', error);
        updateValidationUI({
            valid: false,
            status: 'error',
            message: 'Validation error: ' + error
        });
    }
}

/**
 * Update validation UI
 */
function updateValidationUI(result) {
    const statusDiv = document.getElementById('validationStatus');
    const statusIcon = document.getElementById('statusIcon');
    const statusMessage = document.getElementById('statusMessage');
    const saveButton = document.getElementById('saveButton');

    // Show status
    statusDiv.classList.remove('hidden', 'success', 'warning', 'error');
    statusDiv.classList.add(result.status);

    // Update icon
    if (result.status === 'success') {
        statusIcon.textContent = '✓';
    } else if (result.status === 'warning') {
        statusIcon.textContent = '⚠';
    } else {
        statusIcon.textContent = '✗';
    }

    // Update message
    statusMessage.textContent = result.message;

    // Enable/disable save button
    saveButton.disabled = !result.valid;
}

/**
 * Save settings and start data loading
 */
async function saveAndStart() {
    if (!state.isValid) {
        alert('Please fix validation errors before saving');
        return;
    }

    try {
        // Update state from UI before saving
        state.edbVersion = document.getElementById('edbVersion').value;
        state.grpc = document.getElementById('grpc').checked;
        state.overwrite = document.getElementById('overwrite').checked;

        showLoading('Saving settings...');

        const result = await pywebview.api.save_settings(
            state.edbPath,
            state.edbVersion,
            state.grpc,
            state.overwrite
        );

        if (result.success) {
            showLoading('Settings saved! Closing window...');

            // Wait a moment for user to see the message
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Close window
            await pywebview.api.close_window();
        } else {
            hideLoading();
            alert('Error saving settings: ' + result.message);
        }

    } catch (error) {
        console.error('Error saving settings:', error);
        hideLoading();
        alert('Error saving settings: ' + error);
    }
}

/**
 * Show loading overlay
 */
function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    const messageEl = document.getElementById('loadingMessage');

    messageEl.textContent = message;
    overlay.classList.remove('hidden');
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.add('hidden');
}
