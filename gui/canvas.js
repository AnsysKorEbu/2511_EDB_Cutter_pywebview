// Canvas and context
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

// Data storage
let planesData = [];
let viasData = [];
let tracesData = [];
let layersMap = new Map();

// View state
let viewState = {
    offsetX: 0,
    offsetY: 0,
    scale: 100,
    isDragging: false,
    lastX: 0,
    lastY: 0
};

// Bounds
let dataBounds = {
    minX: Infinity,
    minY: Infinity,
    maxX: -Infinity,
    maxY: -Infinity
};

// Layer colors
const layerColors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
    '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788'
];

// Off-screen canvas for caching static layers
let offscreenCanvas = null;
let offscreenCtx = null;
let cacheValid = false;
let offscreenTransform = { scale: 1, offsetX: 0, offsetY: 0 };

// Initialize canvas size
function resizeCanvas() {
    const container = canvas.parentElement;
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    render();
}

// Load data and process
function loadData(data) {
    planesData = data;
    layersMap.clear();

    // Calculate bounds and group by layer
    dataBounds = {
        minX: Infinity,
        minY: Infinity,
        maxX: -Infinity,
        maxY: -Infinity
    };

    let totalPoints = 0;

    planesData.forEach(plane => {
        // Update bounds from points
        if (plane.points && plane.points.length > 0) {
            plane.points.forEach(([x, y]) => {
                dataBounds.minX = Math.min(dataBounds.minX, x);
                dataBounds.minY = Math.min(dataBounds.minY, y);
                dataBounds.maxX = Math.max(dataBounds.maxX, x);
                dataBounds.maxY = Math.max(dataBounds.maxY, y);
            });
        }

        // Count points
        totalPoints += plane.points.length;

        // Group by layer
        const layer = plane.layer || 'default';
        if (!layersMap.has(layer)) {
            layersMap.set(layer, {
                name: layer,
                planes: [],
                vias: [],
                traces: [],
                visible: true,
                color: layerColors[layersMap.size % layerColors.length]
            });
        }
        layersMap.get(layer).planes.push(plane);
    });

    // Process traces and assign to layers
    if (tracesData && tracesData.length > 0) {
        tracesData.forEach(trace => {
            // Update bounds from trace center_line
            if (trace.center_line && trace.center_line.length > 0) {
                trace.center_line.forEach(([x, y]) => {
                    // Filter out invalid data (e.g., extremely large values)
                    if (isFinite(x) && isFinite(y) && Math.abs(x) < 1 && Math.abs(y) < 1) {
                        dataBounds.minX = Math.min(dataBounds.minX, x);
                        dataBounds.minY = Math.min(dataBounds.minY, y);
                        dataBounds.maxX = Math.max(dataBounds.maxX, x);
                        dataBounds.maxY = Math.max(dataBounds.maxY, y);
                    }
                });
            }

            // Group by layer
            const layer = trace.layer || 'default';
            if (!layersMap.has(layer)) {
                layersMap.set(layer, {
                    name: layer,
                    planes: [],
                    vias: [],
                    traces: [],
                    visible: true,
                    color: layerColors[layersMap.size % layerColors.length]
                });
            }
            layersMap.get(layer).traces.push(trace);
        });
    }

    // Process vias and assign to layers
    if (viasData && viasData.length > 0) {
        viasData.forEach(via => {
            // Update bounds from via position
            if (via.position && via.position.length >= 2) {
                dataBounds.minX = Math.min(dataBounds.minX, via.position[0]);
                dataBounds.minY = Math.min(dataBounds.minY, via.position[1]);
                dataBounds.maxX = Math.max(dataBounds.maxX, via.position[0]);
                dataBounds.maxY = Math.max(dataBounds.maxY, via.position[1]);
            }

            // Add via to all layers in its range
            if (via.layer_range_names && via.layer_range_names.length > 0) {
                via.layer_range_names.forEach(layerName => {
                    if (!layersMap.has(layerName)) {
                        layersMap.set(layerName, {
                            name: layerName,
                            planes: [],
                            vias: [],
                            traces: [],
                            visible: true,
                            color: layerColors[layersMap.size % layerColors.length]
                        });
                    }
                    layersMap.get(layerName).vias.push(via);
                });
            }
        });
    }

    // Update UI
    document.getElementById('planeCount').textContent = planesData.length;
    document.getElementById('traceCount').textContent = tracesData.length;
    document.getElementById('viaCount').textContent = viasData.length;
    document.getElementById('layerCount').textContent = layersMap.size;
    document.getElementById('pointCount').textContent = totalPoints.toLocaleString();

    updateLayerList();
    resetView();
}

// Update layer list UI
function updateLayerList() {
    const layerList = document.getElementById('layerList');
    layerList.innerHTML = '';

    layersMap.forEach((layer, layerName) => {
        const item = document.createElement('div');
        item.className = 'layer-item';
        item.style.opacity = layer.visible ? '1' : '0.5';
        item.onclick = () => toggleLayer(layerName);

        const planeCount = layer.planes.length;
        const traceCount = layer.traces ? layer.traces.length : 0;
        const viaCount = layer.vias ? layer.vias.length : 0;
        const totalCount = planeCount + traceCount + viaCount;

        item.innerHTML = `
            <div class="layer-color" style="background: ${layer.color}"></div>
            <div class="layer-info">
                <span class="layer-name">${layerName}</span>
                <span class="layer-count" title="P:${planeCount} T:${traceCount} V:${viaCount}">${totalCount}</span>
            </div>
        `;

        layerList.appendChild(item);
    });
}

// Toggle layer visibility
function toggleLayer(layerName) {
    const layer = layersMap.get(layerName);
    if (layer) {
        layer.visible = !layer.visible;
        cacheValid = false; // Invalidate cache when layer visibility changes
        updateLayerList();
        render();
    }
}

// Reset view to fit all data
function resetView() {
    if (planesData.length === 0) return;

    const dataWidth = dataBounds.maxX - dataBounds.minX;
    const dataHeight = dataBounds.maxY - dataBounds.minY;

    // Calculate scale to fit
    const scaleX = (canvas.width * 0.8) / dataWidth;
    const scaleY = (canvas.height * 0.8) / dataHeight;
    viewState.scale = Math.min(scaleX, scaleY);

    // Center the view
    const centerX = (dataBounds.minX + dataBounds.maxX) / 2;
    const centerY = (dataBounds.minY + dataBounds.maxY) / 2;

    viewState.offsetX = canvas.width / 2 - centerX * viewState.scale;
    viewState.offsetY = canvas.height / 2 + centerY * viewState.scale;  // Y axis is flipped

    updateZoomLabel();
    render();
}

// Get viewport bounds in world coordinates
function getViewportBounds() {
    const topLeft = screenToWorld(0, 0);
    const bottomRight = screenToWorld(canvas.width, canvas.height);

    return {
        minX: Math.min(topLeft.x, bottomRight.x),
        maxX: Math.max(topLeft.x, bottomRight.x),
        minY: Math.min(topLeft.y, bottomRight.y),
        maxY: Math.max(topLeft.y, bottomRight.y)
    };
}

// Check if plane is visible in viewport (rough bounding box check)
function isPlaneVisible(plane, viewport) {
    if (!plane.points || plane.points.length === 0) return false;

    // Calculate plane bounding box
    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;

    for (const [x, y] of plane.points) {
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x);
        maxY = Math.max(maxY, y);
    }

    // Check if bounding boxes overlap
    return !(maxX < viewport.minX || minX > viewport.maxX ||
             maxY < viewport.minY || minY > viewport.maxY);
}

// Cache static layers (planes and vias) to off-screen canvas
function cacheStaticLayers() {
    // Create or reuse offscreen canvas
    if (!offscreenCanvas) {
        offscreenCanvas = document.createElement('canvas');
        offscreenCtx = offscreenCanvas.getContext('2d');
    }

    // Set resolution - higher = better quality but more memory
    // Using 50,000 pixels per meter for higher zoom support (20μm per pixel)
    const pixelsPerMeter = 50000;

    const dataWidth = dataBounds.maxX - dataBounds.minX;
    const dataHeight = dataBounds.maxY - dataBounds.minY;

    // Limit to max 8192x8192 for browser compatibility
    offscreenCanvas.width = Math.min(8192, Math.ceil(dataWidth * pixelsPerMeter));
    offscreenCanvas.height = Math.min(8192, Math.ceil(dataHeight * pixelsPerMeter));

    // Calculate transform for offscreen rendering
    offscreenTransform.scale = offscreenCanvas.width / dataWidth;
    offscreenTransform.offsetX = -dataBounds.minX * offscreenTransform.scale;
    offscreenTransform.offsetY = dataBounds.maxY * offscreenTransform.scale;

    // Clear offscreen canvas
    offscreenCtx.clearRect(0, 0, offscreenCanvas.width, offscreenCanvas.height);

    // Helper function to transform world coords to offscreen coords
    function worldToOffscreen(x, y) {
        return {
            x: x * offscreenTransform.scale + offscreenTransform.offsetX,
            y: -y * offscreenTransform.scale + offscreenTransform.offsetY
        };
    }

    // Step 1: Draw all plane fills
    layersMap.forEach((layer) => {
        if (!layer.visible) return;

        offscreenCtx.fillStyle = layer.color + '80';

        layer.planes.forEach(plane => {
            if (!plane.points || plane.points.length < 3) return;

            offscreenCtx.beginPath();

            // Draw outer boundary
            const first = worldToOffscreen(plane.points[0][0], plane.points[0][1]);
            offscreenCtx.moveTo(first.x, first.y);

            for (let i = 1; i < plane.points.length; i++) {
                const pt = worldToOffscreen(plane.points[i][0], plane.points[i][1]);
                offscreenCtx.lineTo(pt.x, pt.y);
            }
            offscreenCtx.closePath();

            // Draw voids (holes)
            if (plane.voids && plane.voids.length > 0) {
                for (const void_points of plane.voids) {
                    if (void_points.length < 3) continue;
                    const firstVoid = worldToOffscreen(void_points[0][0], void_points[0][1]);
                    offscreenCtx.moveTo(firstVoid.x, firstVoid.y);
                    for (let i = 1; i < void_points.length; i++) {
                        const pt = worldToOffscreen(void_points[i][0], void_points[i][1]);
                        offscreenCtx.lineTo(pt.x, pt.y);
                    }
                    offscreenCtx.closePath();
                }
            }

            offscreenCtx.fill('evenodd');
        });
    });

    // Step 2: Draw all plane borders
    offscreenCtx.strokeStyle = '#000000';
    offscreenCtx.lineWidth = 1.5;

    layersMap.forEach((layer) => {
        if (!layer.visible) return;

        layer.planes.forEach(plane => {
            if (!plane.points || plane.points.length < 3) return;

            // Draw outer boundary stroke
            offscreenCtx.beginPath();
            const first = worldToOffscreen(plane.points[0][0], plane.points[0][1]);
            offscreenCtx.moveTo(first.x, first.y);

            for (let i = 1; i < plane.points.length; i++) {
                const pt = worldToOffscreen(plane.points[i][0], plane.points[i][1]);
                offscreenCtx.lineTo(pt.x, pt.y);
            }
            offscreenCtx.closePath();
            offscreenCtx.stroke();

            // Draw void strokes
            if (plane.voids && plane.voids.length > 0) {
                for (const void_points of plane.voids) {
                    if (void_points.length < 3) continue;
                    offscreenCtx.beginPath();
                    const firstVoid = worldToOffscreen(void_points[0][0], void_points[0][1]);
                    offscreenCtx.moveTo(firstVoid.x, firstVoid.y);
                    for (let i = 1; i < void_points.length; i++) {
                        const pt = worldToOffscreen(void_points[i][0], void_points[i][1]);
                        offscreenCtx.lineTo(pt.x, pt.y);
                    }
                    offscreenCtx.closePath();
                    offscreenCtx.stroke();
                }
            }
        });
    });

    // Step 3: Draw traces
    layersMap.forEach((layer) => {
        if (!layer.visible) return;

        if (layer.traces && layer.traces.length > 0) {
            layer.traces.forEach(trace => {
                if (!trace.center_line || trace.center_line.length < 2) return;

                // Get trace width (default to 0.0001m = 0.1mm if not specified)
                const traceWidth = (trace.width || 0.0001) * offscreenTransform.scale;
                // Use actual width, minimum 1.5px for visibility
                const renderWidth = Math.max(traceWidth, 1.5);

                offscreenCtx.strokeStyle = layer.color;
                offscreenCtx.lineWidth = renderWidth;
                offscreenCtx.lineCap = 'round';
                offscreenCtx.lineJoin = 'round';

                offscreenCtx.beginPath();

                // Filter and render only valid points
                let started = false;
                for (let i = 0; i < trace.center_line.length; i++) {
                    const [x, y] = trace.center_line[i];
                    // Skip invalid points (like the corrupted data in line__1582)
                    if (!isFinite(x) || !isFinite(y) || Math.abs(x) >= 1 || Math.abs(y) >= 1) {
                        continue;
                    }

                    const pt = worldToOffscreen(x, y);
                    if (!started) {
                        offscreenCtx.moveTo(pt.x, pt.y);
                        started = true;
                    } else {
                        offscreenCtx.lineTo(pt.x, pt.y);
                    }
                }

                if (started) {
                    offscreenCtx.stroke();
                }
            });
        }
    });

    // Step 4: Draw vias (deduplicated - each via only once)
    const drawnVias = new Set();
    layersMap.forEach((layer) => {
        if (!layer.visible) return;

        if (layer.vias && layer.vias.length > 0) {
            layer.vias.forEach(via => {
                if (!via.position || via.position.length < 2) return;

                // Skip if already drawn
                const viaKey = `${via.position[0]},${via.position[1]},${via.name || ''}`;
                if (drawnVias.has(viaKey)) return;
                drawnVias.add(viaKey);

                const pos = worldToOffscreen(via.position[0], via.position[1]);
                const viaRadius = (via.radius || 0.00015) * offscreenTransform.scale;

                // Draw via fill
                offscreenCtx.fillStyle = layer.color + 'CC';
                offscreenCtx.beginPath();
                offscreenCtx.arc(pos.x, pos.y, viaRadius, 0, 2 * Math.PI);
                offscreenCtx.fill();

                // Draw via border
                offscreenCtx.strokeStyle = '#000000';
                offscreenCtx.lineWidth = 1.5;
                offscreenCtx.beginPath();
                offscreenCtx.arc(pos.x, pos.y, viaRadius, 0, 2 * Math.PI);
                offscreenCtx.stroke();
            });
        }
    });

    cacheValid = true;
    console.log(`Cached ${planesData.length} planes and ${tracesData.length} traces to ${offscreenCanvas.width}x${offscreenCanvas.height} offscreen canvas`);
}

// World to screen coordinates
function worldToScreen(x, y) {
    return {
        x: x * viewState.scale + viewState.offsetX,
        y: -y * viewState.scale + viewState.offsetY  // Flip Y axis for screen coordinates
    };
}

// Screen to world coordinates
function screenToWorld(x, y) {
    return {
        x: (x - viewState.offsetX) / viewState.scale,
        y: (viewState.offsetY - y) / viewState.scale  // Flip Y axis back to world coordinates
    };
}

// Render all planes
function render() {
    // Clear canvas
    ctx.fillStyle = '#1e1e1e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (planesData.length === 0) {
        ctx.fillStyle = '#858585';
        ctx.font = '14px Segoe UI';
        ctx.textAlign = 'center';
        ctx.fillText('Click "Reload Data" to load planes from source folder', canvas.width / 2, canvas.height / 2);
        return;
    }

    // Draw grid
    drawGrid();

    // Ensure cache is valid
    if (!cacheValid) {
        cacheStaticLayers();
    }

    // LOD threshold: switch to vector rendering when zoom exceeds cache resolution
    // This ensures crisp rendering at high zoom (μm level, up to 100,000x zoom)
    const lodThreshold = offscreenTransform.scale * 1.5;
    const useVectorRendering = viewState.scale > lodThreshold;

    if (useVectorRendering) {
        // High zoom: Vector rendering with viewport culling for crisp μm-level detail
        const viewport = getViewportBounds();

        // Step 1: Draw all plane fills (only visible ones)
        layersMap.forEach((layer) => {
            if (!layer.visible) return;

            ctx.fillStyle = layer.color + '80';

            layer.planes.forEach(plane => {
                if (isPlaneVisible(plane, viewport)) {
                    drawPlaneFill(plane);
                }
            });
        });

        // Step 2: Draw all plane borders
        ctx.strokeStyle = '#000000';
        // Keep constant 0.8 pixel width for clean appearance
        ctx.lineWidth = 0.8;

        layersMap.forEach((layer) => {
            if (!layer.visible) return;

            layer.planes.forEach(plane => {
                if (isPlaneVisible(plane, viewport)) {
                    drawPlaneStroke(plane);
                }
            });
        });

        // Step 3: Draw traces
        layersMap.forEach((layer) => {
            if (!layer.visible) return;

            if (layer.traces && layer.traces.length > 0) {
                layer.traces.forEach(trace => {
                    if (!trace.center_line || trace.center_line.length < 2) return;

                    // Simple visibility check: check if any valid point is in viewport
                    const isVisible = trace.center_line.some(([x, y]) =>
                        isFinite(x) && isFinite(y) && Math.abs(x) < 1 && Math.abs(y) < 1 &&
                        x >= viewport.minX && x <= viewport.maxX &&
                        y >= viewport.minY && y <= viewport.maxY
                    );

                    if (isVisible) {
                        drawTrace(trace, layer.color);
                    }
                });
            }
        });

        // Step 4: Draw vias (deduplicated - each via only once)
        const drawnVias = new Set();
        layersMap.forEach((layer) => {
            if (!layer.visible) return;

            if (layer.vias && layer.vias.length > 0) {
                layer.vias.forEach(via => {
                    if (!via.position || via.position.length < 2) return;

                    // Skip if already drawn
                    const viaKey = `${via.position[0]},${via.position[1]},${via.name || ''}`;
                    if (drawnVias.has(viaKey)) return;
                    drawnVias.add(viaKey);

                    const [vx, vy] = via.position;
                    if (vx >= viewport.minX && vx <= viewport.maxX &&
                        vy >= viewport.minY && vy <= viewport.maxY) {
                        drawVia(via, layer.color);
                    }
                });
            }
        });

    } else {
        // Low zoom: Fast cached image rendering for overview
        const topLeft = worldToScreen(dataBounds.minX, dataBounds.maxY);
        const bottomRight = worldToScreen(dataBounds.maxX, dataBounds.minY);

        const screenWidth = bottomRight.x - topLeft.x;
        const screenHeight = bottomRight.y - topLeft.y;

        // Draw the cached image scaled to current view
        ctx.drawImage(offscreenCanvas, topLeft.x, topLeft.y, screenWidth, screenHeight);
    }

    // Draw saved cuts
    if (cutMode.enabled) {
        drawSavedCuts();
        // Draw current cut being drawn
        if (cutMode.isDrawing && cutMode.currentCut.length > 0) {
            drawCurrentCut();
        }
    }
}

// Draw grid
function drawGrid() {
    const gridSize = 0.01; // 10mm in meters
    const screenGridSize = gridSize * viewState.scale;

    if (screenGridSize < 10) return; // Don't draw if too small

    ctx.strokeStyle = '#3e3e42';
    ctx.lineWidth = 1;

    // Vertical lines
    const startX = Math.floor((-viewState.offsetX / viewState.scale) / gridSize) * gridSize;
    for (let x = startX; x * viewState.scale + viewState.offsetX < canvas.width; x += gridSize) {
        const screenX = worldToScreen(x, 0).x;
        ctx.beginPath();
        ctx.moveTo(screenX, 0);
        ctx.lineTo(screenX, canvas.height);
        ctx.stroke();
    }

    // Horizontal lines (Y axis is flipped)
    // Screen Y=0 corresponds to world Y = offsetY/scale
    // Screen Y=height corresponds to world Y = (offsetY-height)/scale
    const worldYTop = viewState.offsetY / viewState.scale;
    const worldYBottom = (viewState.offsetY - canvas.height) / viewState.scale;
    const startY = Math.floor(Math.min(worldYTop, worldYBottom) / gridSize) * gridSize;
    const endY = Math.ceil(Math.max(worldYTop, worldYBottom) / gridSize) * gridSize;

    for (let y = startY; y <= endY; y += gridSize) {
        const screenY = worldToScreen(0, y).y;
        if (screenY >= 0 && screenY <= canvas.height) {
            ctx.beginPath();
            ctx.moveTo(0, screenY);
            ctx.lineTo(canvas.width, screenY);
            ctx.stroke();
        }
    }
}

// Draw plane fill only
function drawPlaneFill(plane) {
    if (!plane.points || plane.points.length < 3) return;

    ctx.beginPath();

    // Draw outer boundary (main polygon)
    const firstPoint = worldToScreen(plane.points[0][0], plane.points[0][1]);
    ctx.moveTo(firstPoint.x, firstPoint.y);

    for (let i = 1; i < plane.points.length; i++) {
        const point = worldToScreen(plane.points[i][0], plane.points[i][1]);
        ctx.lineTo(point.x, point.y);
    }
    ctx.closePath();

    // Draw voids (holes) if they exist
    if (plane.voids && plane.voids.length > 0) {
        for (const void_points of plane.voids) {
            if (void_points.length < 3) continue;

            const firstVoidPoint = worldToScreen(void_points[0][0], void_points[0][1]);
            ctx.moveTo(firstVoidPoint.x, firstVoidPoint.y);

            for (let i = 1; i < void_points.length; i++) {
                const point = worldToScreen(void_points[i][0], void_points[i][1]);
                ctx.lineTo(point.x, point.y);
            }
            ctx.closePath();
        }
    }

    // Fill with evenodd rule to create holes
    ctx.fill('evenodd');
}

// Draw plane stroke only
function drawPlaneStroke(plane) {
    if (!plane.points || plane.points.length < 3) return;

    // Draw outer boundary stroke
    ctx.beginPath();
    const firstPoint = worldToScreen(plane.points[0][0], plane.points[0][1]);
    ctx.moveTo(firstPoint.x, firstPoint.y);

    for (let i = 1; i < plane.points.length; i++) {
        const point = worldToScreen(plane.points[i][0], plane.points[i][1]);
        ctx.lineTo(point.x, point.y);
    }

    ctx.closePath();
    ctx.stroke();

    // Draw void strokes (holes)
    if (plane.voids && plane.voids.length > 0) {
        for (const void_points of plane.voids) {
            if (void_points.length < 3) continue;

            ctx.beginPath();
            const firstVoidPoint = worldToScreen(void_points[0][0], void_points[0][1]);
            ctx.moveTo(firstVoidPoint.x, firstVoidPoint.y);

            for (let i = 1; i < void_points.length; i++) {
                const point = worldToScreen(void_points[i][0], void_points[i][1]);
                ctx.lineTo(point.x, point.y);
            }

            ctx.closePath();
            ctx.stroke();
        }
    }
}

// Draw trace as polyline
function drawTrace(trace, color) {
    if (!trace.center_line || trace.center_line.length < 2) return;

    // Get trace width (default to 0.0001m = 0.1mm if not specified)
    const traceWidth = trace.width || 0.0001;
    const screenWidth = traceWidth * viewState.scale;
    // Use actual trace width at high zoom, minimum 1.5px at low zoom
    const renderWidth = Math.max(screenWidth, 1.5);

    ctx.strokeStyle = color;
    ctx.lineWidth = renderWidth;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    ctx.beginPath();

    // Filter and render only valid points
    let started = false;
    for (let i = 0; i < trace.center_line.length; i++) {
        const [x, y] = trace.center_line[i];
        // Skip invalid points (like the corrupted data in line__1582)
        if (!isFinite(x) || !isFinite(y) || Math.abs(x) >= 1 || Math.abs(y) >= 1) {
            continue;
        }

        const point = worldToScreen(x, y);
        if (!started) {
            ctx.moveTo(point.x, point.y);
            started = true;
        } else {
            ctx.lineTo(point.x, point.y);
        }
    }

    if (started) {
        ctx.stroke();
    }
}

// Draw via as circle
function drawVia(via, color) {
    if (!via.position || via.position.length < 2) return;

    const screenPos = worldToScreen(via.position[0], via.position[1]);

    // Use via radius from data, fallback to default (0.15mm = 0.00015m)
    const viaRadius = via.radius || 0.00015;
    const screenRadius = viaRadius * viewState.scale;

    // Draw via fill
    ctx.fillStyle = color + 'CC'; // Semi-transparent
    ctx.beginPath();
    ctx.arc(screenPos.x, screenPos.y, screenRadius, 0, 2 * Math.PI);
    ctx.fill();

    // Draw via border
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 0.8;
    ctx.beginPath();
    ctx.arc(screenPos.x, screenPos.y, screenRadius, 0, 2 * Math.PI);
    ctx.stroke();
}

// Zoom functions
function zoomIn() {
    viewState.scale *= 1.2;
    updateZoomLabel();
    render();
}

function zoomOut() {
    viewState.scale /= 1.2;
    updateZoomLabel();
    render();
}

function updateZoomLabel() {
    const zoomPercent = Math.round(viewState.scale * 100 / 100);
    document.getElementById('zoomLevel').textContent = zoomPercent + '%';
}

// Window resize handler
window.addEventListener('resize', resizeCanvas);
