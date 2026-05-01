/**
 * Admin Panel for Master of Magic Wiki Corpus.
 */

(function() {
    'use strict';

    // Polling interval for job status
    const JOB_POLL_INTERVAL = 2000;
    let activePolls = {};

    // DOM elements
    const addSourceForm = document.getElementById('add-source-form');
    const sourceNameInput = document.getElementById('source-name');
    const sourceTypeSelect = document.getElementById('source-type');
    const sourceLocationInput = document.getElementById('source-location');
    const sourcesList = document.getElementById('sources-list');
    const jobsList = document.getElementById('jobs-list');
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');

    // Stats elements
    const statDocuments = document.getElementById('stat-documents');
    const statNodes = document.getElementById('stat-nodes');
    const statSources = document.getElementById('stat-sources');
    const statRelationships = document.getElementById('stat-relationships');

    /**
     * Initialize the admin panel.
     */
    async function init() {
        console.log('Initializing Admin Panel...');

        // Set up event listeners
        addSourceForm.addEventListener('submit', handleAddSource);

        // Load initial data
        await Promise.all([
            loadSources(),
            loadStats()
        ]);

        console.log('Admin Panel initialized');
    }

    /**
     * Load and display sources.
     */
    async function loadSources() {
        sourcesList.innerHTML = '<p class="loading">Loading sources...</p>';

        try {
            const data = await API.listSources();
            displaySources(data.sources);
        } catch (error) {
            console.error('Failed to load sources:', error);
            sourcesList.innerHTML = '<p class="loading">Failed to load sources. Is the API running?</p>';
        }
    }

    /**
     * Display sources in the list.
     * @param {Array} sources - Array of source objects
     */
    function displaySources(sources) {
        if (!sources || sources.length === 0) {
            sourcesList.innerHTML = '<p class="loading">No sources configured yet.</p>';
            return;
        }

        sourcesList.innerHTML = sources.map(source => `
            <div class="source-card status-${source.status}" data-id="${source.id}">
                <div class="source-info">
                    <h3>${escapeHtml(source.name)}</h3>
                    <div class="source-meta">
                        <span class="source-type">${source.type.toUpperCase()}</span>
                        ${source.last_scraped ? `<span> | Last scraped: ${formatDate(source.last_scraped)}</span>` : ''}
                    </div>
                    <div class="source-location">${escapeHtml(source.location)}</div>
                    ${source.error_message ? `<div class="source-error">${escapeHtml(source.error_message)}</div>` : ''}
                </div>
                <div class="source-actions">
                    <button class="btn-scrape" onclick="Admin.triggerScrape('${source.id}')">
                        Scrape Now
                    </button>
                    <button class="btn-delete" onclick="Admin.deleteSource('${source.id}')">
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
    }

    /**
     * Handle add source form submission.
     * @param {Event} event - Form submit event
     */
    async function handleAddSource(event) {
        event.preventDefault();

        const name = sourceNameInput.value.trim();
        const type = sourceTypeSelect.value;
        const location = sourceLocationInput.value.trim();

        if (!name || !type || !location) {
            showToast('Please fill in all fields', 'error');
            return;
        }

        try {
            await API.createSource({ name, type, location });
            showToast('Source added successfully', 'success');

            // Clear form
            sourceNameInput.value = '';
            sourceLocationInput.value = '';

            // Reload sources
            await loadSources();
            await loadStats();
        } catch (error) {
            console.error('Failed to add source:', error);
            showToast('Failed to add source', 'error');
        }
    }

    /**
     * Trigger scrape for a source.
     * @param {string} sourceId - Source ID
     */
    async function triggerScrape(sourceId) {
        // Disable button
        const btn = document.querySelector(`.source-card[data-id="${sourceId}"] .btn-scrape`);
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Scraping...';
        }

        try {
            const result = await API.triggerScrape(sourceId);
            showToast('Scrape started', 'success');

            // Poll for job completion
            pollJobStatus(result.job_id, sourceId);
        } catch (error) {
            console.error('Failed to trigger scrape:', error);
            showToast('Failed to start scrape', 'error');

            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Scrape Now';
            }
        }
    }

    /**
     * Poll job status until complete.
     * @param {string} jobId - Job ID
     * @param {string} sourceId - Source ID (for UI updates)
     */
    function pollJobStatus(jobId, sourceId) {
        if (activePolls[jobId]) {
            return; // Already polling
        }

        activePolls[jobId] = setInterval(async () => {
            try {
                const job = await API.getJob(jobId);

                if (job.status === 'success' || job.status === 'failed') {
                    // Stop polling
                    clearInterval(activePolls[jobId]);
                    delete activePolls[jobId];

                    // Re-enable button
                    const btn = document.querySelector(`.source-card[data-id="${sourceId}"] .btn-scrape`);
                    if (btn) {
                        btn.disabled = false;
                        btn.textContent = 'Scrape Now';
                    }

                    // Show result
                    if (job.status === 'success') {
                        showToast(`Scrape complete: ${job.documents_created} docs, ${job.nodes_created} nodes`, 'success');
                    } else {
                        showToast('Scrape failed', 'error');
                    }

                    // Reload data
                    loadSources();
                    loadStats();
                }
            } catch (error) {
                console.error('Error polling job status:', error);
                clearInterval(activePolls[jobId]);
                delete activePolls[jobId];
            }
        }, JOB_POLL_INTERVAL);
    }

    /**
     * Delete a source.
     * @param {string} sourceId - Source ID
     */
    async function deleteSource(sourceId) {
        if (!confirm('Are you sure you want to delete this source?')) {
            return;
        }

        try {
            await API.deleteSource(sourceId);
            showToast('Source deleted', 'success');
            await loadSources();
            await loadStats();
        } catch (error) {
            console.error('Failed to delete source:', error);
            showToast('Failed to delete source', 'error');
        }
    }

    /**
     * Load corpus statistics.
     */
    async function loadStats() {
        try {
            const [docsResult, nodesResult, sourcesResult] = await Promise.all([
                API.listDocuments({ limit: 1 }),
                API.listNodes({ limit: 1 }),
                API.listSources()
            ]);

            statDocuments.textContent = docsResult.total || 0;
            statNodes.textContent = nodesResult.total || 0;
            statSources.textContent = sourcesResult.count || 0;
            statRelationships.textContent = '-'; // Would need another endpoint
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    /**
     * Show toast notification.
     * @param {string} message - Message to display
     * @param {string} type - 'success' or 'error'
     */
    function showToast(message, type = 'success') {
        toastMessage.textContent = message;
        toast.className = type;

        // Auto-hide after 3 seconds
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 3000);
    }

    /**
     * Escape HTML to prevent XSS.
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Format date for display.
     * @param {string} isoString - ISO date string
     * @returns {string} Formatted date
     */
    function formatDate(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    // Export functions for inline handlers
    window.Admin = {
        triggerScrape,
        deleteSource
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
