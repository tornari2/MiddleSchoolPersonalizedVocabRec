// ===================================================================
// Student Vocabulary Dashboard - Main JavaScript
// ===================================================================

// Global state
let currentView = 'list';
let currentStudentId = null;
let dashboardData = {};
let charts = {};
let week5Loaded = false;

// Tooltip definitions
const TOOLTIPS = {
    proficiency: {
        title: 'Proficiency Score',
        text: 'Overall vocabulary proficiency (0-1). Calculated from vocabulary diversity, academic word usage, sentence complexity, and grammatical range. Higher scores indicate stronger vocabulary skills.'
    },
    richness: {
        title: 'Vocabulary Richness',
        text: 'Ratio of unique words to total words (0-1). Higher means more diverse vocabulary. For example, a score of 0.5 means half the words used were unique. Note: This metric naturally decreases as more text is analyzed due to word repetition.'
    },
    academic: {
        title: 'Academic Word Ratio',
        text: 'Percentage of academic words used (0-1). Shows academic language proficiency. Academic words are specialized terms commonly used in educational contexts. May vary based on assignment topics.'
    },
    'rec-score': {
        title: 'Recommendation Score',
        text: 'Quality score (0-1) based on gap relevance (40%), grade appropriateness (25%), academic utility (20%), contextual fit (10%), and pronunciation ease (5%).'
    },
    cumulative: {
        title: 'Cumulative Analysis',
        text: 'These metrics analyze all student writing samples collected up to each week (cumulative). Week 1 analyzes 10 samples, Week 4 analyzes 40 samples. As more text is analyzed, vocabulary richness typically decreases due to word repetition, while other metrics may fluctuate based on writing topics and content variety.'
    }
};

// Initialize dashboard on load
document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
});

function initializeDashboard() {
    // Load data
    dashboardData = DASHBOARD_DATA;
    
    // Setup event listeners
    setupEventListeners();
    
    // Render student list
    renderStudentList();
    
    // Setup tooltips
    setupTooltips();
}

function setupEventListeners() {
    // Search
    document.getElementById('search-input').addEventListener('input', filterStudents);
    
    // Grade filter
    document.getElementById('grade-filter').addEventListener('change', filterStudents);
    
    // Back button
    document.getElementById('back-button').addEventListener('click', showStudentList);
    
    // Load new data button
    document.getElementById('load-new-data-btn').addEventListener('click', loadWeek5Data);
    
    // Sort for recommendations table
    document.getElementById('sort-select').addEventListener('change', sortRecommendations);
}

function setupTooltips() {
    document.querySelectorAll('.tooltip-icon').forEach(icon => {
        icon.addEventListener('click', (e) => {
            e.stopPropagation();
            const tooltipKey = icon.dataset.tooltip;
            showTooltip(tooltipKey);
        });
    });
    
    document.querySelector('.tooltip-close').addEventListener('click', hideTooltip);
    document.getElementById('tooltip-overlay').addEventListener('click', (e) => {
        if (e.target.id === 'tooltip-overlay') {
            hideTooltip();
        }
    });
}

function showTooltip(key) {
    const tooltip = TOOLTIPS[key];
    if (!tooltip) return;
    
    document.getElementById('tooltip-title').textContent = tooltip.title;
    document.getElementById('tooltip-text').textContent = tooltip.text;
    document.getElementById('tooltip-overlay').classList.add('active');
}

function hideTooltip() {
    document.getElementById('tooltip-overlay').classList.remove('active');
}

function renderStudentList() {
    const grid = document.getElementById('student-grid');
    grid.innerHTML = '';

    const students = Object.values(dashboardData);
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const gradeFilter = document.getElementById('grade-filter').value;

    students
        .sort((a, b) => a.name.localeCompare(b.name)) // Sort alphabetically by name
        .filter(student => {
            const matchesSearch = student.name.toLowerCase().includes(searchTerm) ||
                                student.student_id.toLowerCase().includes(searchTerm);
            const matchesGrade = gradeFilter === 'all' || student.grade_level.toString() === gradeFilter;
            return matchesSearch && matchesGrade;
        })
        .forEach(student => {
            const latestReport = student.weekly_reports[student.weekly_reports.length - 1];
            const card = createStudentCard(student, latestReport);
            grid.appendChild(card);
        });
}

function createStudentCard(student, latestReport) {
    const card = document.createElement('div');
    card.className = 'student-card';
    card.onclick = () => showStudentDetail(student.student_id);
    
    const proficiencyPercent = (latestReport.proficiency_score * 100).toFixed(0);
    const lastUpdated = new Date(latestReport.report_date).toLocaleDateString();
    
    card.innerHTML = `
        <div class="student-card-header">
            <div class="student-name">${student.name}</div>
            <div class="student-grade">Grade ${student.grade_level}</div>
        </div>
        <div class="student-id">${student.student_id}</div>
        <div class="student-metrics">
            <div class="metric-row">
                <span class="metric-label">Proficiency</span>
                <span class="metric-value">${latestReport.proficiency_score.toFixed(3)}</span>
            </div>
            <div class="proficiency-bar">
                <div class="proficiency-fill" style="width: ${proficiencyPercent}%"></div>
            </div>
            <div class="metric-row">
                <span class="metric-label">Vocabulary Richness</span>
                <span class="metric-value">${latestReport.vocabulary_richness.toFixed(3)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Academic Word Ratio</span>
                <span class="metric-value">${latestReport.academic_word_ratio.toFixed(3)}</span>
            </div>
        </div>
        <div class="last-updated">Last updated: ${lastUpdated}</div>
    `;
    
    return card;
}

function filterStudents() {
    renderStudentList();
}

function showStudentDetail(studentId) {
    currentStudentId = studentId;
    const student = dashboardData[studentId];
    
    // Update header
    document.getElementById('student-name').textContent = student.name;
    document.getElementById('student-meta').textContent = `${student.student_id} | Grade ${student.grade_level}`;
    
    // Update score cards
    const latestReport = student.weekly_reports[student.weekly_reports.length - 1];
    document.getElementById('proficiency-score').textContent = latestReport.proficiency_score.toFixed(3);
    document.getElementById('richness-score').textContent = latestReport.vocabulary_richness.toFixed(3);
    document.getElementById('academic-score').textContent = latestReport.academic_word_ratio.toFixed(3);
    
    // Calculate trends
    if (student.weekly_reports.length > 1) {
        const prevReport = student.weekly_reports[student.weekly_reports.length - 2];
        updateTrend('proficiency-trend', latestReport.proficiency_score, prevReport.proficiency_score);
        updateTrend('richness-trend', latestReport.vocabulary_richness, prevReport.vocabulary_richness);
        updateTrend('academic-trend', latestReport.academic_word_ratio, prevReport.academic_word_ratio);
    }
    
    // Render charts
    renderCharts(student);
    
    // Render recommendations table (sorted by score by default)
    const sortedRecommendations = [...latestReport.recommendations].sort((a, b) => b.total_score - a.total_score);

    // Set display ranks for score-based sorting
    sortedRecommendations.forEach((rec, index) => {
        rec.display_rank = index + 1;
    });

    renderRecommendationsTable(sortedRecommendations);
    
    // Switch views
    document.getElementById('student-list-view').classList.remove('active');
    document.getElementById('student-detail-view').classList.add('active');
    currentView = 'detail';
    
    // Scroll to top
    window.scrollTo(0, 0);
}

function updateTrend(elementId, current, previous) {
    const element = document.getElementById(elementId);
    const diff = current - previous;
    const percent = ((diff / previous) * 100).toFixed(1);
    
    if (diff > 0) {
        element.textContent = `↑ +${percent}%`;
        element.className = 'score-trend up';
    } else if (diff < 0) {
        element.textContent = `↓ ${percent}%`;
        element.className = 'score-trend down';
    } else {
        element.textContent = '→ No change';
        element.className = 'score-trend neutral';
    }
}

function renderCharts(student) {
    // Destroy existing charts
    Object.values(charts).forEach(chart => chart.destroy());
    charts = {};
    
    const weeks = student.weekly_reports.map(r => `Week ${r.week}`);
    const proficiencyData = student.weekly_reports.map(r => r.proficiency_score);
    const richnessData = student.weekly_reports.map(r => r.vocabulary_richness);
    const academicData = student.weekly_reports.map(r => r.academic_word_ratio);
    
    // Proficiency Chart
    charts.proficiency = new Chart(document.getElementById('proficiency-chart'), {
        type: 'line',
        data: {
            labels: weeks,
            datasets: [{
                label: 'Proficiency Score',
                data: proficiencyData,
                borderColor: '#4A90E2',
                backgroundColor: 'rgba(74, 144, 226, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: getChartOptions('Proficiency Score', 0, 1)
    });
    
    // Richness Chart
    charts.richness = new Chart(document.getElementById('richness-chart'), {
        type: 'line',
        data: {
            labels: weeks,
            datasets: [{
                label: 'Vocabulary Richness',
                data: richnessData,
                borderColor: '#50C878',
                backgroundColor: 'rgba(80, 200, 120, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: getChartOptions('Vocabulary Richness', 0, 1)
    });
    
    // Academic Chart
    charts.academic = new Chart(document.getElementById('academic-chart'), {
        type: 'line',
        data: {
            labels: weeks,
            datasets: [{
                label: 'Academic Word Ratio',
                data: academicData,
                borderColor: '#7B68EE',
                backgroundColor: 'rgba(123, 104, 238, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: getChartOptions('Academic Word Ratio', 0, 1)
    });
}

function getChartOptions(title, min, max) {
    return {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                callbacks: {
                    label: (context) => `${context.parsed.y.toFixed(3)}`
                }
            }
        },
        scales: {
            y: {
                min: min,
                max: max,
                ticks: {
                    callback: (value) => value.toFixed(2)
                }
            }
        }
    };
}

function renderRecommendationsTable(recommendations) {
    const tbody = document.getElementById('recommendations-tbody');
    tbody.innerHTML = '';
    
    recommendations.forEach(rec => {
        const row = createRecommendationRow(rec);
        tbody.appendChild(row);
    });
}

function createRecommendationRow(rec) {
    const row = document.createElement('tr');
    const dateAdded = new Date(rec.created_at).toLocaleDateString();

    row.innerHTML = `
        <td>${rec.display_rank || rec.recommendation_rank}</td>
        <td class="word-cell">${rec.word}</td>
        <td>${rec.definition || 'N/A'}</td>
        <td>${rec.part_of_speech}</td>
        <td>${rec.total_score.toFixed(3)}</td>
        <td>${dateAdded}</td>
    `;
    
    return row;
}

function sortRecommendations() {
    const sortBy = document.getElementById('sort-select').value;
    const student = dashboardData[currentStudentId];
    const latestReport = student.weekly_reports[student.weekly_reports.length - 1];
    let recs = [...latestReport.recommendations];

    switch (sortBy) {
        case 'rank':
            recs.sort((a, b) => a.recommendation_rank - b.recommendation_rank);
            break;
        case 'score':
            recs.sort((a, b) => b.total_score - a.total_score);
            break;
        case 'word':
            recs.sort((a, b) => a.word.localeCompare(b.word));
            break;
        case 'date':
            recs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            break;
    }

    // Update ranks to match the current sort order
    recs.forEach((rec, index) => {
        rec.display_rank = index + 1; // Add display_rank for the current sorting
    });

    renderRecommendationsTable(recs);
}


function showStudentList() {
    document.getElementById('student-detail-view').classList.remove('active');
    document.getElementById('student-list-view').classList.add('active');
    currentView = 'list';
    currentStudentId = null;
}

async function loadWeek5Data() {
    if (week5Loaded) {
        showToast('Week 5 data already loaded!');
        return;
    }
    
    showLoading();
    
    // Simulate loading delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    try {
        // Load week 5 data from external file
        const week5Data = await loadWeek5File();
        
        // Merge week 5 data into dashboard data
        Object.keys(week5Data).forEach(studentId => {
            if (dashboardData[studentId]) {
                // Add week 5 report to existing student
                const week5Report = week5Data[studentId].weekly_reports[0];
                dashboardData[studentId].weekly_reports.push(week5Report);
            }
        });
        
        week5Loaded = true;
        
        // Refresh current view
        if (currentView === 'list') {
            renderStudentList();
        } else if (currentStudentId) {
            showStudentDetail(currentStudentId);
        }
        
        hideLoading();
        showToast('✓ Week 5 data loaded successfully!');
        
        // Disable button
        document.getElementById('load-new-data-btn').disabled = true;
        document.getElementById('load-new-data-btn').textContent = '✓ Week 5 Loaded';
        
    } catch (error) {
        hideLoading();
        showToast('Error loading week 5 data', 'error');
        console.error('Error:', error);
    }
}

async function loadWeek5File() {
    // Check if week5_data.js is loaded
    if (typeof WEEK5_DATA !== 'undefined') {
        return WEEK5_DATA;
    }
    
    // If not, load it dynamically
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'week5_data.js';
        script.onload = () => {
            if (typeof WEEK5_DATA !== 'undefined') {
                resolve(WEEK5_DATA);
            } else {
                reject(new Error('Week 5 data not found'));
            }
        };
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

function showLoading() {
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.backgroundColor = type === 'error' ? '#FF6B6B' : '#50C878';
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Export/Print Functions
function printView(mode) {
    // Add print mode class to body
    document.body.className = `print-standard`;

    // Print
    window.print();

    // Remove class after print
    setTimeout(() => {
        document.body.className = '';
    }, 100);
}

function exportToCSV() {
    if (!currentStudentId) return;
    
    const student = dashboardData[currentStudentId];
    const latestReport = student.weekly_reports[student.weekly_reports.length - 1];
    
    // Create CSV content
    let csv = 'Student Vocabulary Report\n\n';
    csv += `Student Name:,${student.name}\n`;
    csv += `Student ID:,${student.student_id}\n`;
    csv += `Grade Level:,${student.grade_level}\n`;
    csv += `Report Date:,${new Date(latestReport.report_date).toLocaleDateString()}\n\n`;
    
    csv += 'Vocabulary Profile\n';
    csv += `Proficiency Score:,${latestReport.proficiency_score.toFixed(3)}\n`;
    csv += `Vocabulary Richness:,${latestReport.vocabulary_richness.toFixed(3)}\n`;
    csv += `Academic Word Ratio:,${latestReport.academic_word_ratio.toFixed(3)}\n`;
    csv += `Unique Words:,${latestReport.unique_words}\n\n`;
    
    csv += 'Recommended Vocabulary Words\n';
    csv += 'Rank,Word,Definition,Part of Speech,Score,Academic Utility,Date Added\n';
    
    latestReport.recommendations.forEach(rec => {
        const dateAdded = new Date(rec.created_at).toLocaleDateString();
        csv += `${rec.recommendation_rank},"${rec.word}","${rec.definition}",${rec.part_of_speech},${rec.total_score.toFixed(3)},${rec.academic_utility},${dateAdded}\n`;
    });
    
    // Download CSV
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${student.student_id}_${student.name.replace(/\s+/g, '_')}_vocabulary_report.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    showToast('CSV exported successfully!');
}

