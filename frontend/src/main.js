/**
 * Main entry point for Master of Magic Wiki 3D Graph Explorer.
 */

(function() {
    'use strict';

    // State
    let currentNode = null;
    let graphData = null;

    // DOM elements
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const typeFilter = document.getElementById('type-filter');
    const realmFilter = document.getElementById('realm-filter');
    const detailPanel = document.getElementById('detail-panel');
    const closePanel = document.getElementById('close-panel');
    const detailTitle = document.getElementById('detail-title');
    const detailMeta = document.getElementById('detail-meta');
    const detailBody = document.getElementById('detail-body');
    const detailRelated = document.getElementById('detail-related');
    const graphContainer = document.getElementById('graph-container');

    /**
     * Initialize the application.
     */
    async function init() {
        console.log('Initializing MoM Wiki Graph Explorer...');

        // Show loading state
        graphContainer.innerHTML = '<div class="loading"></div>';

        // Load data first
        await loadGraphData();

        // Set up event listeners
        setupEventListeners();

        console.log('Application initialized');
    }

    /**
     * Load graph data from API.
     */
    async function loadGraphData() {
        try {
            console.log('Fetching graph data...');
            graphData = await API.getGraph({ limit: 500 });
            console.log('Graph data received:', graphData);

            // Clear loading and initialize graph
            graphContainer.innerHTML = '';
            Graph.init('#graph-container');

            // Build search index
            console.log('Building search index...');
            Search.buildIndex(graphData.nodes);

            // Display graph
            console.log('Setting graph data...');
            Graph.setData(graphData);
            console.log('Graph loaded successfully');
        } catch (error) {
            console.error('Failed to load graph data:', error);
            console.error('Error stack:', error.stack);
            graphContainer.innerHTML = `
                <div class="loading" style="color: #FF6B6B;">
                    Failed to load data: ${error.message}
                </div>
            `;

            // Load sample data for demo
            loadSampleData();
        }
    }

    /**
     * Load sample data for demo/offline use.
     */
    function loadSampleData() {
        console.log('Loading sample data for demo...');

        // Initialize graph if not already done
        graphContainer.innerHTML = '';
        Graph.init('#graph-container');

        const sampleData = {
            nodes: [
                { id: '1', name: 'Fireball', type: 'spell', realm: 'Chaos', summary: 'A destructive Chaos spell' },
                { id: '2', name: 'Healing', type: 'spell', realm: 'Life', summary: 'A restorative Life spell' },
                { id: '3', name: 'Web', type: 'spell', realm: 'Nature', summary: 'Immobilizes enemy units' },
                { id: '4', name: 'Phantom Warriors', type: 'spell', realm: 'Sorcery', summary: 'Summons illusory fighters' },
                { id: '5', name: 'Black Sleep', type: 'spell', realm: 'Death', summary: 'Puts enemies to sleep' },
                { id: '6', name: 'Magic Spirit', type: 'spell', realm: 'Arcane', summary: 'Basic summoned creature' },
                { id: '7', name: 'High Elf Spearmen', type: 'unit', summary: 'Basic High Elf infantry' },
                { id: '8', name: 'Merlin', type: 'wizard', realm: 'Arcane', summary: 'Legendary wizard' }
            ],
            edges: [
                { source: '1', target: '4', type: 'counter' },
                { source: '2', target: '5', type: 'counter' },
                { source: '3', target: '7', type: 'synergy' },
                { source: '6', target: '8', type: 'belongs_to' }
            ]
        };

        graphData = sampleData;
        Search.buildIndex(sampleData.nodes);
        Graph.setData(sampleData);
    }

    /**
     * Set up event listeners.
     */
    function setupEventListeners() {
        // Search
        searchBtn.addEventListener('click', handleSearch);
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSearch();
        });

        // Filters
        typeFilter.addEventListener('change', handleFilterChange);
        realmFilter.addEventListener('change', handleFilterChange);

        // Detail panel
        closePanel.addEventListener('click', hideDetailPanel);

        // Node selection (from graph)
        window.addEventListener('nodeSelected', (e) => {
            showNodeDetail(e.detail);
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                hideDetailPanel();
                Graph.clearHighlights();
            }
        });
    }

    /**
     * Handle search.
     */
    function handleSearch() {
        const query = searchInput.value.trim();

        if (!query) {
            Graph.clearHighlights();
            return;
        }

        const matchingIds = Search.getMatchingIds(query);
        Graph.highlightNodes(matchingIds);

        console.log(`Search "${query}": ${matchingIds.size} results`);
    }

    /**
     * Handle filter changes.
     */
    function handleFilterChange() {
        const type = typeFilter.value;
        const realm = realmFilter.value;

        if (!type && !realm) {
            Graph.resetFilter();
        } else {
            Graph.filterNodes({ type, realm });
        }
    }

    /**
     * Show node detail in panel.
     * @param {Object} node - Node to display
     */
    async function showNodeDetail(node) {
        currentNode = node;

        // Update panel content
        detailTitle.textContent = node.name;

        // Build meta tags
        detailMeta.innerHTML = '';

        const typeTag = document.createElement('span');
        typeTag.className = 'tag';
        typeTag.textContent = node.type;
        detailMeta.appendChild(typeTag);

        if (node.realm) {
            const realmTag = document.createElement('span');
            realmTag.className = `tag realm-${node.realm.toLowerCase()}`;
            realmTag.textContent = node.realm;
            detailMeta.appendChild(realmTag);
        }

        // Summary/content
        detailBody.innerHTML = `<p>${node.summary || 'No description available.'}</p>`;

        // Show panel
        detailPanel.classList.remove('hidden');

        // Load full details from API
        try {
            const fullNode = await API.getNode(node.id);
            if (fullNode.content) {
                const hasMarked = typeof marked !== 'undefined' && marked.parse;
                detailBody.innerHTML = hasMarked ? marked.parse(fullNode.content) : `<p>${fullNode.content}</p>`;
            }

            // Load related nodes
            loadRelatedNodes(node.id);
        } catch (error) {
            console.log('Could not load full node details:', error);
        }
    }

    /**
     * Load and display related nodes.
     * @param {string} nodeId - Node ID
     */
    async function loadRelatedNodes(nodeId) {
        detailRelated.innerHTML = '<h3>Related</h3><p>Loading...</p>';

        try {
            const related = await API.getRelatedNodes(nodeId);

            if (related.related && related.related.length > 0) {
                const list = document.createElement('ul');

                related.related.forEach(r => {
                    const li = document.createElement('li');
                    li.textContent = `${r.node.name} (${r.relationship.type})`;
                    li.dataset.nodeId = r.node.id;
                    li.addEventListener('click', async () => {
                        const fullNode = await API.getNode(r.node.id);
                        showNodeDetail(fullNode);
                    });
                    list.appendChild(li);
                });

                detailRelated.innerHTML = '<h3>Related</h3>';
                detailRelated.appendChild(list);
            } else {
                detailRelated.innerHTML = '<h3>Related</h3><p>No related nodes found.</p>';
            }
        } catch (error) {
            detailRelated.innerHTML = '<h3>Related</h3><p>Could not load related nodes.</p>';
        }
    }

    /**
     * Hide detail panel.
     */
    function hideDetailPanel() {
        detailPanel.classList.add('hidden');
        currentNode = null;
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
