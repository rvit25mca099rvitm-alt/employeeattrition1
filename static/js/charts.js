/**
 * Employee Attrition & XAI - Chart.js Helper Utilities
 * Provides global theme styling, color definitions, and standard chart initializers.
 */

// Corporate Color Palette for HR Analytics
const AttritionColors = {
    primary: '#2563eb',       // Blue
    primaryLight: '#60a5fa',  // Sky Blue
    danger: '#ef4444',        // Red (Attrition / High Risk)
    success: '#10b981',       // Green (Retained / Low Risk)
    warning: '#f59e0b',       // Amber (Medium Risk)
    slate: '#64748b',         // Neutral Slate
    lightGray: '#f1f5f9',     // Gridlines
    darkText: '#1e293b'       // Headings / Labels
};

// Global Chart.js Font & Animation Defaults
if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
    Chart.defaults.color = AttritionColors.slate;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.9)';
}

/**
 * Creates a horizontal bar chart for SHAP contributions.
 * @param {string} canvasId 
 * @param {Array<string>} labels 
 * @param {Array<number>} values 
 */
function renderShapHorizontalBar(canvasId, labels, values) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const bgColors = values.map(v => v >= 0 ? AttritionColors.danger : AttritionColors.success);

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: bgColors,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: AttritionColors.lightGray },
                    title: { display: true, text: 'SHAP Contribution' }
                },
                y: { grid: { display: false } }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}
