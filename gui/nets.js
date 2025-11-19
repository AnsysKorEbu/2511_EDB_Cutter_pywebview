/**
 * NetsManager - Handles net information display and interaction
 */
class NetsManager {
    constructor() {
        this.netsData = null;
        this.selectedNets = new Set(); // Store selected net names
        this.selectedReferenceLayer = null; // Store selected reference layer
    }

    /**
     * Load nets data from Python API
     */
    async loadNetsData() {
        try {
            console.log('Loading nets data...');
            this.netsData = await pywebview.api.get_nets_data();
            console.log('Nets data loaded:', this.netsData);

            // Render the nets panel
            this.renderNetsPanel();

            return this.netsData;
        } catch (error) {
            console.error('Error loading nets data:', error);
            return null;
        }
    }

    /**
     * Render the nets panel with signal and power/ground sections
     */
    renderNetsPanel() {
        const netsContent = document.getElementById('nets-content');
        if (!netsContent) {
            console.error('Nets content container not found');
            return;
        }

        if (!this.netsData) {
            netsContent.innerHTML = '<p style="color: #888; padding: 10px;">No nets data available</p>';
            return;
        }

        const signalNets = this.netsData.signal || [];
        const powerNets = this.netsData.power || [];

        // Build HTML structure
        let html = `
            <div class="nets-panel">
                <!-- Control buttons -->
                <div class="nets-controls">
                    <button id="select-all-nets" class="nets-btn">Select All</button>
                    <button id="deselect-all-nets" class="nets-btn">Deselect All</button>
                </div>

                <!-- Reference Layer Selection -->
                <div class="reference-layer-section">
                    <label for="referenceLayerSelect" class="reference-layer-label">
                        <span style="color: #ff6b6b;">*</span> Reference Layer for Gap Ports:
                    </label>
                    <select id="referenceLayerSelect" class="reference-layer-select">
                        <option value="">-- Select Layer --</option>
                        ${this.renderLayerOptions()}
                    </select>
                </div>

                <!-- Signal Nets Section -->
                <div class="nets-section">
                    <div class="nets-section-header" data-section="signal">
                        <span class="expand-icon">▼</span>
                        <span class="section-title">Signal Nets (${signalNets.length})</span>
                    </div>
                    <div class="nets-list" id="signal-nets-list" data-expanded="true">
                        ${this.renderNetsList(signalNets, 'signal')}
                    </div>
                </div>

                <!-- Power/Ground Nets Section -->
                <div class="nets-section">
                    <div class="nets-section-header" data-section="power">
                        <span class="expand-icon">▼</span>
                        <span class="section-title">Power/Ground Nets (${powerNets.length})</span>
                    </div>
                    <div class="nets-list" id="power-nets-list" data-expanded="true">
                        ${this.renderNetsList(powerNets, 'power')}
                    </div>
                </div>
            </div>
        `;

        netsContent.innerHTML = html;

        // Initialize event handlers
        this.initEventHandlers();

        // Auto-select all nets on initial load
        const checkboxes = document.querySelectorAll('.net-checkbox:checked');
        checkboxes.forEach(checkbox => {
            this.selectedNets.add(checkbox.dataset.net);
        });
        console.log(`[NetsManager] Auto-selected ${this.selectedNets.size} nets`);
    }

    /**
     * Render layer options for reference layer dropdown
     */
    renderLayerOptions() {
        if (!window.layersMap || window.layersMap.size === 0) {
            return '';
        }

        const layerNames = Array.from(window.layersMap.keys());
        return layerNames.map(layerName =>
            `<option value="${layerName}">${layerName}</option>`
        ).join('');
    }

    /**
     * Render a list of nets with checkboxes
     */
    renderNetsList(nets, type) {
        if (!nets || nets.length === 0) {
            return '<p style="color: #888; padding: 5px 10px; font-size: 12px;">No nets found</p>';
        }

        return nets.map(netName => `
            <div class="net-item">
                <label class="net-label">
                    <input type="checkbox" class="net-checkbox"
                           data-net="${netName}"
                           data-type="${type}"
                           checked>
                    <span class="net-name" title="${netName}">${netName}</span>
                </label>
            </div>
        `).join('');
    }

    /**
     * Initialize event handlers for the nets panel
     */
    initEventHandlers() {
        // Select All button
        const selectAllBtn = document.getElementById('select-all-nets');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAllNets());
        }

        // Deselect All button
        const deselectAllBtn = document.getElementById('deselect-all-nets');
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.deselectAllNets());
        }

        // Reference Layer dropdown
        const referenceLayerSelect = document.getElementById('referenceLayerSelect');
        if (referenceLayerSelect) {
            referenceLayerSelect.addEventListener('change', (e) => this.onReferenceLayerChange(e));
        }

        // Section headers (expand/collapse)
        const sectionHeaders = document.querySelectorAll('.nets-section-header');
        sectionHeaders.forEach(header => {
            header.addEventListener('click', (e) => this.toggleSection(e));
        });

        // Checkbox change events
        const checkboxes = document.querySelectorAll('.net-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.onNetCheckboxChange(e));
        });
    }

    /**
     * Toggle section expand/collapse
     */
    toggleSection(event) {
        const header = event.currentTarget;
        const section = header.dataset.section;
        const listId = `${section}-nets-list`;
        const list = document.getElementById(listId);
        const icon = header.querySelector('.expand-icon');

        if (!list) return;

        const isExpanded = list.dataset.expanded === 'true';

        if (isExpanded) {
            list.style.display = 'none';
            list.dataset.expanded = 'false';
            icon.textContent = '▶';
        } else {
            list.style.display = 'block';
            list.dataset.expanded = 'true';
            icon.textContent = '▼';
        }
    }

    /**
     * Select all nets
     */
    selectAllNets() {
        const checkboxes = document.querySelectorAll('.net-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            this.selectedNets.add(checkbox.dataset.net);
        });
        console.log('All nets selected:', this.selectedNets.size);

        // Update canvas highlighting
        if (typeof setHighlightedNets !== 'undefined') {
            setHighlightedNets(this.selectedNets);
        }
    }

    /**
     * Deselect all nets
     */
    deselectAllNets() {
        const checkboxes = document.querySelectorAll('.net-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        this.selectedNets.clear();
        console.log('All nets deselected');

        // Update canvas highlighting (clear all highlights)
        if (typeof setHighlightedNets !== 'undefined') {
            setHighlightedNets(new Set());
        }
    }

    /**
     * Handle checkbox change event
     */
    onNetCheckboxChange(event) {
        const checkbox = event.target;
        const netName = checkbox.dataset.net;
        const netType = checkbox.dataset.type;

        if (checkbox.checked) {
            this.selectedNets.add(netName);
            console.log(`Net selected: ${netName} (${netType})`);
        } else {
            this.selectedNets.delete(netName);
            console.log(`Net deselected: ${netName} (${netType})`);
        }

        console.log(`Total selected nets: ${this.selectedNets.size}`);

        // Update canvas highlighting
        if (typeof setHighlightedNets !== 'undefined') {
            setHighlightedNets(this.selectedNets);
        }
    }

    /**
     * Handle reference layer dropdown change event
     */
    onReferenceLayerChange(event) {
        const select = event.target;
        this.selectedReferenceLayer = select.value || null;
        console.log(`Reference layer selected: ${this.selectedReferenceLayer}`);
    }

    /**
     * Get currently selected nets
     * @returns {Array} Array of selected net names
     */
    getSelectedNets() {
        return Array.from(this.selectedNets);
    }

    /**
     * Get selected nets by type
     * @returns {Object} Object with signal and power arrays, and reference_layer
     */
    getSelectedNetsByType() {
        const signalNets = [];
        const powerNets = [];

        document.querySelectorAll('.net-checkbox:checked').forEach(checkbox => {
            const netName = checkbox.dataset.net;
            const netType = checkbox.dataset.type;

            if (netType === 'signal') {
                signalNets.push(netName);
            } else if (netType === 'power') {
                powerNets.push(netName);
            }
        });

        return {
            signal: signalNets,
            power: powerNets,
            reference_layer: this.selectedReferenceLayer
        };
    }

    /**
     * Update layer dropdown options after layersMap is loaded
     */
    updateLayerDropdown() {
        const select = document.getElementById('referenceLayerSelect');
        if (!select) {
            console.log('[NetsManager] Reference layer select not found');
            return;
        }

        if (!window.layersMap || window.layersMap.size === 0) {
            console.log('[NetsManager] LayersMap not available yet');
            return;
        }

        // Clear existing options except the first one
        while (select.options.length > 1) {
            select.remove(1);
        }

        // Add layer options
        const layerNames = Array.from(window.layersMap.keys());
        layerNames.forEach(layerName => {
            const option = document.createElement('option');
            option.value = layerName;
            option.textContent = layerName;
            select.appendChild(option);
        });

        console.log(`[NetsManager] Updated layer dropdown with ${layerNames.length} layers`);

        // Auto-select the last layer
        if (layerNames.length > 0) {
            const lastLayer = layerNames[layerNames.length - 1];
            select.value = lastLayer;
            this.selectedReferenceLayer = lastLayer;
            console.log(`[NetsManager] Auto-selected last layer: ${lastLayer}`);
        }
    }
}

// Export for use in main.js
window.NetsManager = NetsManager;
