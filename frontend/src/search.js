/**
 * Client-side search using Lunr.js for Master of Magic Wiki.
 */

const Search = {
    index: null,
    documents: {},

    /**
     * Build search index from graph data.
     * @param {Array} nodes - Array of node objects
     */
    buildIndex(nodes) {
        this.documents = {};

        this.index = lunr(function() {
            this.ref('id');
            this.field('name', { boost: 10 });
            this.field('type', { boost: 5 });
            this.field('realm', { boost: 5 });
            this.field('summary');

            nodes.forEach(node => {
                this.add({
                    id: node.id,
                    name: node.name,
                    type: node.type,
                    realm: node.realm || '',
                    summary: node.summary || ''
                });
            });
        });

        // Store documents for result retrieval
        nodes.forEach(node => {
            this.documents[node.id] = node;
        });

        console.log(`Search index built with ${nodes.length} nodes`);
    },

    /**
     * Search the index.
     * @param {string} query - Search query
     * @param {Object} filters - Optional filters { type, realm }
     * @returns {Array} Array of matching nodes
     */
    search(query, filters = {}) {
        if (!this.index) {
            console.warn('Search index not built');
            return [];
        }

        if (!query || query.trim() === '') {
            // Return all documents if no query (for filtering only)
            let results = Object.values(this.documents);

            // Apply filters
            if (filters.type) {
                results = results.filter(n => n.type === filters.type);
            }
            if (filters.realm) {
                results = results.filter(n => n.realm === filters.realm);
            }

            return results;
        }

        try {
            // Lunr search with wildcard support
            let searchQuery = query
                .split(/\s+/)
                .map(term => `${term}*`)
                .join(' ');

            const searchResults = this.index.search(searchQuery);

            // Map to documents and apply filters
            let results = searchResults
                .map(result => this.documents[result.ref])
                .filter(doc => doc !== undefined);

            if (filters.type) {
                results = results.filter(n => n.type === filters.type);
            }
            if (filters.realm) {
                results = results.filter(n => n.realm === filters.realm);
            }

            return results;
        } catch (e) {
            console.error('Search error:', e);
            return [];
        }
    },

    /**
     * Get a specific document by ID.
     * @param {string} id - Document ID
     * @returns {Object|null} Node object or null
     */
    getDocument(id) {
        return this.documents[id] || null;
    },

    /**
     * Get all documents matching filters.
     * @param {Object} filters - Filters { type, realm }
     * @returns {Array} Array of matching nodes
     */
    filter(filters = {}) {
        let results = Object.values(this.documents);

        if (filters.type) {
            results = results.filter(n => n.type === filters.type);
        }
        if (filters.realm) {
            results = results.filter(n => n.realm === filters.realm);
        }

        return results;
    },

    /**
     * Get node IDs matching a search query (for highlighting in graph).
     * @param {string} query - Search query
     * @returns {Set<string>} Set of matching node IDs
     */
    getMatchingIds(query) {
        const results = this.search(query);
        return new Set(results.map(r => r.id));
    }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Search;
}
