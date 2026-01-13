// sectionSelector.js
// Section selection workflow for stackup processing

// State management
let sectionSelector = {
    excelFile: null,
    sections: [],     // ['C/N 1', 'RIGID 5', ...]
    cuts: [],         // [{id, type, points}, ...]
    mapping: {}       // {cut_001: 'RIGID 5', cut_002: 'C/N 1'} - 1:1 mapping
};

/**
 * Browse for Excel file and load sections
 */
async function browseSectionExcel() {
    try {
        // Browse for Excel file and extract sections
        const result = await window.pywebview.api.browse_excel_for_sections();

        if (!result.success) {
            await customAlert(result.error || 'Failed to browse Excel file');
            return;
        }

        // Store sections data
        sectionSelector.excelFile = result.excel_file;
        sectionSelector.sections = result.sections;

        // Check if sections were extracted
        if (!sectionSelector.sections || sectionSelector.sections.length === 0) {
            await customAlert('No sections found in Excel file row 8');
            return;
        }

        // Update Excel file path display
        const excelPathElement = document.getElementById('sectionExcelPath');
        if (excelPathElement) {
            excelPathElement.textContent = result.excel_file;
            excelPathElement.title = result.excel_file;
        }

        // Update section count and render tags
        const sectionCountElement = document.getElementById('sectionCount');
        if (sectionCountElement) {
            sectionCountElement.textContent = sectionSelector.sections.length;
        }

        renderSectionTags();
        renderCutSectionMapping();

        await customAlert(`Loaded ${sectionSelector.sections.length} sections from Excel file`);

    } catch (error) {
        console.error('Error in browseSectionExcel:', error);
        await customAlert(`Unexpected error: ${error.message}`);
    }
}

/**
 * Start section selection workflow
 * Step 1: Check for last used Excel file or prompt to browse
 * Step 2: Get available cuts
 * Step 3: Open section selection modal
 */
async function startSectionSelection() {
    try {
        // Step 1: Get available cuts first
        const cutsResult = await window.pywebview.api.get_cuts_for_section_selection();

        if (!cutsResult.success) {
            await customAlert(cutsResult.error || 'Failed to get cuts');
            return;
        }

        sectionSelector.cuts = cutsResult.cuts;

        // Check if cuts exist
        if (!sectionSelector.cuts || sectionSelector.cuts.length === 0) {
            await customAlert('No cuts available. Please create cuts first using Cut Mode.');
            return;
        }

        // Step 2: Browse for Excel file (will show last used path if available)
        const result = await window.pywebview.api.browse_excel_for_sections();

        if (!result.success) {
            await customAlert(result.error || 'Failed to browse Excel file');
            return;
        }

        sectionSelector.excelFile = result.excel_file;
        sectionSelector.sections = result.sections;

        // Check if sections were extracted
        if (!sectionSelector.sections || sectionSelector.sections.length === 0) {
            await customAlert('No sections found in Excel file row 8');
            return;
        }

        // Save Excel file path to localStorage for next time
        localStorage.setItem('lastSectionExcelFile', sectionSelector.excelFile);

        // Step 3: Open section selection modal
        openSectionSelectionModal();

    } catch (error) {
        console.error('Error in startSectionSelection:', error);
        await customAlert(`Unexpected error: ${error.message}`);
    }
}

/**
 * Open section selection modal and render content
 */
function openSectionSelectionModal() {
    const modal = document.getElementById('sectionSelectionModal');

    if (!modal) {
        console.error('Section selection modal not found');
        return;
    }

    // Populate Excel file info
    const excelPathElement = document.getElementById('sectionExcelPath');
    if (excelPathElement) {
        const filename = sectionSelector.excelFile.split(/[/\\]/).pop();
        excelPathElement.textContent = filename;
    }

    // Populate section count
    const sectionCountElement = document.getElementById('sectionCount');
    if (sectionCountElement) {
        sectionCountElement.textContent = sectionSelector.sections.length;
    }

    // Render section tags
    renderSectionTags();

    // Render cut-section mapping grid
    renderCutSectionMapping();

    // Clear previous status
    const statusDiv = document.getElementById('sectionStatus');
    if (statusDiv) {
        statusDiv.classList.add('hidden');
        statusDiv.innerHTML = '';
    }

    // Show modal
    modal.classList.remove('hidden');
}

/**
 * Render available sections as tags
 */
function renderSectionTags() {
    const container = document.getElementById('sectionTags');
    if (!container) return;

    container.innerHTML = sectionSelector.sections.map(section =>
        `<span class="section-tag">${escapeHtml(section)}</span>`
    ).join('');
}

/**
 * Render cut-section mapping grid with dropdown selects
 */
function renderCutSectionMapping() {
    const container = document.getElementById('sectionMappingList');
    if (!container) return;

    container.innerHTML = sectionSelector.cuts.map(cut => {
        const selectId = `select_${sanitizeId(cut.id)}`;
        const options = sectionSelector.sections.map(section =>
            `<option value="${escapeHtml(section)}">${escapeHtml(section)}</option>`
        ).join('');

        return `
            <div class="section-cut-item" data-cut-id="${escapeHtml(cut.id)}">
                <div class="section-cut-header">
                    <span class="cut-id">${escapeHtml(cut.id)}</span>
                    <span class="cut-type">${escapeHtml(cut.type)}</span>
                    <span class="cut-points">${cut.point_count} points</span>
                </div>
                <div class="section-dropdown-container">
                    <label for="${selectId}" class="section-label">Select Section:</label>
                    <select id="${selectId}"
                            class="section-dropdown"
                            data-cut-id="${escapeHtml(cut.id)}"
                            onchange="updateSectionMapping()">
                        <option value="">-- Select a section --</option>
                        ${options}
                    </select>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Update section mapping when dropdown changes
 */
function updateSectionMapping() {
    // Clear existing mapping
    sectionSelector.mapping = {};

    // Collect selected section for each cut
    sectionSelector.cuts.forEach(cut => {
        const selectElement = document.querySelector(
            `select[data-cut-id="${cut.id}"]`
        );

        if (selectElement && selectElement.value) {
            sectionSelector.mapping[cut.id] = selectElement.value;
        }
    });

    console.log('Updated mapping:', sectionSelector.mapping);
}

/**
 * Save section selection to .sss file
 */
async function saveSectionSelection() {
    try {
        // Validate at least one cut has sections selected
        if (Object.keys(sectionSelector.mapping).length === 0) {
            await customAlert('Please select at least one section for at least one cut');
            return;
        }

        // Disable save button
        const saveBtn = document.getElementById('saveSectionBtn');
        const originalBtnText = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span>⏳ Saving...</span>';

        // Save to backend
        const result = await window.pywebview.api.save_section_selection(
            sectionSelector.excelFile,
            sectionSelector.mapping
        );

        // Re-enable button
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalBtnText;

        if (result.success) {
            // Update SSS file path display in Cut Executor modal
            const sssPathElement = document.getElementById('sssFilePath');
            if (sssPathElement && result.sss_file) {
                const filename = result.sss_file.split(/[/\\]/).pop();
                sssPathElement.textContent = filename;
                sssPathElement.title = result.sss_file;
            }

            // Show success message
            const statusDiv = document.getElementById('sectionStatus');
            const sectionFilename = result.sss_file.split(/[/\\]/).pop();
            const layerFilename = result.layer_file.split(/[/\\]/).pop();

            statusDiv.innerHTML = `
                <div class="status-success">
                    <span class="status-icon">✓</span>
                    <div>
                        <div><strong>Configuration saved successfully!</strong></div>
                        <div style="margin-top: 4px; font-size: 0.9em;">
                            <div>Section file: ${escapeHtml(sectionFilename)}</div>
                            <div>Layer file: ${escapeHtml(layerFilename)}</div>
                        </div>
                    </div>
                </div>
            `;
            statusDiv.classList.remove('hidden');

            // Close modal after delay
            setTimeout(() => {
                closeSectionSelection();
            }, 2500);

        } else {
            await customAlert('Failed to save: ' + (result.error || 'Unknown error'));
        }

    } catch (error) {
        console.error('Error in saveSectionSelection:', error);
        await customAlert(`Unexpected error: ${error.message}`);

        // Re-enable button on error
        const saveBtn = document.getElementById('saveSectionBtn');
        saveBtn.disabled = false;
    }
}

/**
 * Load existing SSS file
 */
async function loadSssFile() {
    try {
        const result = await window.pywebview.api.browse_sss_file();

        if (!result.success) {
            if (result.error && !result.error.includes('cancelled')) {
                await customAlert(result.error || 'Failed to load SSS file');
            }
            return;
        }

        // Update SSS file path display
        const sssPathElement = document.getElementById('sssFilePath');
        if (sssPathElement && result.sss_file) {
            const filename = result.sss_file.split(/[/\\]/).pop();
            sssPathElement.textContent = filename;
            sssPathElement.title = result.sss_file;
        }

        // Show success message
        await customAlert(`SSS file loaded:\n${result.sss_file.split(/[/\\]/).pop()}`);

    } catch (error) {
        console.error('Error in loadSssFile:', error);
        await customAlert(`Unexpected error: ${error.message}`);
    }
}

/**
 * Close section selection modal and reset state
 */
function closeSectionSelection() {
    const modal = document.getElementById('sectionSelectionModal');
    if (modal) {
        modal.classList.add('hidden');
    }

    // Reset state
    sectionSelector = {
        excelFile: null,
        sections: [],
        cuts: [],
        mapping: {}
    };

    // Clear modal content
    const mappingList = document.getElementById('sectionMappingList');
    if (mappingList) {
        mappingList.innerHTML = '';
    }

    const statusDiv = document.getElementById('sectionStatus');
    if (statusDiv) {
        statusDiv.classList.add('hidden');
        statusDiv.innerHTML = '';
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Sanitize string for use in HTML IDs
 */
function sanitizeId(str) {
    return str.replace(/[^a-zA-Z0-9_-]/g, '_');
}
