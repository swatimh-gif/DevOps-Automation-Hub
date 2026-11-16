// Pipeline Execution JavaScript

let isPipelineRunning = false;

async function triggerPipeline(simulateFailure = false) {
    if (isPipelineRunning) return;

    isPipelineRunning = true;
    const runBtn = document.getElementById('runPipelineBtn');
    const failBtn = document.getElementById('simulateFailBtn');
    const terminal = document.getElementById('pipelineTerminal');
    const statusBanner = document.getElementById('pipelineStatusBanner');
    const connectorFill = document.getElementById('connectorFill');

    if (runBtn) runBtn.disabled = true;
    if (failBtn) failBtn.disabled = true;

    // Reset steps UI
    resetPipelineSteps();
    if (terminal) terminal.innerHTML = '';
    if (connectorFill) connectorFill.style.width = '10%';

    appendTerminalLog(`[INIT] Initializing CI/CD Pipeline run (Mode: ${simulateFailure ? 'Failure Simulation' : 'Standard'} )...`, 'info');

    // Step 1: Start & Source
    setStepState('step-source', 'running', 'Verifying repository...');
    if (connectorFill) connectorFill.style.width = '20%';

    try {
        // Send request to backend
        appendTerminalLog(`[API] Dispatching execution request to /api/pipeline/run...`, 'info');

        const response = await fetch('/api/pipeline/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                trigger_type: simulateFailure ? 'Manual (Failure Demo)' : 'Manual Dashboard',
                simulate_failure: simulateFailure
            })
        });

        const data = await response.json();

        // Process source check state
        if (data.source === 'PASSED') {
            setStepState('step-source', 'completed', 'Source Verified');
            appendTerminalLog(`[SOURCE] Git commit hash & working tree verified.`, 'success');
        } else {
            setStepState('step-source', 'failed', 'Source Failed');
        }

        // Step 2: Dependencies
        if (connectorFill) connectorFill.style.width = '35%';
        setStepState('step-dep', 'running', 'Checking packages...');
        await new Promise(r => setTimeout(r, 400));

        if (data.dependencies === 'PASSED') {
            setStepState('step-dep', 'completed', 'Dependencies OK');
            appendTerminalLog(`[DEPS] Verified core dependencies (Flask, Pytest, Requests, Psutil).`, 'success');
        } else {
            setStepState('step-dep', 'failed', 'Missing Packages');
        }

        // Step 3: Automated Testing
        if (connectorFill) connectorFill.style.width = '55%';
        setStepState('step-test', 'running', 'Executing Pytest...');
        appendTerminalLog(`[TEST] Running automated pytest suite on tests/ directory...`, 'info');
        await new Promise(r => setTimeout(r, 500));

        if (data.tests === 'PASSED') {
            setStepState('step-test', 'completed', `${data.tests_passed} Passed`);
            appendTerminalLog(`[TEST] Pytest completed successfully! ${data.tests_passed} tests passed.`, 'success');
        } else {
            setStepState('step-test', 'failed', `${data.tests_failed} Failed`);
            appendTerminalLog(`[TEST] Automated test suite FAILED! ${data.tests_failed} test assertion failure(s).`, 'error');
            appendTerminalLog(`[SECURITY/CI] Pipeline halted! Aborting Docker and Deployment stages to prevent faulty release.`, 'error');
        }

        // Step 4: Docker Containerization
        if (connectorFill) connectorFill.style.width = '75%';
        if (data.docker === 'PASSED') {
            setStepState('step-docker', 'completed', 'Image Built');
            appendTerminalLog(`[DOCKER] Docker image 'devops-automation-hub:latest' built.`, 'success');
        } else if (data.docker === 'SKIPPED') {
            setStepState('step-docker', 'skipped', 'Skipped (No Daemon)');
            appendTerminalLog(`[DOCKER] Stage SKIPPED: Docker engine/daemon not detected on host system.`, 'warning');
        } else {
            setStepState('step-docker', 'failed', 'Build Error');
            appendTerminalLog(`[DOCKER] Image build failed.`, 'error');
        }

        // Step 5: Deployment
        if (connectorFill) connectorFill.style.width = '88%';
        if (data.deployment === 'PASSED') {
            setStepState('step-deploy', 'completed', 'Staging Verified');
            appendTerminalLog(`[DEPLOY] Release artifact deployed to Staging Target.`, 'success');
        } else if (data.deployment === 'PENDING') {
            setStepState('step-deploy', 'skipped', 'Pending / Config');
            appendTerminalLog(`[DEPLOY] Deployment pending: No production hosting webhook configured.`, 'warning');
        } else if (data.deployment === 'SKIPPED') {
            setStepState('step-deploy', 'skipped', 'Skipped');
            appendTerminalLog(`[DEPLOY] Deployment skipped due to prior failure.`, 'warning');
        } else {
            setStepState('step-deploy', 'failed', 'Deploy Failed');
        }

        // Step 6: Health Check
        if (connectorFill) connectorFill.style.width = '100%';
        if (data.health === 'HEALTHY') {
            setStepState('step-health', 'completed', 'Service Healthy');
            appendTerminalLog(`[HEALTH] /health probe responded with HTTP 200 OK.`, 'success');
        } else if (data.health === 'SKIPPED') {
            setStepState('step-health', 'skipped', 'Skipped');
        } else {
            setStepState('step-health', 'failed', 'Degraded');
            appendTerminalLog(`[HEALTH] Service health check returned unhealthy status.`, 'error');
        }

        // Final Banner Update
        if (data.status === 'SUCCESS') {
            appendTerminalLog(`[FINISH] Pipeline Run ${data.run_id} completed successfully in ${data.duration}s!`, 'success');
            showToast('success', `Pipeline ${data.run_id} succeeded in ${data.duration}s!`);
            if (statusBanner) {
                statusBanner.className = 'alert alert-success d-flex align-items-center gap-2 mb-4';
                statusBanner.innerHTML = `<i class="bi bi-check-circle-fill fs-5"></i> <div><strong>Pipeline Run Succeeded (${data.run_id}):</strong> All tests passed and health check verified in ${data.duration}s.</div>`;
                statusBanner.classList.remove('d-none');
            }
        } else {
            appendTerminalLog(`[FINISH] Pipeline Run ${data.run_id} FAILED after ${data.duration}s.`, 'error');
            showToast('danger', `Pipeline ${data.run_id} failed (${data.reason || 'Check logs'})`);
            if (statusBanner) {
                statusBanner.className = 'alert alert-danger d-flex align-items-center gap-2 mb-4';
                statusBanner.innerHTML = `<i class="bi bi-x-circle-fill fs-5"></i> <div><strong>Pipeline Run Failed (${data.run_id}):</strong> Testing or build stage failed. Subsequent deployment was aborted.</div>`;
                statusBanner.classList.remove('d-none');
            }
        }

        // Auto reload after 2.5 seconds to show new run in history table
        setTimeout(() => {
            window.location.reload();
        }, 3000);

    } catch (err) {
        appendTerminalLog(`[FATAL] Error triggering pipeline: ${err.message}`, 'error');
        showToast('danger', `Connection error: ${err.message}`);
    } finally {
        isPipelineRunning = false;
        if (runBtn) runBtn.disabled = false;
        if (failBtn) failBtn.disabled = false;
    }
}

function resetPipelineSteps() {
    ['step-source', 'step-dep', 'step-test', 'step-docker', 'step-deploy', 'step-health'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            const node = el.querySelector('.step-node');
            const sub = el.querySelector('.step-status-sub');
            if (node) node.className = 'step-node';
            if (sub) sub.textContent = 'Pending';
        }
    });
}

function setStepState(stepId, state, subtext) {
    const el = document.getElementById(stepId);
    if (!el) return;
    const node = el.querySelector('.step-node');
    const sub = el.querySelector('.step-status-sub');

    if (node) {
        node.className = `step-node ${state}`;
        if (state === 'completed') {
            node.innerHTML = '<i class="bi bi-check-lg"></i>';
        } else if (state === 'failed') {
            node.innerHTML = '<i class="bi bi-x-lg"></i>';
        } else if (state === 'skipped') {
            node.innerHTML = '<i class="bi bi-dash-lg"></i>';
        } else if (state === 'running') {
            node.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';
        }
    }
    if (sub && subtext) sub.textContent = subtext;
}

function appendTerminalLog(message, type = 'info') {
    const terminal = document.getElementById('pipelineTerminal');
    if (!terminal) return;

    const p = document.createElement('p');
    p.className = `log-line log-${type}`;
    p.textContent = message;
    terminal.appendChild(p);
    terminal.scrollTop = terminal.scrollHeight;
}
