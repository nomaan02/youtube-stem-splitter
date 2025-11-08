// =========================================
// STEM SPLITTER PRO - TERMINAL STYLE JS
// =========================================

// Global state
let activePolling = new Set();
let models = [];
let startTime = Date.now();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

// ============= INITIALIZATION =============
async function initializeApp() {
    // Load models
    await loadModels();
    
    // Setup event listeners
    setupEventListeners();
    
    // Start system monitoring
    startSystemMonitoring();
    
    // Load history
    await loadHistory();
    
    // Start auto-refresh
    setInterval(loadHistory, 30000);
}

// ============= EVENT LISTENERS =============
function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    
    // Single URL form
    document.getElementById('processForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = document.getElementById('urlInput').value;
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
    
    // Clear history
    document.getElementById('clearHistory')?.addEventListener('click', clearHistory);
}

// ============= TAB SWITCHING =============
function switchTab(tabName) {
    // Update tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
}

// ============= MODELS =============
async function loadModels() {
    try {
        const response = await fetch('/api/models');
        models = await response.json();
        
        // Populate selects
        const selects = [
            document.getElementById('modelSelect'),
            document.getElementById('batchModelSelect')
        ];
        
        selects.forEach(select => {
            select.innerHTML = models.map(model => {
                let label = model;
                if (model === 'htdemucs') label += ' [BALANCED]';
                if (model === 'htdemucs_ft') label += ' [QUALITY]';
                if (model === 'htdemucs_6s') label += ' [MAXIMUM]';
                return `<option value="${model}">${label}</option>`;
            }).join('');
        });
    } catch (error) {
        showToast('Failed to load models', 'error');
    }
}

// ============= URL VALIDATION =============
function validateURL(url) {
    const pattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|soundcloud\.com|m\.soundcloud\.com)\/.+$/;
    return pattern.test(url);
}

// ============= PROCESS SINGLE URL =============
async function processSingleURL(url, model) {
    if (!validateURL(url)) {
        showToast('INVALID_URL_FORMAT', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, model })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('PROCESS_INITIATED', 'success');
            document.getElementById('urlInput').value = '';
            startPolling(data.job_id);
        } else {
            showToast('PROCESS_FAILED', 'error');
        }
    } catch (error) {
        showToast('NETWORK_ERROR', 'error');
    }
}

// ============= PROCESS BATCH =============
async function processBatchURLs(urls, model) {
    const validUrls = urls.filter(validateURL);
    
    if (validUrls.length === 0) {
        showToast('NO_VALID_URLS', 'error');
        return;
    }
    
    if (validUrls.length < urls.length) {
        showToast(`${urls.length - validUrls.length} INVALID_URLS_SKIPPED`, 'info');
    }
    
    try {
        const response = await fetch('/api/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ urls: validUrls, model })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`${data.job_ids.length} JOBS_INITIATED`, 'success');
            document.getElementById('batchInput').value = '';
            data.job_ids.forEach(id => startPolling(id));
        }
    } catch (error) {
        showToast('NETWORK_ERROR', 'error');
    }
}

// ============= STATUS POLLING =============
function startPolling(jobId) {
    if (activePolling.has(jobId)) return;
    
    activePolling.add(jobId);
    
    const poll = async () => {
        try {
            const response = await fetch(`/api/status/${jobId}`);
            const job = await response.json();
            
            updateJobDisplay(job);
            
            if (job.status === 'complete' || job.status === 'error') {
                activePolling.delete(jobId);
                await loadHistory();
            } else {
                setTimeout(poll, 2000);
            }
        } catch (error) {
            activePolling.delete(jobId);
        }
    };
    
    poll();
}

// ============= UPDATE JOB DISPLAY =============
function updateJobDisplay(job) {
    let container = document.getElementById('activeJobs');
    let jobCard = document.getElementById(`job-${job.id}`);
    
    if (!jobCard) {
        jobCard = createJobCard(job);
        container.appendChild(jobCard);
        
        // Remove empty state
        const emptyState = container.querySelector('.empty-state');
        if (emptyState) emptyState.remove();
    }
    
    // Update card
    const statusBadge = jobCard.querySelector('.status-badge');
    statusBadge.textContent = job.status.toUpperCase();
    statusBadge.className = `status-badge ${job.status}`;
    
    const progressFill = jobCard.querySelector('.progress-fill');
    if (progressFill) {
        progressFill.style.width = `${job.progress}%`;
    }
    
    const jobInfo = jobCard.querySelector('.job-info');
    if (jobInfo) {
        jobInfo.textContent = `${job.message} | ${job.progress}%`;
    }
    
    // If complete, add download buttons
    if (job.status === 'complete') {
        addDownloadButtons(jobCard, job);
    }
    
    updateCounters();
}

// ============= CREATE JOB CARD =============
function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';
    card.id = `job-${job.id}`;
    
    card.innerHTML = `
        <div class="job-header">
            <div class="job-title">[►] ${job.title || job.url}</div>
            <span class="status-badge ${job.status}">${job.status.toUpperCase()}</span>
        </div>
        <div class="job-info">${job.message} | ${job.progress}%</div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${job.progress}%"></div>
        </div>
        <div class="download-buttons"></div>
    `;
    
    return card;
}

// ============= ADD DOWNLOAD BUTTONS =============
function addDownloadButtons(card, job) {
    const container = card.querySelector('.download-buttons');
    if (container.children.length > 0) return;
    
    const stems = Object.keys(job.stems);
    stems.forEach(stem => {
        const btn = document.createElement('button');
        btn.className = 'download-btn';
        btn.textContent = `[DL] ${stem}`;
        btn.onclick = () => downloadStem(job.id, stem);
        container.appendChild(btn);
    });
}

// ============= DOWNLOAD STEM =============
function downloadStem(jobId, stem) {
    const url = `/api/download/${jobId}/${stem}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = `${stem}.wav`;
    a.click();
    showToast(`DOWNLOADING: ${stem}`, 'info');
}

// ============= LOAD HISTORY =============
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const jobs = await response.json();
        
        const container = document.getElementById('historyJobs');
        
        if (jobs.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">⌀</span>
                    <p>NO_HISTORY</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = jobs.map(job => `
            <div class="job-card" id="history-${job.id}">
                <div class="job-header">
                    <div class="job-title">[✓] ${job.title}</div>
                    <span class="status-badge complete">COMPLETE</span>
                </div>
                <div class="job-info">${formatTimestamp(job.timestamp)}</div>
                <div class="download-buttons">
                    ${Object.keys(job.stems).map(stem => `
                        <button class="download-btn" onclick="downloadStem('${job.id}', '${stem}')">
                            [DL] ${stem}
                        </button>
                    `).join('')}
                </div>
            </div>
        `).join('');
        
        updateCounters();
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

// ============= CLEAR HISTORY =============
function clearHistory() {
    if (!confirm('CLEAR_ALL_HISTORY?')) return;
    
    const container = document.getElementById('historyJobs');
    container.innerHTML = `
        <div class="empty-state">
            <span class="empty-icon">⌀</span>
            <p>NO_HISTORY</p>
        </div>
    `;
    
    showToast('HISTORY_CLEARED', 'success');
    updateCounters();
}

// ============= UPDATE COUNTERS =============
function updateCounters() {
    const activeJobs = document.querySelectorAll('#activeJobs .job-card').length;
    const completeJobs = document.querySelectorAll('#completedJobs .job-card').length;
    const historyJobs = document.querySelectorAll('#historyJobs .job-card').length;
    
    document.getElementById('activeCount').textContent = activeJobs;
    document.getElementById('completeCount').textContent = completeJobs;
    document.getElementById('totalJobs').textContent = historyJobs;
}

// ============= SYSTEM MONITORING =============
function startSystemMonitoring() {
    updateTime();
    setInterval(updateTime, 1000);
    
    updateUptime();
    setInterval(updateUptime, 1000);
}

function updateTime() {
    const now = new Date();
    const timeString = now.toTimeString().split(' ')[0];
    document.getElementById('timeStatus').textContent = timeString;
}

function updateUptime() {
    const uptime = Date.now() - startTime;
    const hours = Math.floor(uptime / 3600000);
    const minutes = Math.floor((uptime % 3600000) / 60000);
    const seconds = Math.floor((uptime % 60000) / 1000);
    
    const uptimeString = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    document.getElementById('uptime').textContent = uptimeString;
}

// ============= TOAST NOTIFICATIONS =============
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? '[✓]' : type === 'error' ? '[✕]' : '[i]';
    toast.textContent = `${icon} ${message}`;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'toastOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============= UTILITIES =============
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return 'JUST_NOW';
    if (minutes < 60) return `${minutes}m AGO`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h AGO`;
    
    const days = Math.floor(hours / 24);
    return `${days}d AGO`;
}

// Add CSS animation for toast out
const style = document.createElement('style');
style.textContent = `
    @keyframes toastOut {
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);
