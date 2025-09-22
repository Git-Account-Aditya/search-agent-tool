// DOM Elements
const searchInput = document.getElementById('searchInput');
const loadingSpinner = document.getElementById('loadingSpinner');
const errorMessage = document.getElementById('errorMessage');
const searchResults = document.getElementById('searchResults');
const currentResults = document.getElementById('currentResults');
const historyList = document.getElementById('historyList');

// API Base URL
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Perform Search
async function performSearch() {
    const query = searchInput.value.trim();
    
    if (!query) {
        showError('Please enter a search query');
        return;
    }

    // Show loading state
    showLoading(true);
    hideError();
    hideResults();

    try {
        const response = await fetch(`${API_BASE_URL}/search?query=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Search failed');
        }

        displaySearchResults(data);
        loadSearchHistory(); // Refresh history after new search
    } catch (error) {
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

// Display Search Results
function displaySearchResults(data) {
    currentResults.innerHTML = '';

    const resultHtml = `
        <div class="result-item">
            <h3>${data.query}</h3>
            <div class="result-meta">
                <p>Results found: ${Object.keys(data.search_results).length}</p>
                <p>Timestamp: ${new Date().toLocaleString()}</p>
            </div>
            <div class="result-content">
                ${formatSearchResults(data.search_results, data.extracted_contents)}
            </div>
        </div>
    `;

    currentResults.innerHTML = resultHtml;
    searchResults.classList.remove('hidden');
}

// Format Search Results
function formatSearchResults(searchResults, extractedContents) {
    let html = '<ul>';
    for (const [id, result] of Object.entries(searchResults)) {
        const content = extractedContents[result.link];
        html += `
            <li>
                <h4><a href="${result.link}" target="_blank">${result.title || result.link}</a></h4>
                ${content && content.text ? `<p>${truncateText(content.text, 200)}</p>` : ''}
            </li>
        `;
    }
    html += '</ul>';
    return html;
}

// Load Search History
async function loadSearchHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/history`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error('Failed to load search history');
        }

        displaySearchHistory(data);
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Display Search History
function displaySearchHistory(history) {
    historyList.innerHTML = '';

    if (!history.length) {
        historyList.innerHTML = '<p>No search history available</p>';
        return;
    }

    history.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.innerHTML = `
            <h3>${item.query}</h3>
            <div class="result-meta">
                <p>Results: ${Object.keys(item.search_results).length}</p>
                <p>Date: ${new Date(item.created_datetime).toLocaleString()}</p>
            </div>
        `;
        historyItem.onclick = () => displayHistoryItem(item);
        historyList.appendChild(historyItem);
    });
}

// Display History Item
function displayHistoryItem(item) {
    currentResults.innerHTML = '';
    const resultHtml = `
        <div class="result-item">
            <h3>${item.query}</h3>
            <div class="result-meta">
                <p>Results found: ${Object.keys(item.search_results).length}</p>
                <p>Timestamp: ${new Date(item.created_datetime).toLocaleString()}</p>
            </div>
            <div class="result-content">
                ${formatSearchResults(item.search_results, item.extracted_contents)}
            </div>
        </div>
    `;
    currentResults.innerHTML = resultHtml;
    searchResults.classList.remove('hidden');
}

// Utility Functions
function showLoading(show) {
    loadingSpinner.classList.toggle('hidden', !show);
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

function hideError() {
    errorMessage.classList.add('hidden');
}

function hideResults() {
    searchResults.classList.add('hidden');
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadSearchHistory();
    
    // Add enter key support for search
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
});