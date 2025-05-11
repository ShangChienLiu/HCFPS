/**
 * Simple debug overlay to diagnose UI issues
 * This will add a small debugging panel to the page
 */

// Create and append the debug panel once DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Create debug panel
    const debugPanel = document.createElement('div');
    debugPanel.id = 'debug-panel';
    debugPanel.style.cssText = `
        position: fixed;
        bottom: 10px;
        right: 10px;
        background: rgba(0, 0, 0, 0.8);
        color: #4fc3f7;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 12px;
        z-index: 9999;
        max-width: 400px;
        max-height: 300px;
        overflow: auto;
        display: none;
    `;
    
    // Create toggle button
    const toggleButton = document.createElement('button');
    toggleButton.innerText = 'Debug';
    toggleButton.style.cssText = `
        position: fixed;
        bottom: 10px;
        right: 10px;
        background: #4361ee;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px 10px;
        z-index: 10000;
        cursor: pointer;
    `;
    
    // Create test controls
    const testControls = document.createElement('div');
    testControls.innerHTML = `
        <div style="margin-bottom: 10px;">
            <button id="test-ui-btn" style="padding: 3px 8px; margin-right: 5px;">Test UI</button>
            <button id="fix-ui-btn" style="padding: 3px 8px;">Fix UI</button>
        </div>
        <div style="margin-bottom: 10px;">
            <button id="test-api-btn" style="padding: 3px 8px; margin-right: 5px;">Test API</button>
            <button id="debug-path-btn" style="padding: 3px 8px;">Force Path Error</button>
        </div>
    `;
    
    // Create log output
    const logOutput = document.createElement('div');
    logOutput.id = 'debug-log';
    
    // Append elements
    debugPanel.appendChild(testControls);
    debugPanel.appendChild(logOutput);
    document.body.appendChild(toggleButton);
    document.body.appendChild(debugPanel);
    
    // Toggle panel visibility
    toggleButton.addEventListener('click', function() {
        if (debugPanel.style.display === 'none') {
            debugPanel.style.display = 'block';
            toggleButton.innerText = 'Hide';
        } else {
            debugPanel.style.display = 'none';
            toggleButton.innerText = 'Debug';
        }
    });
    
    // Log function
    window.debugLog = function(message) {
        const logItem = document.createElement('div');
        logItem.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
        logItem.style.paddingBottom = '5px';
        logItem.style.marginBottom = '5px';
        
        // Format timestamp
        const now = new Date();
        const time = `${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}.${now.getMilliseconds()}`;
        
        logItem.innerHTML = `<span style="color: #aaa;">[${time}]</span> ${message}`;
        
        const log = document.getElementById('debug-log');
        if (log) {
            log.appendChild(logItem);
            log.scrollTop = log.scrollHeight;
        }
    };
    
    // Test UI button
    document.getElementById('test-ui-btn').addEventListener('click', function() {
        debugLog('Testing UI updates...');
        const rows = document.querySelectorAll('#task-container tr');
        
        if (rows.length === 0) {
            debugLog('<span style="color: #ff5252;">ERROR: No task rows found!</span>');
            return;
        }
        
        rows.forEach((row, index) => {
            const statusIcon = row.querySelector('.status-icon');
            const statusText = row.querySelector('.status-text');
            const cloudPathInput = row.querySelector('.cloud-path-input');
            const sourcePathField = row.querySelector('.source-path');
            
            debugLog(`Row ${index}: Status elements: ${!!statusIcon && !!statusText ? '✓' : '✗'}`);
            
            if (statusIcon && statusText) {
                // Save current state
                const originalIcon = statusIcon.textContent;
                const originalText = statusText.textContent;
                const originalClass = statusIcon.className;
                
                // Test update
                statusIcon.className = 'status-icon status-error';
                statusIcon.textContent = '❌';
                statusText.textContent = 'TEST UI ERROR';
                
                debugLog(`Row ${index}: UI updated to error state`);
                
                // After 2 seconds, revert
                setTimeout(() => {
                    statusIcon.className = originalClass;
                    statusIcon.textContent = originalIcon;
                    statusText.textContent = originalText;
                    debugLog(`Row ${index}: UI restored to original state`);
                }, 2000);
            }
        });
    });
    
    // Fix UI button
    document.getElementById('fix-ui-btn').addEventListener('click', function() {
        debugLog('Attempting UI fix...');
        const rows = document.querySelectorAll('#task-container tr');
        
        if (rows.length === 0) {
            debugLog('<span style="color: #ff5252;">ERROR: No task rows found!</span>');
            // Create a new row if none exist
            if (window.createTaskCard && document.getElementById('task-container')) {
                const newRow = window.createTaskCard();
                document.getElementById('task-container').appendChild(newRow);
                debugLog('Created a new task row');
            }
            return;
        }
        
        rows.forEach((row, index) => {
            // Ensure all UI elements exist
            const statusContainer = row.querySelector('.status');
            
            if (!statusContainer) {
                debugLog(`Row ${index}: Missing status container - recreating`);
                
                // Find the status cell
                const statusCell = row.querySelector('.col-status');
                if (statusCell) {
                    statusCell.innerHTML = `
                        <div class="status">
                            <span class="status-icon status-pending">⏳</span>
                            <span class="status-text">Waiting</span>
                        </div>
                    `;
                    debugLog(`Row ${index}: Rebuilt status container`);
                }
            }
        });
    });
    
    // Test API button
    document.getElementById('test-api-btn').addEventListener('click', async function() {
        debugLog('Testing API connectivity...');
        
        try {
            const response = await fetch('/api/diagnostic', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ test: true, timestamp: Date.now() })
            });
            
            if (response.ok) {
                const data = await response.json();
                debugLog(`API test success: ${JSON.stringify(data).substring(0, 100)}...`);
                window.apiConnectivity = true;
            } else {
                debugLog(`API error: ${response.status} ${response.statusText}`);
                window.apiConnectivity = false;
            }
        } catch (error) {
            debugLog(`API connection error: ${error.message}`);
            window.apiConnectivity = false;
        }
    });
    
    // Debug path button
    document.getElementById('debug-path-btn').addEventListener('click', function() {
        debugLog('Forcing path error UI...');
        const rows = document.querySelectorAll('#task-container tr');
        
        if (rows.length === 0) {
            debugLog('<span style="color: #ff5252;">ERROR: No task rows found!</span>');
            return;
        }
        
        rows.forEach((row, index) => {
            const statusIcon = row.querySelector('.status-icon');
            const statusText = row.querySelector('.status-text');
            const sourceType = row.querySelector('.source-type-radio[value="path"]');
            const sourcePathField = row.querySelector('.source-path');
            const cloudPathInput = row.querySelector('.cloud-path-input');
            
            // Switch to path mode
            if (sourceType && !sourceType.checked) {
                sourceType.checked = true;
                debugLog(`Row ${index}: Switched to path mode`);
                
                // Show cloud path input
                if (cloudPathInput) {
                    cloudPathInput.classList.remove('hidden');
                    const fileUpload = row.querySelector('.file-upload-container');
                    if (fileUpload) fileUpload.classList.add('hidden');
                }
            }
            
            // Set an invalid path
            if (sourcePathField) {
                sourcePathField.value = 's3://invalid-bucket';
                debugLog(`Row ${index}: Set invalid path`);
                
                // Manually update UI
                if (statusIcon && statusText) {
                    statusIcon.className = 'status-icon status-error';
                    statusIcon.textContent = '❌';
                    statusText.textContent = 'Missing object key';
                    row.dataset.cloudPathValid = 'false';
                    debugLog(`Row ${index}: Manually set error state`);
                }
                
                // Trigger input event to validate
                const event = new Event('input', { bubbles: true });
                sourcePathField.dispatchEvent(event);
                debugLog(`Row ${index}: Triggered validation`);
            }
        });
    });
    
    // Log init complete
    setTimeout(() => {
        debugLog('Debug panel initialized');
    }, 500);
}); 