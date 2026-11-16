// Main JavaScript for DevOps Automation Hub

document.addEventListener('DOMContentLoaded', () => {
    // Mobile sidebar toggle
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
    }

    // Initialize global health ping
    checkGlobalHealth();
    setInterval(checkGlobalHealth, 15000);
});

// Checks the /health endpoint and updates the live pill
async function checkGlobalHealth() {
    const pill = document.getElementById('globalHealthPill');
    const dot = document.getElementById('globalHealthDot');
    const text = document.getElementById('globalHealthText');

    if (!pill || !dot || !text) return;

    try {
        const res = await fetch('/health');
        if (res.ok) {
            const data = await res.json();
            if (data.status === 'healthy') {
                dot.className = 'pulse-dot pulse-green';
                text.textContent = 'System Healthy';
                pill.className = 'badge-status badge-success';
            } else {
                dot.className = 'pulse-dot pulse-amber';
                text.textContent = 'Degraded';
                pill.className = 'badge-status badge-warning';
            }
        } else {
            dot.className = 'pulse-dot pulse-red';
            text.textContent = `Offline (${res.status})`;
            pill.className = 'badge-status badge-danger';
        }
    } catch (err) {
        dot.className = 'pulse-dot pulse-red';
        text.textContent = 'Unreachable';
        pill.className = 'badge-status badge-danger';
    }
}

// Global Toast notification utility
function showToast(type, message, title = 'DevOps Hub') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    const toastEl = document.createElement('div');
    const bgClass = type === 'success' ? 'text-bg-success' : (type === 'danger' ? 'text-bg-danger' : 'text-bg-primary');
    toastEl.className = `toast align-items-center ${bgClass} border-0 shadow-lg`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');

    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}:</strong> ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    container.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}
