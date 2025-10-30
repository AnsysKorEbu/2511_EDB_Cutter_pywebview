/**
 * UI Controller - Handles user interactions and UI updates
 */
class UIController {
    constructor(renderer) {
        this.renderer = renderer;
        this.setupMouseTracking();
        this.setupButtons();
    }

    setupMouseTracking() {
        const viewport = this.renderer.viewport;

        // Track mouse movement
        viewport.on('mousemove', (event) => {
            // Get world coordinates (in input units: mm)
            const worldPos = viewport.toWorld(event.data.global);

            // Convert to micrometers
            const xUM = worldPos.x * CONFIG.scale;
            const yUM = worldPos.y * CONFIG.scale;

            // Update display
            this.updateCoordinateDisplay(xUM, yUM);
        });

        // Track zoom level
        viewport.on('zoomed', () => {
            const zoomPercent = (viewport.scale.x * 100).toFixed(1);
            const zoomElement = document.getElementById('zoom-level');
            if (zoomElement) {
                zoomElement.textContent = `Zoom: ${zoomPercent}%`;
            }
        });
    }

    updateCoordinateDisplay(xUM, yUM) {
        const coordsElement = document.getElementById('mouse-coords');
        if (coordsElement) {
            coordsElement.textContent = `X: ${xUM.toFixed(3)} μm, Y: ${yUM.toFixed(3)} μm`;
        }
    }

    setupButtons() {
        // Fit to view button
        const btnFit = document.getElementById('btn-fit');
        if (btnFit) {
            btnFit.onclick = async () => {
                const bounds = await pywebview.api.get_bounds();
                this.renderer.fitToContent(bounds);
            };
        }

        // Clear button
        const btnClear = document.getElementById('btn-clear');
        if (btnClear) {
            btnClear.onclick = () => {
                if (window.polygonSelector) {
                    window.polygonSelector.cancelDrawing();
                }
                this.disableCutButton();
            };
        }
    }

    enableCutButton() {
        const btnCut = document.getElementById('btn-cut');
        if (btnCut) {
            btnCut.disabled = false;
        }
    }

    disableCutButton() {
        const btnCut = document.getElementById('btn-cut');
        if (btnCut) {
            btnCut.disabled = true;
        }
    }

    updateCoordinatesList(points) {
        const listElement = document.getElementById('coordinates-list');
        if (!listElement) return;

        if (points.length === 0) {
            listElement.innerHTML = '<p>클릭하여 점 추가</p>';
            return;
        }

        const html = points.map((pt, index) => {
            const xUM = pt[0] * CONFIG.scale;
            const yUM = pt[1] * CONFIG.scale;

            return `
                <div class="coord-item">
                    <span class="coord-index">점 ${index + 1}</span>
                    <span class="coord-value">X: ${xUM.toFixed(3)} μm</span>
                    <span class="coord-value">Y: ${yUM.toFixed(3)} μm</span>
                </div>
            `;
        }).join('');

        listElement.innerHTML = html;
    }

    showMessage(message, type = 'info') {
        const statusBar = document.getElementById('status-bar');
        if (!statusBar) return;

        const messageElement = document.createElement('span');
        messageElement.textContent = message;
        messageElement.className = `message message-${type}`;
        messageElement.style.marginLeft = '20px';

        statusBar.appendChild(messageElement);

        // Remove after 3 seconds
        setTimeout(() => {
            messageElement.remove();
        }, 3000);
    }
}
