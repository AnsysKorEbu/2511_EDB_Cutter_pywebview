/**
 * Polygon Selection Tool
 */
class PolygonSelector {
    constructor(renderer, uiController) {
        this.renderer = renderer;
        this.uiController = uiController;
        this.viewport = renderer.viewport;
        this.selectionLayer = renderer.selectionLayer;

        this.points = [];  // Points in input units (mm)
        this.isDrawing = false;

        this.previewGraphics = new PIXI.Graphics();
        this.vertexMarkers = [];

        this.selectionLayer.addChild(this.previewGraphics);

        this.setupKeyboardShortcuts();
    }

    startDrawing() {
        if (this.isDrawing) {
            this.uiController.showMessage('이미 그리기 모드입니다', 'warning');
            return;
        }

        this.isDrawing = true;
        this.points = [];
        this.clearPreview();

        this.uiController.showMessage('클릭하여 점 추가, 우클릭으로 완료, ESC로 취소', 'info');
        this.uiController.updateCoordinatesList(this.points);

        // Disable viewport drag while drawing
        this.viewport.pause = true;

        // Setup click handler
        this.clickHandler = (event) => {
            if (!this.isDrawing) return;

            const worldPos = this.viewport.toWorld(event.data.global);
            this.addPoint(worldPos.x, worldPos.y);
        };

        // Setup right-click handler
        this.rightClickHandler = (event) => {
            if (!this.isDrawing) return;
            event.preventDefault();
            this.finishDrawing();
        };

        this.viewport.on('click', this.clickHandler);
        this.viewport.on('rightclick', this.rightClickHandler);
    }

    addPoint(x, y) {
        this.points.push([x, y]);

        this.addVertexMarker(x, y);
        this.updatePreview();
        this.uiController.updateCoordinatesList(this.points);

        console.log(`Added point ${this.points.length}: (${x}, ${y})`);
    }

    addVertexMarker(x, y) {
        const marker = new PIXI.Graphics();

        // Draw vertex as circle
        marker.beginFill(0x00FF00, 1);
        marker.drawCircle(x, y, 0.0002);  // Radius in input units
        marker.endFill();

        // Add outline
        marker.lineStyle(0.0001, 0xFFFFFF, 1);
        marker.drawCircle(x, y, 0.0002);

        this.selectionLayer.addChild(marker);
        this.vertexMarkers.push(marker);
    }

    updatePreview() {
        this.previewGraphics.clear();

        if (this.points.length < 1) return;

        // Draw lines connecting points
        this.previewGraphics.lineStyle(0.0002, 0x00FF00, 1);

        if (this.points.length === 1) {
            // Just show the first point (already shown by marker)
            return;
        }

        // Draw polygon outline
        this.previewGraphics.moveTo(this.points[0][0], this.points[0][1]);

        for (let i = 1; i < this.points.length; i++) {
            this.previewGraphics.lineTo(this.points[i][0], this.points[i][1]);
        }

        // Draw line back to first point (preview closure)
        if (this.points.length >= 2) {
            this.previewGraphics.lineTo(this.points[0][0], this.points[0][1]);
        }
    }

    finishDrawing() {
        if (this.points.length < 3) {
            this.uiController.showMessage('최소 3개의 점이 필요합니다', 'warning');
            return;
        }

        this.isDrawing = false;

        // Remove event handlers
        this.viewport.off('click', this.clickHandler);
        this.viewport.off('rightclick', this.rightClickHandler);

        // Re-enable viewport drag
        this.viewport.pause = false;

        // Draw final polygon
        this.drawFinalPolygon();

        // Enable cut button
        this.uiController.enableCutButton();
        this.uiController.showMessage(`다각형 완성: ${this.points.length}개 점`, 'success');

        console.log(`Polygon finished with ${this.points.length} points`);
    }

    drawFinalPolygon() {
        this.previewGraphics.clear();

        // Draw filled polygon
        this.previewGraphics.lineStyle(0.0003, 0x00FF00, 1);
        this.previewGraphics.beginFill(0x00FF00, 0.2);

        this.previewGraphics.moveTo(this.points[0][0], this.points[0][1]);

        for (let i = 1; i < this.points.length; i++) {
            this.previewGraphics.lineTo(this.points[i][0], this.points[i][1]);
        }

        this.previewGraphics.closePath();
        this.previewGraphics.endFill();
    }

    cancelDrawing() {
        if (this.isDrawing) {
            this.viewport.off('click', this.clickHandler);
            this.viewport.off('rightclick', this.rightClickHandler);
            this.viewport.pause = false;
            this.uiController.showMessage('그리기 취소됨', 'info');
        }

        this.isDrawing = false;
        this.points = [];
        this.clearPreview();
        this.uiController.updateCoordinatesList(this.points);
    }

    clearPreview() {
        this.previewGraphics.clear();

        this.vertexMarkers.forEach(marker => marker.destroy());
        this.vertexMarkers = [];
    }

    getPointsInUM() {
        // Convert points to micrometers
        return this.points.map(pt => [
            pt[0] * CONFIG.scale,
            pt[1] * CONFIG.scale
        ]);
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.isDrawing) {
                this.cancelDrawing();
            }
        });
    }

    async executeCut() {
        if (this.points.length < 3) {
            this.uiController.showMessage('선택 영역이 없습니다', 'warning');
            return;
        }

        const coordsUM = this.getPointsInUM();

        this.uiController.showMessage('커팅 중...', 'info');

        try {
            const result = await eel.cut_region(coordsUM)();

            if (result.success) {
                this.uiController.showMessage(result.message, 'success');
                console.log('Cut result:', result);
            } else {
                this.uiController.showMessage('커팅 실패: ' + result.message, 'error');
            }
        } catch (error) {
            console.error('Error executing cut:', error);
            this.uiController.showMessage('커팅 오류: ' + error.message, 'error');
        }
    }
}
