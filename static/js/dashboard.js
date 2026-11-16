// Dashboard Charts & Realtime Metrics

document.addEventListener('DOMContentLoaded', () => {
    initDashboardCharts();
});

async function initDashboardCharts() {
    try {
        const res = await fetch('/api/pipeline/runs?limit=10');
        if (!res.ok) return;
        const runs = await res.json();

        // 1. Pipeline Duration History Chart
        const durationCanvas = document.getElementById('durationHistoryChart');
        if (durationCanvas && runs.length > 0) {
            const reversedRuns = [...runs].reverse();
            const labels = reversedRuns.map(r => r.run_id);
            const durations = reversedRuns.map(r => r.duration);
            const bgColors = reversedRuns.map(r => r.overall_status === 'SUCCESS' ? 'rgba(37, 99, 235, 0.8)' : 'rgba(239, 68, 68, 0.8)');

            new Chart(durationCanvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Duration (seconds)',
                        data: durations,
                        backgroundColor: bgColors,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => `Duration: ${ctx.parsed.y}s`
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: '#f1f5f9' },
                            ticks: { callback: v => `${v}s` }
                        },
                        x: {
                            grid: { display: false }
                        }
                    }
                }
            });
        }

        // 2. Build Success vs Failure Doughnut Chart
        const successRateCanvas = document.getElementById('successRateChart');
        if (successRateCanvas) {
            const metricsRes = await fetch('/api/metrics');
            const metrics = await metricsRes.json();

            const successCount = metrics.success_runs || 0;
            const failedCount = metrics.failed_runs || 0;
            const total = successCount + failedCount;

            new Chart(successRateCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['Successful Builds', 'Failed Builds'],
                    datasets: [{
                        data: total === 0 ? [1, 0] : [successCount, failedCount],
                        backgroundColor: total === 0 ? ['#cbd5e1', '#f1f5f9'] : ['#10b981', '#ef4444'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '70%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 12,
                                font: { size: 12 }
                            }
                        }
                    }
                }
            });
        }

    } catch (e) {
        console.error('Chart initialization error:', e);
    }
}
