/**
 * NetsManager - Handles net information display and interaction
 */
class NetsManager {
    constructor() {
        this.netsData = null;
        this.selectedNets = new Set(); // Store selected net names
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
                           data-type="${type}">
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

        // TODO: Future implementation - apply filtering or highlighting based on selected nets
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
     * @returns {Object} Object with signal and power arrays
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

        return { signal: signalNets, power: powerNets };
    }
}

// Export for use in main.js
window.NetsManager = NetsManager;
