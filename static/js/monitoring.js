// Realtime Application Monitoring JavaScript

let monitoringInterval = null;

document.addEventListener('DOMContentLoaded', () => {
    fetchRealtimeMetrics();
    monitoringInterval = setInterval(fetchRealtimeMetrics, 4000);

    const manualProbeBtn = document.getElementById('manualProbeBtn');
    if (manualProbeBtn) {
        manualProbeBtn.addEventListener('click', triggerManualHealthProbe);
    }
});

async function fetchRealtimeMetrics() {
    try {
        const res = await fetch('/api/monitoring/metrics');
        if (!res.ok) return;
        const data = await res.json();

        // CPU Metric
        const cpuVal = document.getElementById('monCpuVal');
        const cpuBar = document.getElementById('monCpuBar');
        if (cpuVal && cpuBar) {
            cpuVal.textContent = `${data.cpu_percent}%`;
            cpuBar.style.width = `${Math.min(data.cpu_percent, 100)}%`;
            cpuBar.className = `progress-bar ${data.cpu_percent > 80 ? 'bg-danger' : (data.cpu_percent > 50 ? 'bg-warning' : 'bg-primary')}`;
        }

        // Memory Metric
        const memVal = document.getElementById('monMemVal');
        const memBar = document.getElementById('monMemBar');
        const memDetail = document.getElementById('monMemDetail');
        if (memVal && memBar) {
            memVal.textContent = `${data.memory_percent}%`;
            memBar.style.width = `${Math.min(data.memory_percent, 100)}%`;
            memBar.className = `progress-bar ${data.memory_percent > 85 ? 'bg-danger' : (data.memory_percent > 65 ? 'bg-warning' : 'bg-purple')}`;
            if (memDetail) {
                memDetail.textContent = `${data.memory_used_gb} GB / ${data.memory_total_gb} GB`;
            }
        }

        // Disk Metric
        const diskVal = document.getElementById('monDiskVal');
        const diskBar = document.getElementById('monDiskBar');
        const diskDetail = document.getElementById('monDiskDetail');
        if (diskVal && diskBar) {
            diskVal.textContent = `${data.disk_percent}%`;
            diskBar.style.width = `${Math.min(data.disk_percent, 100)}%`;
            if (diskDetail) {
                diskDetail.textContent = `${data.disk_used_gb} GB / ${data.disk_total_gb} GB`;
            }
        }

        // Process Memory & Uptime
        const procMem = document.getElementById('monProcMem');
        const uptimeEl = document.getElementById('monUptime');
        if (procMem) procMem.textContent = `${data.process_memory_mb} MB`;
        if (uptimeEl) uptimeEl.textContent = data.uptime_formatted;

    } catch (err) {
        console.error('Failed to fetch monitoring metrics:', err);
    }
}

async function triggerManualHealthProbe() {
    const probeBtn = document.getElementById('manualProbeBtn');
    const probeResult = document.getElementById('probeJsonViewer');
    const latencyBadge = document.getElementById('probeLatencyBadge');
    const statusBadge = document.getElementById('probeStatusBadge');

    if (probeBtn) probeBtn.disabled = true;
    const start = performance.now();

    try {
        const res = await fetch('/health');
        const latency = (performance.now() - start).toFixed(2);
        const data = await res.json();

        if (latencyBadge) latencyBadge.textContent = `${latency} ms`;
        if (statusBadge) {
            statusBadge.className = res.ok ? 'badge-status badge-success' : 'badge-status badge-danger';
            statusBadge.textContent = `HTTP ${res.status} ${res.ok ? 'OK' : 'ERROR'}`;
        }
        if (probeResult) {
            probeResult.textContent = JSON.stringify(data, null, 2);
        }
        showToast('success', `Health probe responded in ${latency}ms`);
    } catch (err) {
        if (statusBadge) {
            statusBadge.className = 'badge-status badge-danger';
            statusBadge.textContent = 'Connection Error';
        }
        if (probeResult) {
            probeResult.textContent = `Error: ${err.message}`;
        }
    } finally {
        if (probeBtn) probeBtn.disabled = false;
    }
}
