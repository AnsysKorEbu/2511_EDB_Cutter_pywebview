/**
 * Circuit Generator GUI JavaScript
 *
 * Handles config file selection, loading, and HFSS project generation.
 */

// Global state management
let circuitState = {
    configLoaded: false,
    configPath: null,
    configData: null,
    metadata: null
};

/**
 * Initialize GUI when pywebview is ready
 */
window.addEventListener('pywebviewready', async function() {
    console.log('Circuit Generator GUI ready');
    await init();
});

/**
 * Main initialization function
 */
async function init() {
    try {
        console.log('Loading recent configs...');

        // Load recent configs and populate dropdown
        await loadRecentConfigs();

    } catch (error) {
        console.error('Failed to initialize:', error);
        showError(`Failed to load GUI: ${error.message || error}`);
    }
}

/**
 * Load recent config files and populate dropdown
 */
async function loadRecentConfigs() {
    try {
        const result = await window.pywebview.api.get_recent_configs(5);

        if (!result.success) {
            console.error('Failed to get recent configs:', result.error);
            showError(`Failed to load recent configs: ${result.error}`);
            return;
        }

        const configs = result.configs || [];
        console.log(`Found ${configs.length} recent configs`);

        // Populate dropdown
        const dropdown = document.getElementById('recentConfigs');
        dropdown.innerHTML = '';

        if (configs.length === 0) {
            // No configs found
            const option = document.createElement('option');
            option.value = '';
            option.textContent = '-- No recent configs found --';
            dropdown.appendChild(option);
            console.log('No recent configs found');
            return;
        }

        // Add configs to dropdown
        configs.forEach((config, index) => {
            const option = document.createElement('option');
            option.value = config.path;
            option.textContent = config.folder;
            dropdown.appendChild(option);
        });

        // Auto-select first config
        if (configs.length > 0) {
            dropdown.selectedIndex = 0;
            console.log('Auto-selecting most recent config:', configs[0].path);
            await loadConfig(configs[0].path);
        }

    } catch (error) {
        console.error('Failed to load recent configs:', error);
        showError(`Error loading recent configs: ${error.message || error}`);
    }
}

/**
 * Handle recent config selection from dropdown
 */
async function selectRecentConfig() {
    const dropdown = document.getElementById('recentConfigs');
    const selectedPath = dropdown.value;

    if (!selectedPath) {
        console.log('No config selected from dropdown');
        return;
    }

    console.log('Selected config from dropdown:', selectedPath);
    await loadConfig(selectedPath);
}

/**
 * Browse for config file using file dialog
 */
async function browseConfigFile() {
    try {
        console.log('Opening file browser...');

        const result = await window.pywebview.api.browse_config_file();

        if (!result.success) {
            console.log('File selection cancelled:', result.error);
            return;
        }

        console.log('Selected config file:', result.config_path);
        await loadConfig(result.config_path);

    } catch (error) {
        console.error('Failed to browse file:', error);
        showError(`Error browsing file: ${error.message || error}`);
    }
}

/**
 * Load config file and display metadata
 */
async function loadConfig(configPath) {
    try {
        console.log('Loading config:', configPath);

        const result = await window.pywebview.api.load_config(configPath);

        if (!result.success) {
            console.error('Failed to load config:', result.error);
            showError(`Failed to load config: ${result.error}`);
            circuitState.configLoaded = false;
            updateRunButton();
            return;
        }

        // Update state
        circuitState.configLoaded = true;
        circuitState.configPath = configPath;
        circuitState.configData = result.config_data;
        circuitState.metadata = result.metadata;

        console.log('Config loaded successfully:', result.metadata);

        // Update UI with metadata
        document.getElementById('configPath').textContent = getFileName(configPath);
        document.getElementById('configPath').title = configPath;
        document.getElementById('analysisFolder').textContent = result.metadata.analysis_folder;
        document.getElementById('totalFiles').textContent = result.metadata.total_files;
        document.getElementById('configVersion').textContent = result.metadata.version;

        // Enable Run button
        updateRunButton();

        // Show success message
        showSuccess(`Config loaded successfully: ${getFileName(configPath)}`);

    } catch (error) {
        console.error('Failed to load config:', error);
        showError(`Error loading config: ${error.message || error}`);
        circuitState.configLoaded = false;
        updateRunButton();
    }
}

/**
 * Update Run button state (enable/disable)
 */
function updateRunButton() {
    const runBtn = document.getElementById('runBtn');

    if (circuitState.configLoaded) {
        runBtn.disabled = false;
        runBtn.classList.add('enabled');
    } else {
        runBtn.disabled = true;
        runBtn.classList.remove('enabled');
    }
}

/**
 * Run HFSS project generation
 */
async function runHfssGeneration() {
    try {
        if (!circuitState.configLoaded) {
            showError('No config loaded. Please select a config file first.');
            return;
        }

        console.log('Running HFSS generation...');

        // Show loading state
        const runBtn = document.getElementById('runBtn');
        const originalText = runBtn.textContent;
        runBtn.textContent = '⏳ Generating...';
        runBtn.disabled = true;

        // Call API to create HFSS project
        const result = await window.pywebview.api.create_hfss_project();

        // Restore button state
        runBtn.textContent = originalText;
        runBtn.disabled = false;

        if (!result.success) {
            console.error('Failed to create HFSS project:', result.error);
            showError(`Failed to create HFSS project: ${result.error}`);
            return;
        }

        console.log('HFSS project created successfully:', result.aedt_file);
        showSuccess(result.message || `HFSS project created: ${result.aedt_file}`);

    } catch (error) {
        console.error('Error running HFSS generation:', error);
        showError(`Error: ${error.message || error}`);

        // Restore button state
        const runBtn = document.getElementById('runBtn');
        runBtn.textContent = '▶ Run HFSS Generation';
        runBtn.disabled = false;
    }
}

/**
 * Show success message
 */
function showSuccess(message) {
    const statusSection = document.getElementById('statusSection');
    const statusMessage = document.getElementById('statusMessage');

    statusMessage.innerHTML = `<div class="success-message">${message}</div>`;
    statusSection.classList.remove('hidden');

    console.log('[SUCCESS]', message);

    // Auto-hide after 10 seconds
    setTimeout(() => {
        statusSection.classList.add('hidden');
    }, 10000);
}

/**
 * Show error message
 */
function showError(message) {
    const statusSection = document.getElementById('statusSection');
    const statusMessage = document.getElementById('statusMessage');

    statusMessage.innerHTML = `<div class="error-message">${message}</div>`;
    statusSection.classList.remove('hidden');

    console.error('[ERROR]', message);

    // Auto-hide after 15 seconds
    setTimeout(() => {
        statusSection.classList.add('hidden');
    }, 15000);
}

/**
 * Get filename from full path
 */
function getFileName(path) {
    if (!path) return '';
    return path.split('\\').pop().split('/').pop();
}