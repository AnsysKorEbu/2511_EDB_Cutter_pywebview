// Cut mode state
let cutMode = {
    enabled: false,
    activeTool: null,
    currentCut: [],
    isDrawing: false,
    savedCuts: [],
    panMode: false,  // Temporary pan mode in cut mode
    snapPoint: null  // Current snap point {x, y} in world coordinates
};

// Snap settings
const SNAP_DISTANCE = 15;  // Snap distance in screen pixels

// Toggle cut mode
function toggleCutMode() {
    cutMode.enabled = !cutMode.enabled;
    const btn = document.getElementById('cutModeBtn');
    const cutTools = document.getElementById('cutTools');
    const cutList = document.getElementById('cutList');

    if (cutMode.enabled) {
        btn.classList.add('active');
        cutTools.classList.remove('hidden');
        cutList.classList.remove('hidden');
        canvas.classList.add('cut-mode');
        refreshCutList();
        document.getElementById('statusText').textContent = 'Cut Mode Active - Select a tool to start cutting';
    } else {
        btn.classList.remove('active');
        cutTools.classList.add('hidden');
        cutList.classList.add('hidden');
        canvas.classList.remove('cut-mode');
        cutMode.activeTool = null;
        cutMode.currentCut = [];
        cutMode.isDrawing = false;
        cutMode.panMode = false;
        document.querySelectorAll('.cut-tool-btn').forEach(b => b.classList.remove('active'));
        document.getElementById('finishCutBtn').classList.add('hidden');
        document.getElementById('statusText').textContent = 'Cut Mode Disabled';
        canvas.style.cursor = 'grab';
    }

    render();
}

// Select cut tool
function selectCutTool(tool) {
    if (!cutMode.enabled) return;

    // Reset current drawing
    cutMode.currentCut = [];
    cutMode.isDrawing = false;

    // Set active tool
    cutMode.activeTool = tool;

    // Update UI
    document.querySelectorAll('.cut-tool-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tool="${tool}"]`).classList.add('active');

    // Update hint
    const hints = {
        'line': 'Click two points to draw a line',
        'rectangle': 'Click two opposite corners to draw a rectangle',
        'polyline': 'Click points, then click near last point to finish',
        'polygon': 'Click points to draw polygon, click near start point to close'
    };
    document.getElementById('cutHint').textContent = hints[tool];
    document.getElementById('statusText').textContent = `${tool.toUpperCase()} tool selected - ${hints[tool]}`;

    // Show finish button for polyline
    document.getElementById('finishCutBtn').classList.add('hidden');

    render();
}

// Toggle pan mode
function togglePanMode() {
    if (!cutMode.enabled) return;

    cutMode.panMode = !cutMode.panMode;
    const panBtn = document.getElementById('panModeBtn');

    if (cutMode.panMode) {
        panBtn.style.background = '#10a37f';
        panBtn.textContent = '✋ Pan Active (Space)';
        canvas.style.cursor = 'grab';
        document.getElementById('statusText').textContent = 'Pan Mode - Click and drag to move view';
    } else {
        panBtn.style.background = '#3e3e42';
        panBtn.textContent = '🤚 Pan Mode (Space)';
        canvas.style.cursor = 'crosshair';
        document.getElementById('statusText').textContent = 'Cut Mode - Select a tool to continue';
    }
}

// Finish current cut
function finishCurrentCut() {
    if (cutMode.currentCut.length >= 2) {
        cutMode.isDrawing = false;
        saveCut();
        document.getElementById('finishCutBtn').classList.add('hidden');
    } else {
        alert('Need at least 2 points to save a cut');
    }
}

// Draw saved cuts
function drawSavedCuts() {
    cutMode.savedCuts.forEach(cut => {
        ctx.strokeStyle = '#ff6b35';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);

        if (cut.points && cut.points.length > 0) {
            ctx.beginPath();
            const first = worldToScreen(cut.points[0][0], cut.points[0][1]);
            ctx.moveTo(first.x, first.y);

            for (let i = 1; i < cut.points.length; i++) {
                const pt = worldToScreen(cut.points[i][0], cut.points[i][1]);
                ctx.lineTo(pt.x, pt.y);
            }

            if (cut.type === 'rectangle' || cut.type === 'polygon') {
                ctx.closePath();
            }

            ctx.stroke();
        }

        ctx.setLineDash([]);
    });
}

// Draw current cut
function drawCurrentCut() {
    if (cutMode.currentCut.length === 0) return;

    ctx.strokeStyle = '#ff3333';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);

    ctx.beginPath();
    const first = worldToScreen(cutMode.currentCut[0][0], cutMode.currentCut[0][1]);
    ctx.moveTo(first.x, first.y);

    for (let i = 1; i < cutMode.currentCut.length; i++) {
        const pt = worldToScreen(cutMode.currentCut[i][0], cutMode.currentCut[i][1]);
        ctx.lineTo(pt.x, pt.y);
    }

    if (cutMode.activeTool === 'rectangle' && cutMode.currentCut.length === 2) {
        // Complete rectangle
        const pt1 = worldToScreen(cutMode.currentCut[0][0], cutMode.currentCut[0][1]);
        const pt2 = worldToScreen(cutMode.currentCut[1][0], cutMode.currentCut[1][1]);
        ctx.clearRect(0, 0, 0, 0);
        ctx.beginPath();
        ctx.rect(pt1.x, pt1.y, pt2.x - pt1.x, pt2.y - pt1.y);
    }

    // Don't auto-close polygon while drawing - only close when user explicitly clicks near first point
    // This prevents the confusing auto-connection line from appearing

    ctx.stroke();
    ctx.setLineDash([]);
}

// Save cut
async function saveCut() {
    if (cutMode.currentCut.length === 0) {
        alert('No cut to save');
        return;
    }

    const cutData = {
        type: cutMode.activeTool,
        points: cutMode.currentCut
    };

    try {
        const result = await window.pywebview.api.save_cut_data(cutData);
        if (result.success) {
            console.log('Cut saved:', result.id);
            cutMode.currentCut = [];
            cutMode.isDrawing = false;
            await refreshCutList();
            render();
            document.getElementById('statusText').textContent = `Cut saved: ${result.id}`;
        } else {
            alert('Error saving cut: ' + result.error);
        }
    } catch (error) {
        console.error('Error saving cut:', error);
        alert('Error saving cut: ' + error.message);
    }
}

// Refresh cut list
async function refreshCutList() {
    try {
        const cuts = await window.pywebview.api.get_cut_list();
        cutMode.savedCuts = [];

        // Load full cut data for rendering
        for (const cut of cuts) {
            const fullData = await window.pywebview.api.get_cut_data(cut.id);
            if (fullData) {
                cutMode.savedCuts.push(fullData);
            }
        }

        const cutListItems = document.getElementById('cutListItems');
        const cutCount = document.getElementById('cutCount');
        cutCount.textContent = cuts.length;

        if (cuts.length === 0) {
            cutListItems.innerHTML = '<div style="color: #858585; font-size: 11px; text-align: center;">No cuts saved</div>';
        } else {
            cutListItems.innerHTML = cuts.map(cut => `
                <div class="cut-list-item">
                    <div>
                        <div style="color: #9cdcfe;">${cut.id}</div>
                        <div style="color: #858585; font-size: 10px;">${cut.type}</div>
                    </div>
                    <div class="cut-list-item-buttons">
                        <button class="cut-rename-btn" onclick="renameCut('${cut.id}')">Rename</button>
                        <button class="cut-delete-btn" onclick="deleteCut('${cut.id}')">Delete</button>
                    </div>
                </div>
            `).join('');
        }

        render();
    } catch (error) {
        console.error('Error refreshing cut list:', error);
    }
}

// Delete cut
async function deleteCut(cutId) {
    try {
        const result = await window.pywebview.api.delete_cut(cutId);
        if (result.success) {
            await refreshCutList();
            document.getElementById('statusText').textContent = `Deleted: ${cutId}`;
        } else {
            alert('Error deleting cut: ' + result.error);
        }
    } catch (error) {
        console.error('Error deleting cut:', error);
        alert('Error deleting cut: ' + error.message);
    }
}

// Rename cut
async function renameCut(cutId) {
    try {
        const newName = prompt('Enter new name (letters, numbers, and underscores only):', cutId);

        // User cancelled
        if (newName === null) return;

        // Empty name
        if (newName.trim() === '') {
            alert('Name cannot be empty');
            return;
        }

        // Validate format
        if (!/^[a-zA-Z0-9_]+$/.test(newName)) {
            alert('Invalid name format. Only letters, numbers, and underscores allowed.');
            return;
        }

        const result = await window.pywebview.api.rename_cut(cutId, newName);
        if (result.success) {
            await refreshCutList();
            document.getElementById('statusText').textContent = `Renamed: ${cutId} -> ${result.new_id}`;
        } else {
            alert('Error renaming cut: ' + result.error);
        }
    } catch (error) {
        console.error('Error renaming cut:', error);
        alert('Error renaming cut: ' + error.message);
    }
}

// Clear all cuts
async function clearAllCuts() {
    if (!confirm('Delete all cuts?')) return;

    try {
        const cuts = await window.pywebview.api.get_cut_list();
        for (const cut of cuts) {
            await window.pywebview.api.delete_cut(cut.id);
        }
        await refreshCutList();
        document.getElementById('statusText').textContent = 'All cuts deleted';
    } catch (error) {
        console.error('Error clearing cuts:', error);
        alert('Error clearing cuts: ' + error.message);
    }
}

// Get all snap points from saved cuts and current cut
function getAllSnapPoints() {
    const snapPoints = [];

    // Add points from all saved cuts
    cutMode.savedCuts.forEach(cut => {
        if (cut.points && cut.points.length > 0) {
            cut.points.forEach(point => {
                snapPoints.push({
                    x: point[0],
                    y: point[1],
                    source: 'saved'
                });
            });
        }
    });

    // Add points from current cut (except the last one being drawn)
    if (cutMode.isDrawing && cutMode.currentCut.length > 0) {
        cutMode.currentCut.forEach(point => {
            snapPoints.push({
                x: point[0],
                y: point[1],
                source: 'current'
            });
        });
    }

    return snapPoints;
}

// Find nearest snap point to screen coordinates
function findNearestSnapPoint(screenX, screenY) {
    const snapPoints = getAllSnapPoints();
    let nearestPoint = null;
    let minDistance = SNAP_DISTANCE;

    snapPoints.forEach(point => {
        const screenPoint = worldToScreen(point.x, point.y);
        const distance = Math.sqrt(
            Math.pow(screenPoint.x - screenX, 2) +
            Math.pow(screenPoint.y - screenY, 2)
        );

        if (distance < minDistance) {
            minDistance = distance;
            nearestPoint = {
                x: point.x,
                y: point.y,
                screenX: screenPoint.x,
                screenY: screenPoint.y,
                source: point.source
            };
        }
    });

    return nearestPoint;
}

// Draw snap point indicator
function drawSnapIndicator(snapPoint) {
    if (!snapPoint) return;

    // Draw highlight circle around snap point
    ctx.strokeStyle = '#00ff00';
    ctx.fillStyle = 'rgba(0, 255, 0, 0.2)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(snapPoint.screenX, snapPoint.screenY, 8, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();

    // Draw small center dot
    ctx.fillStyle = '#00ff00';
    ctx.beginPath();
    ctx.arc(snapPoint.screenX, snapPoint.screenY, 3, 0, 2 * Math.PI);
    ctx.fill();
}

// Handle cut mouse down
function handleCutMouseDown(e) {
    // Use snap point if available, otherwise use cursor position
    let worldPos;
    if (cutMode.snapPoint) {
        worldPos = { x: cutMode.snapPoint.x, y: cutMode.snapPoint.y };
    } else {
        worldPos = screenToWorld(e.offsetX, e.offsetY);
    }

    switch (cutMode.activeTool) {
        case 'line':
            if (!cutMode.isDrawing) {
                // Start line
                cutMode.isDrawing = true;
                cutMode.currentCut = [[worldPos.x, worldPos.y]];
                document.getElementById('statusText').textContent = 'Click end point';
            } else {
                // Finish line - replace preview point instead of pushing
                cutMode.currentCut[1] = [worldPos.x, worldPos.y];
                cutMode.isDrawing = false;
                saveCut();
            }
            break;

        case 'rectangle':
            if (!cutMode.isDrawing) {
                // Start rectangle - first corner
                cutMode.isDrawing = true;
                cutMode.currentCut = [[worldPos.x, worldPos.y]];
                document.getElementById('statusText').textContent = 'Click opposite corner';
            } else {
                // Finish rectangle - second corner
                const [x1, y1] = cutMode.currentCut[0];
                cutMode.currentCut = [
                    [x1, y1],
                    [worldPos.x, y1],
                    [worldPos.x, worldPos.y],
                    [x1, worldPos.y]
                ];
                cutMode.isDrawing = false;
                saveCut();
            }
            break;

        case 'polyline':
            if (!cutMode.isDrawing) {
                cutMode.isDrawing = true;
                cutMode.currentCut = [[worldPos.x, worldPos.y]];
                document.getElementById('finishCutBtn').classList.remove('hidden');
                document.getElementById('statusText').textContent = 'Click points, then click near last point to finish';
            } else {
                // Check if clicking near the last point (snap distance: 15px in screen space)
                if (cutMode.currentCut.length >= 2) {
                    const lastPoint = worldToScreen(cutMode.currentCut[cutMode.currentCut.length - 1][0], cutMode.currentCut[cutMode.currentCut.length - 1][1]);
                    const currentPoint = { x: e.offsetX, y: e.offsetY };
                    const distance = Math.sqrt(
                        Math.pow(lastPoint.x - currentPoint.x, 2) +
                        Math.pow(lastPoint.y - currentPoint.y, 2)
                    );

                    if (distance < SNAP_DISTANCE) {
                        // Finish polyline
                        finishCurrentCut();
                        document.getElementById('statusText').textContent = 'Polyline finished and saved';
                        break;
                    }
                }

                cutMode.currentCut.push([worldPos.x, worldPos.y]);
                document.getElementById('statusText').textContent = `${cutMode.currentCut.length} points - Click near last point to finish`;
            }
            render();
            break;

        case 'polygon':
            if (!cutMode.isDrawing) {
                cutMode.isDrawing = true;
                cutMode.currentCut = [[worldPos.x, worldPos.y]];
                document.getElementById('statusText').textContent = 'Click points to draw polygon, click near start to close';
            } else {
                // Check if clicking near the first point (snap distance: 15px in screen space)
                if (cutMode.currentCut.length >= 3) {
                    const firstPoint = worldToScreen(cutMode.currentCut[0][0], cutMode.currentCut[0][1]);
                    const currentPoint = { x: e.offsetX, y: e.offsetY };
                    const distance = Math.sqrt(
                        Math.pow(firstPoint.x - currentPoint.x, 2) +
                        Math.pow(firstPoint.y - currentPoint.y, 2)
                    );

                    if (distance < SNAP_DISTANCE) {
                        // Close the polygon by connecting to first point
                        cutMode.isDrawing = false;
                        saveCut();
                        document.getElementById('statusText').textContent = 'Polygon closed and saved';
                        break;
                    }
                }

                cutMode.currentCut.push([worldPos.x, worldPos.y]);
                document.getElementById('statusText').textContent = `${cutMode.currentCut.length} points - Click near start to close`;
            }
            render();
            break;
    }

    render();
}

// Handle cut mouse move
function handleCutMouseMove(e) {
    // Find nearest snap point
    cutMode.snapPoint = findNearestSnapPoint(e.offsetX, e.offsetY);

    // Use snap point if available, otherwise use cursor position
    let worldPos;
    let targetX = e.offsetX;
    let targetY = e.offsetY;

    if (cutMode.snapPoint) {
        worldPos = { x: cutMode.snapPoint.x, y: cutMode.snapPoint.y };
        targetX = cutMode.snapPoint.screenX;
        targetY = cutMode.snapPoint.screenY;
    } else {
        worldPos = screenToWorld(e.offsetX, e.offsetY);
    }

    switch (cutMode.activeTool) {
        case 'line':
            // Show snap indicator even before drawing starts
            if (!cutMode.isDrawing) {
                render();
                drawSnapIndicator(cutMode.snapPoint);
            }
            // Show preview line for line tool
            else if (cutMode.isDrawing && cutMode.currentCut.length === 1) {
                render();
                const startScreen = worldToScreen(cutMode.currentCut[0][0], cutMode.currentCut[0][1]);

                // Draw snap indicator
                drawSnapIndicator(cutMode.snapPoint);

                // Draw preview line
                ctx.strokeStyle = '#ff3333';
                ctx.lineWidth = 1;
                ctx.setLineDash([3, 3]);
                ctx.beginPath();
                ctx.moveTo(startScreen.x, startScreen.y);
                ctx.lineTo(targetX, targetY);
                ctx.stroke();
                ctx.setLineDash([]);
            }
            break;

        case 'rectangle':
            // Show snap indicator even before drawing starts
            if (!cutMode.isDrawing) {
                render();
                drawSnapIndicator(cutMode.snapPoint);
            }
            else if (cutMode.isDrawing && cutMode.currentCut.length === 1) {
                // Show preview rectangle
                const [x1, y1] = cutMode.currentCut[0];
                const tempRect = [
                    [x1, y1],
                    [worldPos.x, y1],
                    [worldPos.x, worldPos.y],
                    [x1, worldPos.y]
                ];

                // Draw preview
                render();

                // Draw snap indicator
                drawSnapIndicator(cutMode.snapPoint);

                ctx.strokeStyle = '#ff3333';
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                const pt1 = worldToScreen(tempRect[0][0], tempRect[0][1]);
                ctx.moveTo(pt1.x, pt1.y);
                for (let i = 1; i < tempRect.length; i++) {
                    const pt = worldToScreen(tempRect[i][0], tempRect[i][1]);
                    ctx.lineTo(pt.x, pt.y);
                }
                ctx.closePath();
                ctx.stroke();
                ctx.setLineDash([]);
            }
            break;

        case 'polyline':
            // Show preview line to cursor
            render();
            // Show snap indicator even before drawing starts
            if (!cutMode.isDrawing) {
                drawSnapIndicator(cutMode.snapPoint);
            }
            else if (cutMode.isDrawing && cutMode.currentCut.length > 0) {
                const last = cutMode.currentCut[cutMode.currentCut.length - 1];
                const lastScreen = worldToScreen(last[0], last[1]);

                // Check if near last point for finish preview
                let isNearLastPoint = false;
                if (cutMode.currentCut.length >= 2) {
                    const distance = Math.sqrt(
                        Math.pow(lastScreen.x - e.offsetX, 2) +
                        Math.pow(lastScreen.y - e.offsetY, 2)
                    );

                    if (distance < SNAP_DISTANCE) {
                        isNearLastPoint = true;
                        targetX = lastScreen.x;
                        targetY = lastScreen.y;

                        // Draw special highlight for polyline finish
                        ctx.strokeStyle = '#00ff00';
                        ctx.fillStyle = 'rgba(0, 255, 0, 0.2)';
                        ctx.lineWidth = 2;
                        ctx.beginPath();
                        ctx.arc(lastScreen.x, lastScreen.y, 10, 0, 2 * Math.PI);
                        ctx.fill();
                        ctx.stroke();
                    }
                }

                // Draw snap indicator (if not near last point)
                if (!isNearLastPoint) {
                    drawSnapIndicator(cutMode.snapPoint);
                }

                // Draw preview line
                ctx.strokeStyle = '#ff3333';
                ctx.lineWidth = 1;
                ctx.setLineDash([3, 3]);
                ctx.beginPath();
                ctx.moveTo(lastScreen.x, lastScreen.y);
                ctx.lineTo(targetX, targetY);
                ctx.stroke();
                ctx.setLineDash([]);
            }
            break;

        case 'polygon':
            // Show preview line to cursor, snap to first point if close
            render();
            // Show snap indicator even before drawing starts
            if (!cutMode.isDrawing) {
                drawSnapIndicator(cutMode.snapPoint);
            }
            else if (cutMode.isDrawing && cutMode.currentCut.length > 0) {
                const last = cutMode.currentCut[cutMode.currentCut.length - 1];
                const lastScreen = worldToScreen(last[0], last[1]);

                // Check if near first point for snap preview (polygon closing)
                let isClosingPolygon = false;
                if (cutMode.currentCut.length >= 3) {
                    const firstPoint = worldToScreen(cutMode.currentCut[0][0], cutMode.currentCut[0][1]);
                    const distance = Math.sqrt(
                        Math.pow(firstPoint.x - e.offsetX, 2) +
                        Math.pow(firstPoint.y - e.offsetY, 2)
                    );

                    if (distance < SNAP_DISTANCE) {
                        isClosingPolygon = true;
                        targetX = firstPoint.x;
                        targetY = firstPoint.y;

                        // Draw special highlight for polygon closing
                        ctx.strokeStyle = '#ffff00';
                        ctx.fillStyle = 'rgba(255, 255, 0, 0.2)';
                        ctx.lineWidth = 2;
                        ctx.beginPath();
                        ctx.arc(firstPoint.x, firstPoint.y, 10, 0, 2 * Math.PI);
                        ctx.fill();
                        ctx.stroke();
                    }
                }

                // Draw snap indicator (if not closing polygon)
                if (!isClosingPolygon) {
                    drawSnapIndicator(cutMode.snapPoint);
                }

                // Draw preview line
                ctx.strokeStyle = '#ff3333';
                ctx.lineWidth = 1;
                ctx.setLineDash([3, 3]);
                ctx.beginPath();
                ctx.moveTo(lastScreen.x, lastScreen.y);
                ctx.lineTo(targetX, targetY);
                ctx.stroke();
                ctx.setLineDash([]);
            }
            break;
    }
}
