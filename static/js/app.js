// ===== GLOBAL STATE =====
let activePolling = new Set();
let models = [];

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    console.log('Initializing Stem Splitter Pro...');

    // Load models
    await loadModels();

    // Setup event listeners
    setupEventListeners();

    // Load dark mode preference
    loadDarkMode();

    // Load history
    await loadHistory();

    // Start auto-refresh for history
    setInterval(loadHistory, 30000); // Every 30 seconds

    console.log('Initialization complete!');
}

// ===== LOAD MODELS =====
async function loadModels() {
    try {
        const response = await fetch('/api/models');
        models = await response.json();

        const selects = ['modelSelect', 'batchModelSelect'];
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            select.innerHTML = models.map(model =>
                `<option value="${model}">${model}</option>`
            ).join('');
        });

        console.log('Models loaded:', models);
    } catch (error) {
        console.error('Failed to load models:', error);
        showToast('Failed to load models', 'error');
    }
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Single URL form
    document.getElementById('singleForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = document.getElementById('urlInput').value.trim();
        const model = document.getElementById('modelSelect').value;
        await processSingleURL(url, model);
    });

    // Batch form
    document.getElementById('batchForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const urls = document.getElementById('batchInput').value
            .split('\n')
            .map(url => url.trim())
            .filter(url => url.length > 0);
        const model = document.getElementById('batchModelSelect').value;
        await processBatchURLs(urls, model);
    });

    // Dark mode toggle
    document.getElementById('darkModeToggle').addEventListener('click', toggleDarkMode);
}

// ===== URL VALIDATION =====
function validateURL(url) {
    const pattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|soundcloud\.com|m\.soundcloud\.com)\/.+$/;
    return pattern.test(url);
}

// ===== PROCESS SINGLE URL =====
async function processSingleURL(url, model) {
    // Validate
    if (!validateURL(url)) {
        document.getElementById('urlError').textContent = 'Invalid YouTube or SoundCloud URL';
        document.getElementById('urlError').classList.add('show');
        return;
    }

    document.getElementById('urlError').classList.remove('show');

    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, model })
        });

        const data = await response.json();

        if (data.success) {
            showToast('Processing started!', 'success');
            document.getElementById('urlInput').value = '';

            // Start polling this job
            startPolling(data.job_id);
        } else {
            showToast('Failed to start processing', 'error');
        }
    } catch (error) {
        console.error('Network error:', error);
        showToast('Network error', 'error');
    }
}

// ===== PROCESS BATCH URLS =====
async function processBatchURLs(urls, model) {
    // Validate all URLs
    const validUrls = urls.filter(validateURL);

    if (validUrls.length === 0) {
        showToast('No valid URLs found', 'error');
        return;
    }

    if (validUrls.length < urls.length) {
        showToast(`${urls.length - validUrls.length} invalid URLs skipped`, 'warning');
    }

    try {
        const response = await fetch('/api/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ urls: validUrls, model })
        });

        const data = await response.json();

        if (data.success) {
            showToast(`${data.job_ids.length} jobs started!`, 'success');
            document.getElementById('batchInput').value = '';

            // Start polling all jobs
            data.job_ids.forEach(id => startPolling(id));
        }
    } catch (error) {
        console.error('Network error:', error);
        showToast('Network error', 'error');
    }
}

// ===== POLLING =====
function startPolling(jobId) {
    if (activePolling.has(jobId)) return;

    activePolling.add(jobId);
    console.log('Started polling job:', jobId);

    const poll = async () => {
        try {
            const response = await fetch(`/api/status/${jobId}`);
            const job = await response.json();

            updateJobDisplay(job);

            // Stop polling if complete or error
            if (job.status === 'complete' || job.status === 'error') {
                activePolling.delete(jobId);
                console.log('Stopped polling job:', jobId, 'Status:', job.status);
                await loadHistory();
            } else {
                setTimeout(poll, 2000); // Poll every 2 seconds
            }
        } catch (error) {
            console.error('Polling error:', error);
            activePolling.delete(jobId);
        }
    };

    poll();
}

// ===== UPDATE JOB DISPLAY =====
function updateJobDisplay(job) {
    let container = document.getElementById('activeJobs');
    let jobCard = document.getElementById(`job-${job.id}`);

    // Create card if it doesn't exist
    if (!jobCard) {
        jobCard = createJobCard(job);

        // Remove empty state if present
        const emptyState = container.querySelector('.empty-state');
        if (emptyState) emptyState.remove();

        container.appendChild(jobCard);
    }

    // Update card content
    const titleEl = jobCard.querySelector('.job-title');
    if (job.title && titleEl.textContent !== job.title) {
        titleEl.textContent = job.title;
    }

    const statusBadge = jobCard.querySelector('.status-badge');
    statusBadge.textContent = job.status;
    statusBadge.className = `status-badge status-${job.status}`;

    const progressFill = jobCard.querySelector('.progress-fill');
    progressFill.style.width = `${job.progress}%`;

    const message = jobCard.querySelector('.job-message');
    message.textContent = job.message;

    // If complete, add download buttons
    if (job.status === 'complete') {
        addDownloadButtons(jobCard, job);
    }
}

// ===== CREATE JOB CARD =====
function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';
    card.id = `job-${job.id}`;

    card.innerHTML = `
        <div class="job-header">
            <div class="job-title">${job.title || job.url}</div>
            <span class="status-badge status-${job.status}">${job.status}</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${job.progress}%"></div>
        </div>
        <div class="job-message">${job.message}</div>
        <div class="download-buttons"></div>
    `;

    return card;
}

// ===== ADD DOWNLOAD BUTTONS =====
function addDownloadButtons(card, job) {
    const container = card.querySelector('.download-buttons');
    if (container.children.length > 0) return; // Already added

    const stems = Object.keys(job.stems);
    stems.forEach(stem => {
        const btn = document.createElement('button');
        btn.className = 'btn-download';
        btn.textContent = `📥 ${stem}`;
        btn.onclick = () => downloadStem(job.id, stem);
        container.appendChild(btn);
    });
}

// ===== DOWNLOAD STEM =====
function downloadStem(jobId, stem) {
    const url = `/api/download/${jobId}/${stem}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = `${stem}.wav`;
    a.click();
    showToast(`Downloading ${stem}...`, 'info');
}

// ===== LOAD HISTORY =====
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const jobs = await response.json();

        const container = document.getElementById('completedJobs');

        if (jobs.length === 0) {
            container.innerHTML = '<p class="empty-state">No completed jobs</p>';
            return;
        }

        container.innerHTML = jobs.map(job => `
            <div class="job-card" id="history-${job.id}">
                <div class="job-header">
                    <div class="job-title">${job.title}</div>
                    <span class="status-badge status-complete">complete</span>
                </div>
                <p class="job-message">Processed: ${formatTimestamp(job.timestamp)}</p>
                <div class="download-buttons">
                    ${Object.keys(job.stems).map(stem => `
                        <button class="btn-download" onclick="downloadStem('${job.id}', '${stem}')">
                            📥 ${stem}
                        </button>
                    `).join('')}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : type === 'warning' ? '⚠' : 'ℹ';
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ===== DARK MODE =====
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);

    const toggle = document.getElementById('darkModeToggle');
    toggle.textContent = isDark ? '☀️' : '🌙';
}

function loadDarkMode() {
    const isDark = localStorage.getItem('darkMode') === 'true';
    if (isDark) {
        document.body.classList.add('dark-mode');
        document.getElementById('darkModeToggle').textContent = '☀️';
    }
}

// ===== UTILITIES =====
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;

    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;

    return date.toLocaleDateString();
}
