/**
 * CareerGraph AI - Client Side Graph Visualization & Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    initInteractiveGraph();
});

/**
 * Visualizes Graph Subgraph Data using SVG Elements dynamically
 */
function initInteractiveGraph() {
    const container = document.getElementById('careerGraphVisualizer');
    if (!container) return;

    // Retrieve raw graph data passed via data attribute
    const rawData = container.getAttribute('data-graph');
    if (!rawData) return;

    try {
        const graphData = JSON.parse(rawData);
        renderGraphSVG(container, graphData);
    } catch (e) {
        console.error("Failed to parse graph visualization JSON:", e);
    }
}

function renderGraphSVG(container, data) {
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 380;
    const centerX = width / 2;
    const centerY = height / 2;

    const candidateName = data.candidate_name || 'Candidate';
    const skills = (data.skills || []).slice(0, 6);
    const projects = (data.projects || []).slice(0, 4);
    const roles = (data.roles || []).slice(0, 4);
    const companies = (data.companies || []).slice(0, 3);

    let svgHtml = `<svg width="100%" height="100%" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">`;

    // Central Candidate Node
    const nodes = [
        { id: 'candidate', name: candidateName, type: 'candidate', x: centerX, y: centerY, color: '#38bdf8', r: 28 }
    ];

    // Helper for laying nodes out in orbital rings
    const addRingNodes = (items, radius, color, nodeType, startAngle = 0) => {
        const total = items.length;
        if (total === 0) return;
        const angleStep = (2 * Math.PI) / total;

        items.forEach((item, index) => {
            if (!item.name) return;
            const angle = startAngle + index * angleStep;
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);
            nodes.push({ id: item.id || `${nodeType}_${index}`, name: item.name, type: nodeType, x, y, color, r: 18 });
        });
    };

    // Orbit 1: Skills (Emerald)
    addRingNodes(skills, 110, '#10b981', 'skill', 0);

    // Orbit 2: Projects (Amber)
    addRingNodes(projects, 170, '#f59e0b', 'project', Math.PI / 4);

    // Orbit 3: Job Roles (Indigo)
    addRingNodes(roles, 230, '#6366f1', 'role', Math.PI / 6);

    // Orbit 4: Companies (Rose)
    addRingNodes(companies, 280, '#f43f5e', 'company', Math.PI / 3);

    // Draw Edges / Links connecting Central candidate to surrounding nodes
    nodes.forEach(node => {
        if (node.id !== 'candidate') {
            svgHtml += `<line x1="${centerX}" y1="${centerY}" x2="${node.x}" y2="${node.y}" stroke="#334155" stroke-width="2" stroke-dasharray="4" />`;
        }
    });

    // Render Nodes
    nodes.forEach(node => {
        svgHtml += `
            <g class="graph-node" transform="translate(${node.x}, ${node.y})">
                <circle r="${node.r}" fill="${node.color}" opacity="0.9" stroke="#1e293b" stroke-width="3"/>
                <text y="${node.r + 14}" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="600">${escapeXml(node.name)}</text>
            </g>
        `;
    });

    svgHtml += `</svg>`;
    container.innerHTML = svgHtml;
}

function escapeXml(unsafe) {
    return unsafe.replace(/[<>&'"]/g, (c) => {
        switch (c) {
            case '<': return '&lt;';
            case '>': return '&gt;';
            case '&': return '&amp;';
            case '\'': return '&apos;';
            case '"': return '&quot;';
        }
    });
}