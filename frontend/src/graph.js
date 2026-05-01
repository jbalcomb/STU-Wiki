/**
 * 3D Force Graph visualization for Master of Magic Wiki.
 */

const Graph = {
    graph: null,
    container: null,
    data: { nodes: [], edges: [] },
    highlightedNodes: new Set(),

    // Color schemes
    realmColors: {
        'Life': '#FFD700',
        'Death': '#800080',
        'Nature': '#228B22',
        'Sorcery': '#4169E1',
        'Chaos': '#FF4500',
        'Arcane': '#C0C0C0'
    },

    typeColors: {
        'spell': '#FF6B6B',
        'unit': '#4ECDC4',
        'item': '#45B7D1',
        'wizard': '#96CEB4',
        'ability': '#FFEAA7',
        'realm': '#DDA0DD',
        'concept': '#98D8C8',
        'page': '#A8E6CF'
    },

    /**
     * Initialize the graph in a container.
     * @param {string|HTMLElement} container - Container element or selector
     */
    init(container) {
        if (typeof container === 'string') {
            this.container = document.querySelector(container);
        } else {
            this.container = container;
        }

        if (!this.container) {
            console.error('Graph container not found');
            return;
        }

        this.graph = ForceGraph3D()(this.container)
            .backgroundColor('#1a1a2e')
            .nodeLabel(node => `${node.name} (${node.type})`)
            .nodeColor(node => this.getNodeColor(node))
            .nodeOpacity(0.9)
            .nodeResolution(16)
            .nodeVal(node => node.size || 1)
            .linkColor(() => 'rgba(255, 255, 255, 0.2)')
            .linkOpacity(0.3)
            .linkWidth(1)
            .linkDirectionalParticles(2)
            .linkDirectionalParticleWidth(1)
            .linkDirectionalParticleColor(() => 'rgba(255, 255, 255, 0.4)')
            .onNodeClick(node => this.onNodeClick(node))
            .onNodeHover(node => this.onNodeHover(node))
            .enableNavigationControls(true)
            .enableNodeDrag(true);

        // Handle window resize
        window.addEventListener('resize', () => this.resize());
    },

    /**
     * Get color for a node based on realm or type.
     * @param {Object} node - Node object
     * @returns {string} Color hex code
     */
    getNodeColor(node) {
        // Highlight color for search results
        if (this.highlightedNodes.has(node.id)) {
            return '#FFFFFF';
        }

        // Use realm color if available
        if (node.realm && this.realmColors[node.realm]) {
            return this.realmColors[node.realm];
        }

        // Fall back to type color
        return this.typeColors[node.type] || '#888888';
    },

    /**
     * Load and display graph data.
     * @param {Object} graphData - { nodes, edges }
     */
    setData(graphData) {
        this.data = graphData;

        // Transform for force-graph
        const nodes = graphData.nodes.map(n => ({
            id: n.id,
            name: n.name,
            type: n.type,
            realm: n.realm,
            summary: n.summary,
            color: n.color || this.getNodeColor(n),
            size: n.size || 1
        }));

        const links = graphData.edges.map(e => ({
            source: e.source,
            target: e.target,
            type: e.type
        }));

        this.graph.graphData({ nodes, links });

        // Update stats
        this.updateStats(nodes.length, links.length);
    },

    /**
     * Update the footer stats display.
     * @param {number} nodeCount - Number of nodes
     * @param {number} edgeCount - Number of edges
     */
    updateStats(nodeCount, edgeCount) {
        const nodeCountEl = document.getElementById('node-count');
        const edgeCountEl = document.getElementById('edge-count');

        if (nodeCountEl) {
            nodeCountEl.textContent = `${nodeCount} nodes`;
        }
        if (edgeCountEl) {
            edgeCountEl.textContent = `${edgeCount} edges`;
        }
    },

    /**
     * Handle node click - show detail panel.
     * @param {Object} node - Clicked node
     */
    onNodeClick(node) {
        if (!node) return;

        // Emit custom event for main.js to handle
        const event = new CustomEvent('nodeSelected', { detail: node });
        window.dispatchEvent(event);

        // Zoom to node
        this.zoomToNode(node);
    },

    /**
     * Handle node hover.
     * @param {Object} node - Hovered node
     */
    onNodeHover(node) {
        this.container.style.cursor = node ? 'pointer' : 'default';
    },

    /**
     * Zoom and focus on a specific node.
     * @param {Object} node - Node to focus on
     */
    zoomToNode(node) {
        if (!node) return;

        const distance = 200;
        const distRatio = 1 + distance / Math.hypot(node.x || 0, node.y || 0, node.z || 0);

        this.graph.cameraPosition(
            { x: (node.x || 0) * distRatio, y: (node.y || 0) * distRatio, z: (node.z || 0) * distRatio },
            node,
            1000
        );
    },

    /**
     * Highlight nodes matching search results.
     * @param {Set<string>} nodeIds - Set of node IDs to highlight
     */
    highlightNodes(nodeIds) {
        this.highlightedNodes = nodeIds;

        // Re-render to apply new colors
        this.graph.nodeColor(node => this.getNodeColor(node));

        // If there's a single result, zoom to it
        if (nodeIds.size === 1) {
            const nodeId = [...nodeIds][0];
            const node = this.data.nodes.find(n => n.id === nodeId);
            if (node) {
                this.zoomToNode(node);
            }
        }
    },

    /**
     * Clear all highlights.
     */
    clearHighlights() {
        this.highlightedNodes = new Set();
        this.graph.nodeColor(node => this.getNodeColor(node));
    },

    /**
     * Filter visible nodes by type and/or realm.
     * @param {Object} filters - { type, realm }
     */
    filterNodes(filters) {
        const { nodes, edges } = this.data;

        let filteredNodes = nodes;

        if (filters.type) {
            filteredNodes = filteredNodes.filter(n => n.type === filters.type);
        }
        if (filters.realm) {
            filteredNodes = filteredNodes.filter(n => n.realm === filters.realm);
        }

        const nodeIds = new Set(filteredNodes.map(n => n.id));

        // Filter edges to only include those between visible nodes
        const filteredEdges = edges.filter(
            e => nodeIds.has(e.source) && nodeIds.has(e.target)
        );

        this.graph.graphData({
            nodes: filteredNodes,
            links: filteredEdges
        });

        this.updateStats(filteredNodes.length, filteredEdges.length);
    },

    /**
     * Reset to show all nodes.
     */
    resetFilter() {
        this.setData(this.data);
    },

    /**
     * Handle window resize.
     */
    resize() {
        if (this.graph && this.container) {
            this.graph.width(this.container.offsetWidth);
            this.graph.height(this.container.offsetHeight);
        }
    },

    /**
     * Center and reset camera position.
     */
    centerCamera() {
        this.graph.cameraPosition({ x: 0, y: 0, z: 500 }, { x: 0, y: 0, z: 0 }, 1000);
    }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Graph;
}
