// sectionSelector.js
// Section selection workflow for stackup processing

// State management
let sectionSelector = {
    excelFile: null,
    sections: [],     // ['C/N 1', 'RIGID 5', ...]
    cuts: [],         // [{id, type, points}, ...]
    mapping: {},      // {cut_001: 'RIGID 5', cut_002: 'C/N 1'} - 1:1 mapping
    extractorJson: null,  // Path to FPCB-Extractor JSON (required - legacy removed)
    isExtractorBased: true  // Always true (legacy workflow removed)
};

// Legacy functions removed - use useStackupExtractor() instead
// - browseSectionExcel() → useStackupExtractor()
// - browseExcelForSectionSelection() → useStackupExtractor()

/**
 * Use FPCB-Extractor to process stackup Excel file
 */
async function useStackupExtractor() {
    try {
        // Browse for Excel file and process with stackup_extractor
        const result = await window.pywebview.api.use_stackup_extractor();

        if (!result.success) {
            await customAlert(result.error || 'Failed to process with stackup_extractor');
            return;
        }

        // Store extracted data (extractor mode)
        sectionSelector.excelFile = result.excel_file;
        sectionSelector.sections = result.sections;
        sectionSelector.extractorJson = result.output_file;  // Store JSON path
        sectionSelector.isExtractorBased = true;  // Mark as extractor-based

        // Check if sections were extracted
        if (!sectionSelector.sections || sectionSelector.sections.length === 0) {
            await customAlert('No sections found in the processed Excel file');
            return;
        }

        // Update Excel file path display in Cut Executor modal
        const excelPathElement = document.getElementById('excelFilePath');
        if (excelPathElement) {
            excelPathElement.textContent = result.excel_file;
            excelPathElement.title = result.excel_file;
        }

        // Enable Section Selection button
        const sectionBtn = document.getElementById('processSectionSelectionBtn');
        if (sectionBtn) {
            sectionBtn.disabled = false;
        }

        // Show success message with extraction details
        let message = `✓ FPCB-Extractor processed successfully!\n\n`;
        message += `Format: ${result.format_type}\n`;
        message += `Layers: ${result.layer_count}\n`;
        message += `Sections: ${result.section_count}\n`;
        message += `Output: ${result.output_file}`;

        await customAlert(message);

    } catch (error) {
        console.error('Error in useStackupExtractor:', error);
        await customAlert(`Unexpected error: ${error.message}`);
    }
}

/**
 * Open section selection modal and render content
 */
async function openSectionSelectionModal() {
    try {
        // Check if Excel file is loaded
        if (!sectionSelector.excelFile || !sectionSelector.sections || sectionSelector.sections.length === 0) {
            await customAlert('Please browse and load an Excel file first');
            return;
        }

        // Get available cuts
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

        const modal = document.getElementById('sectionSelectionModal');

        if (!modal) {
            console.error('Section selection modal not found');
            return;
        }

        // Populate Excel file info
        const excelPathElement = document.getElementById('sectionExcelPath');
        if (excelPathElement) {
            excelPathElement.textContent = sectionSelector.excelFile;
            excelPathElement.title = sectionSelector.excelFile;
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

    } catch (error) {
        console.error('Error in openSectionSelectionModal:', error);
        await customAlert(`Unexpected error: ${error.message}`);
    }
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

        // Save to backend (pass extractor JSON if using extractor-based workflow)
        const result = await window.pywebview.api.save_section_selection(
            sectionSelector.excelFile,
            sectionSelector.mapping,
            sectionSelector.extractorJson  // Pass extractor JSON path or null
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

            // Show success message + validation results
            const statusDiv = document.getElementById('sectionStatus');
            const sectionFilename = result.sss_file.split(/[/\\]/).pop();
            const layerFilename = result.layer_file.split(/[/\\]/).pop();

            // Build validation results HTML
            let validationHtml = '';
            const validation = result.validation || [];
            const allMatch = validation.length > 0 && validation.every(v => v.match);
            const hasFailure = validation.some(v => !v.match);

            if (validation.length > 0) {
                const validationLines = validation.map(v => {
                    if (v.match) {
                        return `<div style="color: #4ec9b0;">&#10003; ${escapeHtml(v.cut_id)} (${escapeHtml(v.section)}): ${v.copper_count} layers - Validated</div>`;
                    } else {
                        return `<div style="color: #f44747;">&#10007; ${escapeHtml(v.cut_id)} (${escapeHtml(v.section)}): COPPER ${v.copper_count} != EDB ${v.edb_count}</div>`;
                    }
                }).join('');

                validationHtml = `
                    <div style="margin-top: 8px; padding: 6px 8px; background: #1e1e1e; border-radius: 4px; font-size: 0.85em; font-family: monospace;">
                        <div style="margin-bottom: 4px; color: #ccc;"><strong>Layer Validation (EDB: ${validation[0]?.edb_count} conductor layers)</strong></div>
                        ${validationLines}
                    </div>
                `;
            }

            if (hasFailure) {
                // Validation failed - show warning, don't auto-close
                statusDiv.innerHTML = `
                    <div class="status-success" style="border-left: 3px solid #f44747;">
                        <span class="status-icon" style="color: #f44747;">!</span>
                        <div>
                            <div><strong>Saved, but layer count mismatch detected</strong></div>
                            <div style="margin-top: 4px; font-size: 0.9em;">
                                <div>Section file: ${escapeHtml(sectionFilename)}</div>
                                <div>Layer file: ${escapeHtml(layerFilename)}</div>
                            </div>
                            ${validationHtml}
                        </div>
                    </div>
                `;
            } else {
                statusDiv.innerHTML = `
                    <div class="status-success">
                        <span class="status-icon">✓</span>
                        <div>
                            <div><strong>Configuration saved successfully!</strong></div>
                            <div style="margin-top: 4px; font-size: 0.9em;">
                                <div>Section file: ${escapeHtml(sectionFilename)}</div>
                                <div>Layer file: ${escapeHtml(layerFilename)}</div>
                            </div>
                            ${validationHtml}
                        </div>
                    </div>
                `;

                // Auto-close only when all validated
                setTimeout(() => {
                    closeSectionSelection();
                }, 2500);
            }

            statusDiv.classList.remove('hidden');

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
 * Clear SSS file selection
 */
function clearSssFileSelection() {
    // Reset SSS file path display
    const sssPathElement = document.getElementById('sssFilePath');
    if (sssPathElement) {
        sssPathElement.textContent = 'No file selected';
        sssPathElement.title = '';
    }

    console.log('SSS file selection cleared - stackup will not be applied');
}

/**
 * Close section selection modal and reset state
 */
function closeSectionSelection() {
    const modal = document.getElementById('sectionSelectionModal');
    if (modal) {
        modal.classList.add('hidden');
    }

    // Reset state (preserve excel file and extractor json for potential reuse)
    const preservedExcel = sectionSelector.excelFile;
    const preservedJson = sectionSelector.extractorJson;
    const preservedIsExtractor = sectionSelector.isExtractorBased;

    sectionSelector = {
        excelFile: preservedExcel,
        sections: [],
        cuts: [],
        mapping: {},
        extractorJson: preservedJson,
        isExtractorBased: preservedIsExtractor
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
