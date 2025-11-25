let startX = 0;
let startY = 0;
let isDrawing = false;

// Function called by Python when the first click hits
window.startGhostDrawing = (x, y) => {
    startX = x;
    startY = y;
    isDrawing = true;
    
    const rect = document.getElementById('ghost_rect');
    if (rect) {
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', '0');
        rect.setAttribute('height', '0');
        rect.setAttribute('visibility', 'visible');
    } else {
        console.warn("Ghost rect not found in DOM");
    }
};

// Function called by Python when Stopping
window.stopGhostDrawing = () => {
    isDrawing = false;
    const rect = document.getElementById('ghost_rect');
    if (rect) rect.setAttribute('visibility', 'hidden');
};

// Global mouse move listener
document.addEventListener('mousemove', (e) => {
    if (!isDrawing) return;

    // 1. Find the rectangle by its unique ID
    const rect = document.getElementById('ghost_rect');
    if (!rect) return;

    // 2. Get the parent SVG directly from the element (More robust)
    const svg = rect.ownerSVGElement;
    if (!svg) return;

    try {
        // 3. Coordinate conversion math (Screen -> SVG)
        // This automatically corrects for zoom, scroll, and window position
        const point = svg.createSVGPoint();
        point.x = e.clientX;
        point.y = e.clientY;
        const cursor = point.matrixTransform(svg.getScreenCTM().inverse());

        // 4. Calculate geometry
        const currentX = cursor.x;
        const currentY = cursor.y;
        
        const width = Math.abs(currentX - startX);
        const height = Math.abs(currentY - startY);
        const x = Math.min(startX, currentX);
        const y = Math.min(startY, currentY);

        // 5. Update visual attributes
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', width);
        rect.setAttribute('height', height);
        
    } catch (err) {
        console.error("Error drawing ghost rect:", err);
    }
});
