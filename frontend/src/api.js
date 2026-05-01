/**
 * API client for Master of Magic Wiki Corpus REST API.
 */

const API = {
    baseUrl: '',  // Same origin when served by API

    /**
     * Set the API base URL.
     * @param {string} url - Base URL for the API
     */
    setBaseUrl(url) {
        this.baseUrl = url.replace(/\/$/, '');
    },

    /**
     * Make a GET request to the API.
     * @param {string} endpoint - API endpoint
     * @param {Object} params - Query parameters
     * @returns {Promise<Object>} Response data
     */
    async get(endpoint, params = {}) {
        const base = this.baseUrl || window.location.origin;
        const url = new URL(`${base}${endpoint}`);
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                url.searchParams.append(key, value);
            }
        });

        const response = await fetch(url.toString());
        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        return response.json();
    },

    /**
     * Make a POST request to the API.
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request body
     * @returns {Promise<Object>} Response data
     */
    async post(endpoint, data = {}) {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        return response.json();
    },

    // Search
    async search(query, options = {}) {
        return this.get('/search', { q: query, ...options });
    },

    // Documents
    async listDocuments(options = {}) {
        return this.get('/documents', options);
    },

    async getDocument(id, includeContent = true) {
        return this.get(`/documents/${id}`, { include_content: includeContent });
    },

    async getDocumentContent(id) {
        return this.get(`/documents/${id}/content`);
    },

    // Nodes
    async listNodes(options = {}) {
        return this.get('/nodes', options);
    },

    async getNode(id) {
        return this.get(`/nodes/${id}`);
    },

    async getRelatedNodes(id, relType = null) {
        const params = relType ? { rel_type: relType } : {};
        return this.get(`/nodes/${id}/related`, params);
    },

    async getGraph(options = {}) {
        return this.get('/nodes/graph', options);
    },

    // Sources
    async listSources(options = {}) {
        return this.get('/sources', options);
    },

    async getSource(id) {
        return this.get(`/sources/${id}`);
    },

    async createSource(data) {
        return this.post('/sources', data);
    },

    async triggerScrape(sourceId) {
        return this.post(`/sources/${sourceId}/scrape`);
    },

    async getJob(jobId) {
        return this.get(`/sources/jobs/${jobId}`);
    }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
}
