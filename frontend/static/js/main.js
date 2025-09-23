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

    // Check if the data is a final report or search results
    if (data.detailed_summary) {
        // Display the final report
        const reportHtml = `
            <div class="result-item">
                <h3>${data.title}</h3>
                <div class="result-content">
                    <h4>Summary</h4>
                    <p>${data.detailed_summary.replace(/\n/g, '<br>')}</p>
                    <h4>Sources</h4>
                    <ul>
                        ${Object.entries(data.links).map(([url, status]) => `<li><a href="${url}" target="_blank">${url}</a> - <em>${status}</em></li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
        currentResults.innerHTML = reportHtml;
    } else {
        // This part can be kept for displaying initial search results if the backend ever sends them
        const resultHtml = `
            <div class="result-item">
                <h3>${data.query}</h3>
                <div class="result-meta">
                    <p>Results found: ${Object.keys(data.search_results).length}</p>
                    <p>Timestamp: ${new Date().toLocaleString()}</p>
                </div>
                <div class="result-content">
                    ${Object.entries(data.search_results).map(([id, result]) => {
                        const content = data.extracted_contents[result.link];
                        return `
                            <li>
                                <h4><a href="${result.link}" target="_blank">${result.title || result.link}</a></h4>
                                ${content && content.text ? `<p>${truncateText(content.text, 200)}</p>` : ''}
                            </li>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
        currentResults.innerHTML = resultHtml;
    }

    searchResults.classList.remove('hidden');
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
        
        // The content of the report, to be shown/hidden
        const reportContent = `
            <div class="result-content">
                <h4>Summary</h4>
                <p>${item.detailed_summary.replace(/\n/g, '<br>')}</p>
                <h4>Sources</h4>
                <ul>
                    ${Object.entries(item.links).map(([url, status]) => `<li><a href="${url}" target="_blank">${url}</a> - <em>${status}</em></li>`).join('')}
                </ul>
            </div>
        `;

        historyItem.innerHTML = `
            <h3>${item.title || item.query}</h3>
            <div class="result-meta">
                <p>Date: ${new Date(item.created_datetime).toLocaleString()}</p>
            </div>
            ${reportContent}
        `;

        // Add click event to the title to toggle the content
        historyItem.querySelector('h3').addEventListener('click', () => {
            historyItem.classList.toggle('active');
        });

        historyList.appendChild(historyItem);
    });
}

// Display History Item
function displayHistoryItem(item) {
    // This function will now act as a wrapper for displaySearchResults
    displaySearchResults(item);
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