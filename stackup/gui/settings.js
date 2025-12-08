/**
 * Stackup Settings - Frontend Logic
 *
 * Manages the stackup settings UI, including Excel file selection,
 * section extraction, and cut-section mapping.
 */

// Application state
let state = {
    excelFile: null,      // Path to selected Excel file
    sections: [],         // Available sections from Excel
    cuts: [],             // Available cuts from EDB
    mapping: {},          // cut_id -> section_name mapping
    hasConfig: false      // Whether existing config was loaded
};

// Initialize on page load
window.addEventListener('DOMContentLoaded', async () => {
    console.log('Stackup Settings window loaded');
    await loadExistingConfig();
});

/**
 * Load existing configuration if available
 */
async function loadExistingConfig() {
    try {
        showLoading(true);

        const config = await window.pywebview.api.get_current_config();

        if (config.has_config) {
            console.log('Loading existing config:', config);

            state.hasConfig = true;
            state.excelFile = config.excel_file;
            state.mapping = config.cut_stackup_mapping || {};

            // Update UI with loaded Excel file
            if (state.excelFile) {
                document.getElementById('excelFilePath').value = state.excelFile;

                // Auto-analyze the Excel file
                await analyzeExcelFile();
            }
        } else {
            console.log('No existing config found - showing empty state');
        }

        showLoading(false);

    } catch (error) {
        console.error('Failed to load existing config:', error);
        // Don't show error on initial load - just show empty state
        showLoading(false);
    }
}

/**
 * Browse for Excel file
 */
async function browseExcelFile() {
    try {
        console.log('Opening file browser...');

        const result = await window.pywebview.api.browse_excel_file();

        if (result.success) {
            state.excelFile = result.file_path;
            document.getElementById('excelFilePath').value = result.file_path;

            // Clear previous analysis results
            hideAnalysisResult();
            hideMappingSection();

            console.log('Excel file selected:', result.file_path);

            // Auto-analyze the selected file
            await analyzeExcelFile();
        } else {
            console.log('File selection cancelled or failed:', result.error);
        }

    } catch (error) {
        console.error('Error browsing for file:', error);
        showError('Failed to open file browser');
    }
}

/**
 * Analyze Excel file to extract sections
 */
async function analyzeExcelFile() {
    try {
        if (!state.excelFile) {
            showError('Please select an Excel file first');
            return;
        }

        console.log('Analyzing Excel file:', state.excelFile);
        showLoading(true);
        hideError();

        // Extract sections from Excel
        const result = await window.pywebview.api.analyze_excel_file(state.excelFile);

        showLoading(false);

        if (result.success) {
            state.sections = result.sections || [];

            if (state.sections.length === 0) {
                showError('No sections found in Excel file. Please check the file format.');
                hideAnalysisResult();
                hideMappingSection();
                return;
            }

            console.log(`Found ${state.sections.length} sections:`, state.sections);

            // Display sections
            displaySections();

            // Load cuts and show mapping section
            await loadCuts();

        } else {
            showError(result.error || 'Failed to analyze Excel file');
            hideAnalysisResult();
            hideMappingSection();
        }

    } catch (error) {
        console.error('Error analyzing Excel file:', error);
        showError('Failed to analyze Excel file');
        showLoading(false);
    }
}

/**
 * Display extracted sections
 */
function displaySections() {
    const analysisResult = document.getElementById('analysisResult');
    const sectionCount = document.getElementById('sectionCount');
    const sectionList = document.getElementById('sectionList');

    // Update count
    sectionCount.textContent = state.sections.length;

    // Clear list
    sectionList.innerHTML = '';

    // Add sections
    state.sections.forEach(section => {
        const li = document.createElement('li');
        li.textContent = section;
        sectionList.appendChild(li);
    });

    // Show result
    analysisResult.classList.remove('hidden');
}

/**
 * Load available cuts from EDB
 */
async function loadCuts() {
    try {
        console.log('Loading available cuts...');

        const result = await window.pywebview.api.get_available_cuts();

        if (result.success) {
            state.cuts = result.cuts || [];
            console.log(`Loaded ${state.cuts.length} cuts:`, state.cuts);

            if (state.cuts.length === 0) {
                showNoMappingsMessage();
            } else {
                displayCutMappings();
            }

        } else {
            showError(result.error || 'Failed to load cuts');
        }

    } catch (error) {
        console.error('Error loading cuts:', error);
        showError('Failed to load cuts');
    }
}

/**
 * Display cut-section mapping UI
 */
function displayCutMappings() {
    const mappingSection = document.getElementById('mappingSection');
    const cutMappingList = document.getElementById('cutMappingList');
    const noMappingsMessage = document.getElementById('noMappingsMessage');

    // Clear existing content
    cutMappingList.innerHTML = '';

    // Create mapping row for each cut
    state.cuts.forEach(cut => {
        const row = createCutMappingRow(cut);
        cutMappingList.appendChild(row);
    });

    // Show mapping section, hide no mappings message
    mappingSection.classList.remove('hidden');
    noMappingsMessage.classList.add('hidden');

    // Validate to enable/disable save button
    validateMapping();
}

/**
 * Create a cut-section mapping row
 */
function createCutMappingRow(cut) {
    const row = document.createElement('div');
    row.className = 'cut-mapping-row';

    // Cut info
    const cutInfo = document.createElement('div');
    cutInfo.className = 'cut-info';
    cutInfo.innerHTML = `
        <span class="cut-id">${cut.id}</span>
        <span class="cut-type">(${cut.type})</span>
    `;

    // Section selector
    const selector = document.createElement('select');
    selector.className = 'section-selector';
    selector.id = `selector_${cut.id}`;

    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = '-- Select Section --';
    selector.appendChild(defaultOption);

    // Add section options
    state.sections.forEach(section => {
        const option = document.createElement('option');
        option.value = section;
        option.textContent = section;
        selector.appendChild(option);
    });

    // Set current value from state.mapping (if exists)
    if (state.mapping[cut.id]) {
        selector.value = state.mapping[cut.id];
    }

    // Add change listener
    selector.addEventListener('change', (e) => {
        onSectionChange(cut.id, e.target.value);
    });

    row.appendChild(cutInfo);
    row.appendChild(selector);

    return row;
}

/**
 * Handle section selection change
 */
function onSectionChange(cutId, sectionName) {
    if (sectionName) {
        state.mapping[cutId] = sectionName;
        console.log(`Assigned section "${sectionName}" to cut "${cutId}"`);
    } else {
        delete state.mapping[cutId];
        console.log(`Removed section assignment for cut "${cutId}"`);
    }

    validateMapping();
}

/**
 * Validate current mapping and enable/disable save button
 */
function validateMapping() {
    const saveBtn = document.getElementById('saveBtn');

    // Check if Excel file is selected
    if (!state.excelFile) {
        saveBtn.disabled = true;
        return;
    }

    // Check if at least one mapping exists
    const hasMappings = Object.keys(state.mapping).length > 0;

    // Enable save button if we have mappings
    saveBtn.disabled = !hasMappings;
}

/**
 * Save configuration
 */
async function saveConfiguration() {
    try {
        console.log('Saving configuration...');
        console.log('Excel file:', state.excelFile);
        console.log('Mapping:', state.mapping);

        showLoading(true);
        hideError();

        const result = await window.pywebview.api.save_configuration(
            state.excelFile,
            state.mapping
        );

        showLoading(false);

        if (result.success) {
            console.log('Configuration saved successfully');
            console.log('Config path:', result.config_path);
            console.log('Saved mappings:', result.saved_mappings);

            await showAlert(
                'Success',
                `Configuration saved successfully!\n\nSaved ${result.saved_mappings} cut-section mappings.`
            );

            // Close window after successful save
            await closeWindow();

        } else {
            console.error('Save failed:', result.error);
            showError(result.error || 'Failed to save configuration');
        }

    } catch (error) {
        console.error('Error saving configuration:', error);
        showError('Failed to save configuration');
        showLoading(false);
    }
}

/**
 * Close window
 */
async function closeWindow() {
    try {
        if (window.pywebview && window.pywebview.api.close) {
            console.log('Closing window...');
            await window.pywebview.api.close();
        } else {
            console.warn('pywebview.api.close not available');
        }
    } catch (error) {
        console.error('Error closing window:', error);
    }
}

// UI Helper Functions

function showLoading(show) {
    const indicator = document.getElementById('loadingIndicator');
    if (show) {
        indicator.classList.remove('hidden');
    } else {
        indicator.classList.add('hidden');
    }
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');

    errorText.textContent = message;
    errorDiv.classList.remove('hidden');

    console.error('Error:', message);
}

function hideError() {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.classList.add('hidden');
}

function hideAnalysisResult() {
    const analysisResult = document.getElementById('analysisResult');
    analysisResult.classList.add('hidden');
}

function hideMappingSection() {
    const mappingSection = document.getElementById('mappingSection');
    mappingSection.classList.add('hidden');
}

function showNoMappingsMessage() {
    const mappingSection = document.getElementById('mappingSection');
    const cutMappingList = document.getElementById('cutMappingList');
    const noMappingsMessage = document.getElementById('noMappingsMessage');

    cutMappingList.innerHTML = '';
    mappingSection.classList.remove('hidden');
    noMappingsMessage.classList.remove('hidden');
}

/**
 * Show custom alert dialog
 */
function showAlert(title, message) {
    return new Promise((resolve) => {
        const modal = document.getElementById('customAlert');
        const alertTitle = document.getElementById('alertTitle');
        const alertMessage = document.getElementById('alertMessage');

        alertTitle.textContent = title;
        alertMessage.textContent = message;

        modal.classList.remove('hidden');

        // Store resolve function for closeAlert to call
        window._alertResolve = resolve;
    });
}

/**
 * Close alert dialog
 */
function closeAlert() {
    const modal = document.getElementById('customAlert');
    modal.classList.add('hidden');

    if (window._alertResolve) {
        window._alertResolve();
        delete window._alertResolve;
    }
}
