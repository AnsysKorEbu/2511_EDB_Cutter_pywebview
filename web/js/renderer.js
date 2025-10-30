/**
 * EDB Renderer using Pixi.js and WebGL
 */
class EDBRenderer {
    constructor(containerId) {
        this.containerId = containerId;
        this.app = null;
        this.viewport = null;

        // Layers
        this.planeLayer = null;
        this.traceLayer = null;
        this.componentLayer = null;
        this.selectionLayer = null;

        // Layer colors
        this.layerColors = {
            'Top': 0xFF4444,
            'Bottom': 0x4444FF,
            'signal_1': 0xFF6666,
            'signal_2': 0x6666FF,
            'spt': 0x44FF44,
            'GND': 0x666666,
            'PWR': 0xFF8844
        };

        this.initialize();
    }

    initialize() {
        // Create Pixi application
        this.app = new PIXI.Application({
            backgroundColor: 0x1a1a1a,
            antialias: true,
            resolution: window.devicePixelRatio || 1,
            autoDensity: true,
            resizeTo: document.getElementById(this.containerId)
        });

        // Add canvas to container
        document.getElementById(this.containerId).appendChild(this.app.view);

        // Create viewport as a simple container
        this.viewport = new PIXI.Container();
        this.viewport.interactive = true;
        this.viewport.sortableChildren = true;

        this.app.stage.addChild(this.viewport);

        // Create layers
        this.planeLayer = new PIXI.Container();
        this.traceLayer = new PIXI.Container();
        this.componentLayer = new PIXI.Container();
        this.selectionLayer = new PIXI.Container();

        this.viewport.addChild(this.planeLayer);
        this.viewport.addChild(this.traceLayer);
        this.viewport.addChild(this.componentLayer);
        this.viewport.addChild(this.selectionLayer);

        // Setup pan and zoom
        this.setupPanZoom();

        // Handle window resize
        window.addEventListener('resize', () => {
            this.app.renderer.resize(
                document.getElementById(this.containerId).clientWidth,
                document.getElementById(this.containerId).clientHeight
            );
        });
    }

    setupPanZoom() {
        let isDragging = false;
        let lastPosition = { x: 0, y: 0 };

        // Mouse wheel for zoom
        this.app.view.addEventListener('wheel', (e) => {
            e.preventDefault();

            const delta = e.deltaY;
            const zoomFactor = delta > 0 ? 0.9 : 1.1;

            // Get mouse position in world coordinates
            const worldPos = {
                x: (e.offsetX - this.viewport.x) / this.viewport.scale.x,
                y: (e.offsetY - this.viewport.y) / this.viewport.scale.y
            };

            // Apply zoom
            this.viewport.scale.x *= zoomFactor;
            this.viewport.scale.y *= zoomFactor;

            // Clamp zoom
            this.viewport.scale.x = Math.max(0.01, Math.min(10000, this.viewport.scale.x));
            this.viewport.scale.y = Math.max(0.01, Math.min(10000, this.viewport.scale.y));

            // Adjust position to zoom towards mouse
            this.viewport.x = e.offsetX - worldPos.x * this.viewport.scale.x;
            this.viewport.y = e.offsetY - worldPos.y * this.viewport.scale.y;
        });

        // Mouse drag for pan
        this.app.view.addEventListener('mousedown', (e) => {
            if (e.button === 1 || (e.button === 0 && e.shiftKey)) { // Middle button or Shift+Left
                isDragging = true;
                lastPosition = { x: e.clientX, y: e.clientY };
                this.app.view.style.cursor = 'grabbing';
            }
        });

        this.app.view.addEventListener('mousemove', (e) => {
            if (isDragging) {
                const dx = e.clientX - lastPosition.x;
                const dy = e.clientY - lastPosition.y;

                this.viewport.x += dx;
                this.viewport.y += dy;

                lastPosition = { x: e.clientX, y: e.clientY };
            }
        });

        this.app.view.addEventListener('mouseup', (e) => {
            if (isDragging) {
                isDragging = false;
                this.app.view.style.cursor = 'default';
            }
        });

        this.app.view.addEventListener('mouseleave', () => {
            if (isDragging) {
                isDragging = false;
                this.app.view.style.cursor = 'default';
            }
        });
    }

    async loadData() {
        try {
            console.log('Loading EDB data...');

            // Get configuration using pywebview
            const config = await pywebview.api.get_config();
            CONFIG.scale = config.scale;
            CONFIG.inputUnit = config.inputUnit;
            console.log(`Unit configuration: ${config.inputUnit} -> ${CONFIG.outputUnit} (scale: ${CONFIG.scale})`);

            // Get data using pywebview
            const [planes, traces, components, bounds] = await Promise.all([
                pywebview.api.get_planes(),
                pywebview.api.get_traces(),
                pywebview.api.get_components(),
                pywebview.api.get_bounds()
            ]);

            console.log(`Loaded: ${planes.length} planes, ${traces.length} traces, ${Object.keys(components).length} components`);

            // Render data
            this.renderPlanes(planes);
            this.renderTraces(traces);
            this.renderComponents(components);

            // Fit to content
            this.fitToContent(bounds);

            console.log('Rendering complete');
        } catch (error) {
            console.error('Error loading data:', error);
            alert('Error loading EDB data: ' + error.message);
        }
    }

    renderPlanes(planes) {
        console.log(`Rendering ${planes.length} planes...`);

        planes.forEach((plane, index) => {
            try {
                const graphics = new PIXI.Graphics();

                // Get layer color
                const color = this.getLayerColor(plane.layer);
                graphics.beginFill(color, 0.6);
                graphics.lineStyle(0, color, 1);

                // Draw polygon
                const points = plane.points;
                if (points && points.length > 0) {
                    // Flatten points array
                    const flatPoints = [];
                    points.forEach(pt => {
                        if (Array.isArray(pt)) {
                            flatPoints.push(pt[0], pt[1]);
                        }
                    });

                    if (flatPoints.length >= 6) {  // At least 3 points (x,y pairs)
                        graphics.drawPolygon(flatPoints);
                    }
                }

                graphics.endFill();

                // Make interactive
                graphics.interactive = true;
                graphics.buttonMode = true;

                graphics.on('pointerover', () => {
                    graphics.alpha = 1.0;
                });

                graphics.on('pointerout', () => {
                    graphics.alpha = 0.6;
                });

                // Store metadata
                graphics.userData = plane;

                this.planeLayer.addChild(graphics);
            } catch (error) {
                console.error(`Error rendering plane ${index}:`, error);
            }
        });
    }

    renderTraces(traces) {
        console.log(`Rendering ${traces.length} traces...`);

        traces.forEach((trace, index) => {
            try {
                const graphics = new PIXI.Graphics();

                // Get layer color
                const color = this.getLayerColor(trace.layer);
                const width = trace.width || 0.0001;

                graphics.lineStyle(width, color, 0.8);

                // Draw center line
                const points = trace.center_line;
                if (points && points.length > 1) {
                    graphics.moveTo(points[0][0], points[0][1]);

                    for (let i = 1; i < points.length; i++) {
                        graphics.lineTo(points[i][0], points[i][1]);
                    }
                }

                // Store metadata
                graphics.userData = trace;

                this.traceLayer.addChild(graphics);
            } catch (error) {
                console.error(`Error rendering trace ${index}:`, error);
            }
        });
    }

    renderComponents(components) {
        console.log(`Rendering ${Object.keys(components).length} components...`);

        Object.entries(components).forEach(([name, position]) => {
            try {
                const graphics = new PIXI.Graphics();

                // Draw component marker (small circle)
                graphics.beginFill(0xFFFF00, 0.8);
                graphics.drawCircle(position[0], position[1], 0.0005);  // 0.5mm radius
                graphics.endFill();

                // Store metadata
                graphics.userData = { name, position };

                this.componentLayer.addChild(graphics);
            } catch (error) {
                console.error(`Error rendering component ${name}:`, error);
            }
        });
    }

    getLayerColor(layerName) {
        // Check if layer has predefined color
        if (this.layerColors[layerName]) {
            return this.layerColors[layerName];
        }

        // Generate color based on layer name hash
        let hash = 0;
        for (let i = 0; i < layerName.length; i++) {
            hash = layerName.charCodeAt(i) + ((hash << 5) - hash);
        }

        const color = Math.abs(hash) % 0xFFFFFF;
        this.layerColors[layerName] = color;  // Cache for consistency

        return color;
    }

    fitToContent(bounds) {
        const width = bounds.x_max - bounds.x_min;
        const height = bounds.y_max - bounds.y_min;
        const centerX = (bounds.x_min + bounds.x_max) / 2;
        const centerY = (bounds.y_min + bounds.y_max) / 2;

        console.log(`Fitting to bounds: ${width} x ${height} at (${centerX}, ${centerY})`);

        // Calculate scale to fit content
        const padding = 50; // pixels
        const scaleX = (this.app.screen.width - padding * 2) / width;
        const scaleY = (this.app.screen.height - padding * 2) / height;
        const scale = Math.min(scaleX, scaleY);

        this.viewport.scale.set(scale);

        // Center the content
        this.viewport.x = this.app.screen.width / 2 - centerX * scale;
        this.viewport.y = this.app.screen.height / 2 - centerY * scale;
    }

    fitToView() {
        // Get bounds of all content
        const bounds = this.viewport.getLocalBounds();

        if (bounds.width === 0 || bounds.height === 0) {
            return;
        }

        const padding = 50;
        const scaleX = (this.app.screen.width - padding * 2) / bounds.width;
        const scaleY = (this.app.screen.height - padding * 2) / bounds.height;
        const scale = Math.min(scaleX, scaleY);

        this.viewport.scale.set(scale);

        const centerX = bounds.x + bounds.width / 2;
        const centerY = bounds.y + bounds.height / 2;

        this.viewport.x = this.app.screen.width / 2 - centerX * scale;
        this.viewport.y = this.app.screen.height / 2 - centerY * scale;
    }

    clearSelection() {
        this.selectionLayer.removeChildren();
    }
}
