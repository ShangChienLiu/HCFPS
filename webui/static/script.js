document.addEventListener('DOMContentLoaded', function() {
    // Add version/timestamp to verify script loading
    const scriptVersion = Date.now();
    console.log('Script initialized with version timestamp:', scriptVersion);
    
    // Debug function to force update UI on page load
    window.debugUI = function() {
        console.log('DEBUG: Testing UI updates');
        const rows = document.querySelectorAll('#task-container tr');
        rows.forEach((row, index) => {
            const statusIcon = row.querySelector('.status-icon');
            const statusText = row.querySelector('.status-text');
            
            // Get references to key fields
            const cloudPathInput = row.querySelector('.cloud-path-input');
            const sourcePathField = row.querySelector('.source-path');
            const sourceValue = sourcePathField ? sourcePathField.value : 'N/A';
            
            console.log(`DEBUG: Row ${index} - Cloud path input: ${cloudPathInput ? 'Found' : 'Not Found'}`);
            console.log(`DEBUG: Row ${index} - Status icons: ${statusIcon ? 'Found' : 'Not Found'}`);
            console.log(`DEBUG: Row ${index} - Source path: ${sourceValue}`);
            
            if (statusIcon && statusText) {
                // Flash test status
                statusIcon.className = 'status-icon status-error';
                statusIcon.textContent = '❌';
                statusText.textContent = 'TEST ERROR';
                
                // After 2 seconds, revert
                setTimeout(() => {
                    statusIcon.className = 'status-icon status-success';
                    statusIcon.textContent = '✅';
                    statusText.textContent = 'UI Works!';
                }, 2000);
            }
        });
    };
    
    // Run the debugUI function after a delay
    setTimeout(window.debugUI, 1000);
    
    // Test API connectivity on startup
    testApiConnectivity();
    
    // DOM elements
    const taskContainer = document.getElementById('task-container');
    const addTaskBtn = document.getElementById('add-task-btn');
    const submitAllBtn = document.getElementById('submit-all-btn');
    const alertBox = document.getElementById('alert');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    console.log('DOM loaded', {
        taskContainer: !!taskContainer,
        addTaskBtn: !!addTaskBtn,
        submitAllBtn: !!submitAllBtn
    });
    
    // Check if elements were found
    if (!addTaskBtn) {
        console.error('Add Task button not found');
    } else {
        // Add event listener for the Add Task button
        addTaskBtn.addEventListener('click', function() {
            console.log('Add Task button clicked');
            const newRow = window.createTaskCard();
            taskContainer.appendChild(newRow);
        });
    }
    
    if (!taskContainer) {
        console.error('Task container not found');
    }
    
    // Session ID for grouping uploads
    const sessionId = 'session-' + Date.now();
    
    // Show/hide loading overlay
    function showLoading() {
        loadingOverlay.style.display = 'flex';
    }
    
    function hideLoading() {
        loadingOverlay.style.display = 'none';
    }
    
    // Show alert messages
    function showAlert(message, isError = false) {
        alertBox.textContent = message;
        alertBox.style.display = 'block';
        
        if (isError) {
            alertBox.className = 'alert alert-error';
        } else {
            alertBox.className = 'alert alert-success';
        }
        
        setTimeout(() => {
            alertBox.style.display = 'none';
        }, 5000);
    }
    
    // Create a new task row
    window.createTaskCard = function() {
        const taskId = 'task-' + Date.now();
        const row = document.createElement('tr');
        row.id = taskId;
        
        // Source cell
        const sourceCell = document.createElement('td');
        sourceCell.className = 'col-source';
        sourceCell.innerHTML = `
            <div class="radio-group">
                <label class="radio-label">
                    <input type="radio" name="source-${taskId}" class="source-type-radio" value="file" checked>
                    File Upload
                </label>
                <label class="radio-label">
                    <input type="radio" name="source-${taskId}" class="source-type-radio" value="path">
                    Cloud Path
                </label>
            </div>
            <div class="file-upload-container">
                <div class="file-input">
                    <div class="file-input-button">Choose a file</div>
                    <input type="file" class="source-file" data-type="local">
                </div>
                <select class="upload-to">
                    <option value="">Select platform</option>
                    <option value="aws">AWS</option>
                    <option value="gcp">Google Cloud</option>
                </select>
            </div>
            <div class="cloud-path-input hidden">
                <input type="text" class="source-path" placeholder="s3://bucket/key or gs://bucket/object">
            </div>
        `;
        
        // Action cell
        const actionCell = document.createElement('td');
        actionCell.className = 'col-action';
        actionCell.innerHTML = `
            <select class="action">
                <option value="">Select action</option>
                <option value="convert_h265">Convert to H.265</option>
                <option value="compress">Compress to ZIP</option>
                <option value="rename">Rename</option>
            </select>
        `;
        
        // Output path cell
        const outputCell = document.createElement('td');
        outputCell.className = 'col-output';
        outputCell.innerHTML = `
            <input type="text" class="output-path" placeholder="s3://bucket/key or gs://bucket/object">
        `;
        
        // Status cell
        const statusCell = document.createElement('td');
        statusCell.className = 'col-status';
        statusCell.innerHTML = `
            <div class="status">
                <span class="status-icon status-pending">⏳</span>
                <span class="status-text">Waiting</span>
            </div>
        `;
        
        // Delete cell
        const deleteCell = document.createElement('td');
        deleteCell.className = 'col-delete';
        deleteCell.innerHTML = `
            <button class="btn-icon delete-task">
                <i class="fas fa-trash"></i>
            </button>
        `;
        
        // Append cells to row
        row.appendChild(sourceCell);
        row.appendChild(actionCell);
        row.appendChild(outputCell);
        row.appendChild(statusCell);
        row.appendChild(deleteCell);
        
        setupTaskCardListeners(row);
        return row;
    };
    
    // Set up event listeners for a task row
    function setupTaskCardListeners(row) {
        // Elements
        const sourceTypeRadios = row.querySelectorAll('.source-type-radio');
        const sourceFile = row.querySelector('.source-file');
        const fileInputButton = row.querySelector('.file-input-button');
        const sourcePath = row.querySelector('.source-path');
        const uploadToSelect = row.querySelector('.upload-to');
        const cloudPathInput = row.querySelector('.cloud-path-input');
        const fileUploadContainer = row.querySelector('.file-upload-container');
        const actionSelect = row.querySelector('.action');
        const outputPath = row.querySelector('.output-path');
        const deleteBtn = row.querySelector('.delete-task');
        const statusIcon = row.querySelector('.status-icon');
        const statusText = row.querySelector('.status-text');
        
        // Source type radio buttons
        sourceTypeRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'file') {
                    // Show file upload, hide path input
                    fileUploadContainer.classList.remove('hidden');
                    cloudPathInput.classList.add('hidden');
                } else {
                    // Show path input, hide file upload
                    fileUploadContainer.classList.add('hidden');
                    cloudPathInput.classList.remove('hidden');
                    sourcePath.focus();
                }
                validateTask(row);
            });
        });
        
        // File selection with format validation
        sourceFile.addEventListener('change', function() {
            if (this.files.length > 0) {
                const file = this.files[0];
                const fileName = file.name;
                const fileExt = fileName.split('.').pop().toLowerCase();
                
                // Update file button display
                fileInputButton.textContent = fileName.length > 30 ? 
                    fileName.substring(0, 27) + '...' : 
                    fileName;
                
                // Validate file format
                const validFormats = ['bag', 'mcap', 'h5', 'hdf5', 'rosbag'];
                if (!validFormats.includes(fileExt)) {
                    row.dataset.fileValid = 'false';
                    updateStatus(row, 'error', 'Invalid file format');
                } else {
                    row.dataset.fileValid = 'true';
                    updateStatus(row, 'success', 'File valid');
                }
                
                validateTask(row);
            }
        });
        
        // Cloud Path validation with debounce
        let cloudPathTimeout;
        let outputPathTimeout;
        
        sourcePath.addEventListener('input', function() {
            const path = this.value.trim().toLowerCase();
            const statusIcon = row.querySelector('.status-icon');
            const statusText = row.querySelector('.status-text');
            
            // Reset validation timeout
            clearTimeout(cloudPathTimeout);
            
            console.log('Source path input changed:', path);
            
            // Force update UI elements directly - emergency fix
            function updatePathStatus(icon, message, iconClass) {
                console.log(`UPDATING UI: ${message}`);
                if (statusIcon) {
                    statusIcon.className = `status-icon ${iconClass}`;
                    statusIcon.textContent = icon;
                } else {
                    console.error('Status icon element not found');
                }
                
                if (statusText) {
                    statusText.textContent = message;
                } else {
                    console.error('Status text element not found');
                }
                
                // Set validation state
                row.dataset.cloudPathValid = iconClass === 'status-success' ? 'true' : 'false';
                
                // Show this in console for debugging
                console.log(`UI updated: Icon=${icon}, Message=${message}, Class=${iconClass}`);
            }
            
            // Skip validation if path is empty
            if (!path) {
                updatePathStatus('⏳', 'Enter path', 'status-pending');
                validateTask(row);
                return;
            }
            
            // Skip validation if path is not a cloud path
            if (!path.startsWith('s3://') && !path.startsWith('gs://')) {
                updatePathStatus('❌', 'Invalid prefix', 'status-error');
                validateTask(row);
                return;
            }
            
            // Check for incomplete path
            const isS3Path = path.startsWith('s3://');
            const isGsPath = path.startsWith('gs://');
            
            // Extract parts
            let parts = [];
            if (isS3Path) {
                parts = path.substring(5).split('/', 2);
            } else if (isGsPath) {
                parts = path.substring(5).split('/', 2);
            }
            
            console.log('Path parts:', parts);
            
            // Immediately validate path format
            if (parts.length < 2 || !parts[0]) {
                // Path is incomplete - bucket only or empty bucket
                updatePathStatus('❌', 'Need bucket/key', 'status-error');
                validateTask(row);
                console.log('Path incomplete (no bucket/key)');
                return;
            } else if (!parts[1]) {
                // Path has bucket but no key
                updatePathStatus('❌', 'Missing object key', 'status-error');
                validateTask(row);
                console.log('Path incomplete (no key)');
                return;
            }
            
            // Show checking status for valid format paths
            updatePathStatus('⏳', 'Checking...', 'status-pending');
            
            // Allow the user to override the API validation if needed
            // Set a manual validation flag to bypass API checks
            const manualValidationBtn = row.querySelector('.manual-validate');
            if (!manualValidationBtn) {
                // Create a button to manually validate if it doesn't exist
                const validateBtn = document.createElement('button');
                validateBtn.className = 'manual-validate';
                validateBtn.innerHTML = '<small>Force validate</small>';
                validateBtn.style.marginLeft = '5px';
                validateBtn.style.padding = '1px 3px';
                validateBtn.style.fontSize = '10px';
                validateBtn.style.backgroundColor = '#f8f9fa';
                validateBtn.style.border = '1px solid #ced4da';
                validateBtn.style.borderRadius = '2px';
                validateBtn.style.display = 'none';
                
                validateBtn.onclick = function(e) {
                    e.preventDefault();
                    console.log('Manual validation clicked');
                    statusIcon.className = 'status-icon status-warning';
                    statusIcon.textContent = '⚠️';
                    statusText.textContent = 'Manually validated';
                    row.dataset.cloudPathValid = 'warning';
                    this.style.display = 'none';
                    validateTask(row);
                };
                
                const statusContainer = row.querySelector('.status');
                statusContainer.appendChild(validateBtn);
            }
            
            // Schedule validation with API
            console.log('Setting timeout to validate path');
            cloudPathTimeout = setTimeout(() => {
                console.log('Timeout triggered, validating cloud path');
                validateCloudPath(path, row);
                
                // Show manual validation button after a delay if still checking
                setTimeout(() => {
                    const manualBtn = row.querySelector('.manual-validate');
                    if (manualBtn && statusText.textContent === 'Checking...') {
                        manualBtn.style.display = 'inline';
                    }
                }, 3000);
            }, 800); // 800ms delay
            
            validateTask(row);
        });
        
        // Output path validation with debounce
        outputPath.addEventListener('input', function() {
            const path = this.value.trim().toLowerCase();
            const statusIcon = row.querySelector('.status-icon');
            const statusText = row.querySelector('.status-text');
            
            // Reset validation timeout
            clearTimeout(outputPathTimeout);
            
            console.log('Output path input changed:', path);
            
            // Skip validation if path is empty
            if (!path) {
                validateTask(row);
                return;
            }
            
            // Skip validation if path is not a cloud path
            if (!path.startsWith('s3://') && !path.startsWith('gs://')) {
                row.dataset.outputPathValid = 'false';
                if (Array.from(sourceTypeRadios).find(r => r.checked).value === 'file') {
                    statusIcon.className = 'status-icon status-error';
                    statusIcon.textContent = '❌';
                    statusText.textContent = 'Invalid output prefix';
                }
                validateTask(row);
                return;
            }
            
            // Always validate output path, regardless of source type (file or cloud path)
            // Flag that we're validating output path
            row.dataset.validatingOutput = 'true';
            
            // For file upload mode, update status to show we're checking output
            const fileMode = Array.from(sourceTypeRadios).find(r => r.checked).value === 'file';
            
            // Check for incomplete path for bucket validation
            const bucketPath = path.substring(0, path.lastIndexOf('/') || path.length);
            const isS3Path = bucketPath.startsWith('s3://');
            const isGsPath = bucketPath.startsWith('gs://');
            
            // Extract bucket name
            let bucket = '';
            if (isS3Path) {
                bucket = bucketPath.substring(5);
            } else if (isGsPath) {
                bucket = bucketPath.substring(5);
            }
            
            // Check output path format
            const parts = path.substring(path.startsWith('s3://') ? 5 : 5).split('/', 2);
            if (parts.length < 2 || !parts[0]) {
                // Output path is incomplete
                row.dataset.outputPathValid = 'false';
                if (fileMode) {
                    statusIcon.className = 'status-icon status-error';
                    statusIcon.textContent = '❌';
                    statusText.textContent = 'Invalid output format';
                }
                row.dataset.validatingOutput = 'false';
                validateTask(row);
                return;
            } else if (!parts[1]) {
                // Output path has bucket but no key
                row.dataset.outputPathValid = 'false';
                if (fileMode) {
                    statusIcon.className = 'status-icon status-error';
                    statusIcon.textContent = '❌';
                    statusText.textContent = 'Missing output key';
                }
                row.dataset.validatingOutput = 'false';
                validateTask(row);
                return;
            }
            
            if (fileMode) {
                statusIcon.className = 'status-icon status-pending';
                statusIcon.textContent = '⏳';
                statusText.textContent = 'Checking output...';
            }
            
            // Allow manual validation for output path too
            const manualOutputValidateBtn = row.querySelector('.manual-output-validate');
            if (!manualOutputValidateBtn) {
                // Create a button to manually validate if it doesn't exist
                const validateBtn = document.createElement('button');
                validateBtn.className = 'manual-output-validate';
                validateBtn.innerHTML = '<small>Force output</small>';
                validateBtn.style.marginLeft = '5px';
                validateBtn.style.padding = '1px 3px';
                validateBtn.style.fontSize = '10px';
                validateBtn.style.backgroundColor = '#f8f9fa';
                validateBtn.style.border = '1px solid #ced4da';
                validateBtn.style.borderRadius = '2px';
                validateBtn.style.display = 'none';
                
                validateBtn.onclick = function(e) {
                    e.preventDefault();
                    console.log('Manual output validation clicked');
                    if (fileMode) {
                        statusIcon.className = 'status-icon status-warning';
                        statusIcon.textContent = '⚠️';
                        statusText.textContent = 'Output force validated';
                    }
                    row.dataset.outputPathValid = 'warning';
                    row.dataset.validatingOutput = 'false';
                    this.style.display = 'none';
                    validateTask(row);
                };
                
                const statusContainer = row.querySelector('.status');
                statusContainer.appendChild(validateBtn);
            }
            
            // Debounce validation to wait until user stops typing
            console.log('Setting timeout to validate output path');
            outputPathTimeout = setTimeout(() => {
                console.log('Timeout triggered, validating output path');
                validateOutputPath(path, row);
                
                // Show manual validation button after a delay if still checking
                setTimeout(() => {
                    const manualBtn = row.querySelector('.manual-output-validate');
                    if (manualBtn && statusText.textContent === 'Checking output...' && fileMode) {
                        manualBtn.style.display = 'inline';
                    }
                }, 3000);
            }, 800); // 800ms delay
            
            validateTask(row);
        });
        
        // Other input changes
        uploadToSelect.addEventListener('change', () => validateTask(row));
        actionSelect.addEventListener('change', () => validateTask(row));
        
        // Delete button
        deleteBtn.addEventListener('click', function() {
            row.remove();
        });
    }
    
    // Validate a cloud path exists
    async function validateCloudPath(path, row) {
        const statusIcon = row.querySelector('.status-icon');
        const statusText = row.querySelector('.status-text');
        
        console.log('Starting cloud path validation for:', path);
        
        // First check if we have API connectivity
        if (window.apiConnectivity === false) {
            console.log('Skipping API validation due to connectivity issues');
            row.dataset.cloudPathValid = 'warning';
            statusIcon.className = 'status-icon status-warning';
            statusIcon.textContent = '⚠️';
            statusText.textContent = 'API unavailable';
            validateTask(row);
            return;
        }
        
        try {
            // Path format validation
            const isS3Path = path.startsWith('s3://');
            const isGsPath = path.startsWith('gs://');
            
            // Extract parts
            let parts = [];
            if (isS3Path) {
                parts = path.substring(5).split('/', 2);
            } else if (isGsPath) {
                parts = path.substring(5).split('/', 2);
            }
            
            console.log('validateCloudPath parts:', parts);
            
            // Path must have bucket/key parts
            if (parts.length < 2 || !parts[0] || !parts[1]) {
                row.dataset.cloudPathValid = 'false';
                statusIcon.className = 'status-icon status-warning';
                statusIcon.textContent = '⚠️';
                statusText.textContent = 'Incomplete path';
                validateTask(row);
                console.log('Path format invalid, not making API call');
                return;
            }
            
            console.log('Making API call to validate path');
            
            // Create a promise that rejects after a timeout
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('API request timeout')), 5000); // 5 second timeout
            });
            
            // Race the fetch against the timeout
            const response = await Promise.race([
                fetch('/api/validate_path', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ path })
                }),
                timeoutPromise
            ]);
            
            console.log('API response status:', response.status);
            
            if (!response.ok) {
                console.error('API error:', response.status);
                throw new Error('API error: ' + response.status);
            }
            
            const result = await response.json();
            console.log('API response data:', result);
            
            if (result.success) {
                if (result.exists) {
                    // Path exists
                    row.dataset.cloudPathValid = 'true';
                    statusIcon.className = 'status-icon status-success';
                    statusIcon.textContent = '✅';
                    statusText.textContent = 'Source valid';
                } else {
                    // Path format valid but does not exist
                    row.dataset.cloudPathValid = 'false';
                    statusIcon.className = 'status-icon status-error';
                    statusIcon.textContent = '❌';
                    
                    // Check for specific error reasons
                    if (result.reason === 'object_not_found') {
                        statusText.textContent = 'File not found';
                    } else if (result.reason === 'bucket_not_found') {
                        statusText.textContent = 'Bucket not found';
                    } else if (result.reason === 'access_denied') {
                        statusText.textContent = 'Access denied';
                    } else {
                        statusText.textContent = 'Source not found';
                    }
                    
                    console.error('Path validation failed:', result.error || 'File not found');
                }
            } else {
                // Error in validation
                row.dataset.cloudPathValid = 'false';
                statusIcon.className = 'status-icon status-error';
                statusIcon.textContent = '❌';
                
                // Check for specific error types
                if (result.client_status === 'not_initialized') {
                    statusText.textContent = 'Missing credentials';
                } else if (result.validation_error === 'invalid_format') {
                    statusText.textContent = 'Invalid format';
                } else {
                    statusText.textContent = 'Validation error';
                }
                
                console.error('Path validation error:', result.error);
            }
        } catch (error) {
            row.dataset.cloudPathValid = 'false';
            console.error('Path validation error:', error);
            statusIcon.className = 'status-icon status-error';
            statusIcon.textContent = '❌';
            
            // Handle specific error types
            if (error.message === 'API request timeout') {
                statusText.textContent = 'Server timeout';
                console.error('API request timed out');
            } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                statusText.textContent = 'Network error';
                console.error('Network error occurred');
            } else {
                statusText.textContent = 'Connection error';
            }
        }
        
        validateTask(row);
        console.log('Cloud path validation complete');
    }
    
    // Validate output path
    async function validateOutputPath(path, row) {
        const statusIcon = row.querySelector('.status-icon');
        const statusText = row.querySelector('.status-text');
        
        // First check if we have API connectivity
        if (window.apiConnectivity === false) {
            console.log('Skipping output validation due to connectivity issues');
            row.dataset.outputPathValid = 'warning';
            if (row.dataset.validatingOutput === 'true') {
                statusIcon.className = 'status-icon status-warning';
                statusIcon.textContent = '⚠️';
                statusText.textContent = 'API unavailable';
            }
            row.dataset.validatingOutput = 'false';
            validateTask(row);
            return;
        }
        
        try {
            // For output paths, we first check if it's a valid cloud path format
            if (path.startsWith('s3://') || path.startsWith('gs://')) {
                // Extract bucket part for validation
                const bucketPath = path.substring(0, path.lastIndexOf('/') || path.length);
                const isS3Path = bucketPath.startsWith('s3://');
                const isGsPath = bucketPath.startsWith('gs://');
                
                // Extract bucket name
                let bucket = '';
                if (isS3Path) {
                    bucket = bucketPath.substring(5);
                } else if (isGsPath) {
                    bucket = bucketPath.substring(5);
                }
                
                // Check if bucket name is present
                if (!bucket) {
                    row.dataset.outputPathValid = 'false';
                    if (row.dataset.validatingOutput === 'true') {
                        statusIcon.className = 'status-icon status-warning';
                        statusIcon.textContent = '⚠️';
                        statusText.textContent = 'Incomplete output path';
                    }
                    row.dataset.validatingOutput = 'false';
                    validateTask(row);
                    return;
                }
                
                // Check bucket validity
                try {
                    console.log('Making API call to validate output bucket');
                    
                    // Create a promise that rejects after a timeout
                    const timeoutPromise = new Promise((_, reject) => {
                        setTimeout(() => reject(new Error('API request timeout')), 5000); // 5 second timeout
                    });
                    
                    // Race the fetch against the timeout
                    const response = await Promise.race([
                        fetch('/api/validate_path', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ 
                                path: path.substring(0, path.lastIndexOf('/') || path.length),
                                checkBucketOnly: true
                            })
                        }),
                        timeoutPromise
                    ]);
                    
                    console.log('Output bucket API response status:', response.status);
                    
                    if (!response.ok) {
                        console.error('Output bucket API error:', response.status);
                        throw new Error('API error: ' + response.status);
                    }
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        if (result.exists) {
                            // Bucket exists, output path is valid
                            row.dataset.outputPathValid = 'true';
                            if (row.dataset.validatingOutput === 'true') {
                                statusIcon.className = 'status-icon status-success';
                                statusIcon.textContent = '✅';
                                statusText.textContent = 'Output valid';
                            }
                        } else {
                            // Check specific error reasons
                            if (result.reason === 'bucket_not_found') {
                                row.dataset.outputPathValid = 'warning';
                                if (row.dataset.validatingOutput === 'true') {
                                    statusIcon.className = 'status-icon status-warning';
                                    statusIcon.textContent = '⚠️';
                                    statusText.textContent = 'Bucket not found';
                                }
                            } else if (result.reason === 'access_denied') {
                                row.dataset.outputPathValid = 'warning';
                                if (row.dataset.validatingOutput === 'true') {
                                    statusIcon.className = 'status-icon status-warning';
                                    statusIcon.textContent = '⚠️';
                                    statusText.textContent = 'Access denied';
                                }
                            } else {
                                row.dataset.outputPathValid = 'warning';
                                if (row.dataset.validatingOutput === 'true') {
                                    statusIcon.className = 'status-icon status-warning';
                                    statusIcon.textContent = '⚠️';
                                    statusText.textContent = 'Bucket may not exist';
                                }
                            }
                        }
                    } else {
                        // API error checking bucket
                        if (result.client_status === 'not_initialized') {
                            row.dataset.outputPathValid = 'false';
                            if (row.dataset.validatingOutput === 'true') {
                                statusIcon.className = 'status-icon status-error';
                                statusIcon.textContent = '❌';
                                statusText.textContent = 'Missing credentials';
                            }
                        } else {
                            row.dataset.outputPathValid = 'warning';
                            if (row.dataset.validatingOutput === 'true') {
                                statusIcon.className = 'status-icon status-warning';
                                statusIcon.textContent = '⚠️';
                                statusText.textContent = 'Can\'t verify bucket';
                            }
                        }
                    }
                } catch (error) {
                    // Error in API call, but format is still valid
                    console.error('Output bucket check error:', error);
                    row.dataset.outputPathValid = 'warning';
                    if (row.dataset.validatingOutput === 'true') {
                        statusIcon.className = 'status-icon status-warning';
                        statusIcon.textContent = '⚠️';
                        
                        // Handle specific error types
                        if (error.message === 'API request timeout') {
                            statusText.textContent = 'Server timeout';
                            console.error('API request timed out');
                        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                            statusText.textContent = 'Network error';
                            console.error('Network error occurred');
                        } else {
                            statusText.textContent = 'Can\'t verify bucket';
                        }
                    }
                }
            } else {
                // Invalid format
                row.dataset.outputPathValid = 'false';
                if (row.dataset.validatingOutput === 'true') {
                    statusIcon.className = 'status-icon status-error';
                    statusIcon.textContent = '❌';
                    statusText.textContent = 'Invalid format';
                }
            }
        } catch (error) {
            row.dataset.outputPathValid = 'false';
            console.error('Output path validation error:', error);
            if (row.dataset.validatingOutput === 'true') {
                statusIcon.className = 'status-icon status-error';
                statusIcon.textContent = '❌';
                statusText.textContent = 'Connection error';
            }
        }
        
        // Always reset the validating flag when done
        row.dataset.validatingOutput = 'false';
        validateTask(row);
    }
    
    // Validate task inputs - simplified left-to-right approach
    function validateTask(row) {
        console.log('validateTask called');
        
        // Debug - show what the current UI state is
        const statusIcon = row.querySelector('.status-icon');
        const statusText = row.querySelector('.status-text');
        if (statusIcon && statusText) {
            console.log(`Current UI state: Icon=${statusIcon.textContent}, Text=${statusText.textContent}, Class=${statusIcon.className}`);
        }
        
        // Save current validation state
        let currentStatus = row.dataset.taskStatus || '';
        let currentClass = statusIcon ? statusIcon.className : '';
        let currentIcon = statusIcon ? statusIcon.textContent : '';
        let currentText = statusText ? statusText.textContent : '';
        
        try {
            // Get values
            const actionSelect = row.querySelector('.action');
            const cloudPathValid = row.dataset.cloudPathValid || 'false';
            const outputPathValid = row.dataset.outputPathValid || 'false';
            const fileValid = row.dataset.fileValid || 'false';
            const fileModeSelected = row.querySelector('.source-type-radio[value="file"]').checked;
            
            // Reset validation state while checking
            row.dataset.taskStatus = 'validating';
            
            // 1. Check source type (file or cloud path)
            if (fileModeSelected) {
                // FILE MODE
                
                // 2. Check if file is selected
                const fileInput = row.querySelector('.source-file');
                if (fileInput.files.length === 0) {
                    updateStatus(row, 'error', 'Select file');
                    return false;
                }
                
                // 3. Check if file is valid
                if (fileValid !== 'true') {
                    updateStatus(row, 'error', 'Invalid file format');
                    return false;
                }
                
                // 4. Check if platform is selected for file mode
                const platformSelect = row.querySelector('.upload-to');
                if (platformSelect.value === '') {
                    updateStatus(row, 'error', 'Select platform');
                    return false;
                }
            } else {
                // CLOUD PATH MODE
                
                // 2. Check if cloud path input is empty
                const cloudPathInput = row.querySelector('.source-path');
                if (!cloudPathInput.value.trim()) {
                    updateStatus(row, 'error', 'Enter source path');
                    return false;
                }
                
                // CRITICAL: Do not override error state for path validation
                // If cloudPathValid is false and we have an error message displayed, keep it
                if (cloudPathValid === 'false' && 
                    statusIcon && 
                    statusIcon.className.includes('status-error') &&
                    statusText) {
                    console.log('Preserving source path error state:', statusText.textContent);
                    return false;
                }
                
                // 3. Check if source validation is in progress
                if (cloudPathValid !== 'true' && !row.dataset.validatingOutput) {
                    // If the path input seems valid but status is stuck at checking,
                    // we'll assume it's a network issue and let the user proceed with a warning
                    const path = cloudPathInput.value.trim();
                    
                    // Extract parts to check if the format is valid
                    let parts = [];
                    if (path.startsWith('s3://')) {
                        parts = path.substring(5).split('/', 2);
                    } else if (path.startsWith('gs://')) {
                        parts = path.substring(5).split('/', 2);
                    }
                    
                    // If the path format is valid but we have no response, allow proceeding with warning
                    if (parts.length >= 2 && parts[0] && parts[1] && statusText.textContent === 'Checking...') {
                        // If stuck checking for more than 5 seconds, let user proceed
                        if (!row.dataset.checkingStartTime) {
                            row.dataset.checkingStartTime = Date.now().toString();
                        } else if (Date.now() - parseInt(row.dataset.checkingStartTime) > 5000) {
                            // Allow proceeding but mark with warning
                            updateStatus(row, 'warning', 'Using unverified source');
                            row.dataset.cloudPathValid = 'warning';
                            return true;
                        }
                    } else {
                        // Reset checking timer if not in checking state
                        delete row.dataset.checkingStartTime;
                    }
                    
                    // Don't overwrite error messages with this generic message
                    if (!statusText.textContent.includes('Missing') && 
                        !statusText.textContent.includes('Invalid') &&
                        !statusText.textContent.includes('Need')) {
                        updateStatus(row, 'pending', 'Checking source...');
                    }
                    return false;
                }
                
                // 4. Check if cloud path is valid
                if (cloudPathValid === 'false') {
                    // Error message is already shown by validateCloudPath
                    return false;
                }
            }
            
            // 5. Check if action is selected
            if (actionSelect.value === '') {
                updateStatus(row, 'error', 'Select action');
                return false;
            }
            
            // 6. Check if output path is empty
            const outputPathInput = row.querySelector('.output-path');
            if (!outputPathInput.value.trim()) {
                updateStatus(row, 'error', 'Enter output path');
                return false;
            }
            
            // 7. Check if output validation is in progress
            if (row.dataset.validatingOutput === 'true') {
                // If stuck checking for more than 5 seconds, let user proceed
                if (!row.dataset.outputCheckingStartTime) {
                    row.dataset.outputCheckingStartTime = Date.now().toString();
                } else if (Date.now() - parseInt(row.dataset.outputCheckingStartTime) > 5000) {
                    // Allow proceeding but mark with warning
                    updateStatus(row, 'warning', 'Using unverified output');
                    row.dataset.outputPathValid = 'warning';
                    row.dataset.validatingOutput = 'false';
                    return true;
                }
                
                updateStatus(row, 'pending', 'Checking output...');
                return false;
            } else {
                // Reset output checking timer
                delete row.dataset.outputCheckingStartTime;
            }
            
            // 8. Check if output path is valid
            if (outputPathValid === 'false') {
                updateStatus(row, 'error', 'Invalid output');
                return false;
            }
            
            // All checks passed
            updateStatus(row, 'success', 'Ready');
            return true;
        } catch (error) {
            console.error('Task validation error:', error);
            updateStatus(row, 'error', 'Validation error');
            return false;
        }
    }
    
    // Helper function to update status
    function updateStatus(row, status, message) {
        const statusIcon = row.querySelector('.status-icon');
        const statusText = row.querySelector('.status-text');
        
        if (!statusIcon || !statusText) {
            console.error('Status elements not found:', {
                row: row,
                statusIcon: !!statusIcon,
                statusText: !!statusText
            });
            return;
        }
        
        console.log(`updateStatus called: status=${status}, message=${message}`);
        
        // Update dataset
        row.dataset.taskStatus = status;
        
        // Update status based on type
        switch (status) {
            case 'success':
                statusIcon.className = 'status-icon status-success';
                statusIcon.textContent = '✅';
                break;
            case 'pending':
                statusIcon.className = 'status-icon status-pending';
                statusIcon.textContent = '⏳';
                break;
            case 'warning':
                statusIcon.className = 'status-icon status-warning';
                statusIcon.textContent = '⚠️';
                break;
            case 'error':
                statusIcon.className = 'status-icon status-error';
                statusIcon.textContent = '❌';
                break;
            default:
                statusIcon.className = 'status-icon';
                statusIcon.textContent = '⏳';
        }
        
        // Update message
        statusText.textContent = message;
        
        // For debugging
        console.log(`UI updated to: ${status} - ${message}`);
    }
    
    // Extract task data from a row
    function getTaskData(row) {
        const sourceTypeRadios = row.querySelectorAll('.source-type-radio');
        const fileMode = Array.from(sourceTypeRadios).find(r => r.checked).value === 'file';
        
        const sourceFile = row.querySelector('.source-file');
        const sourcePath = row.querySelector('.source-path');
        const action = row.querySelector('.action').value;
        const outputPath = row.querySelector('.output-path').value.trim();
        
        if (fileMode) {
            // Local file upload
            return {
                source_type: 'local',
                action: action,
                output_path: outputPath,
                files: sourceFile.files,
                upload_to: row.querySelector('.upload-to').value
            };
        } else {
            // Cloud path
            const path = sourcePath.value.trim();
            return {
                source_type: path.toLowerCase().startsWith('s3://') ? 's3' : 'gcs',
                source_path: path,
                action: action,
                output_path: outputPath
            };
        }
    }
    
    // Upload a local file
    async function uploadFile(file, uploadTo, sessionId) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('upload_to', uploadTo);
        formData.append('session_id', sessionId);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Upload failed: ' + response.status);
        }
        
        return await response.json();
    }
    
    // Submit tasks to the API
    async function submitTasks(tasks) {
        try {
            showLoading();
            
            const response = await fetch('/api/submit_task', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    tasks: tasks,
                    session_id: sessionId
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                hideLoading();
                showAlert(`Successfully submitted ${result.successful} out of ${result.total} tasks.`, false);
                
                // Update task statuses based on submission results
                updateTaskStatusesFromSubmission(result);
                
                // Start polling for task statuses if there were successful submissions
                if (result.successful > 0) {
                    // Store session ID for status polling
                    window.currentSessionId = result.session_id;
                    
                    // Start polling
                    startStatusPolling(result.session_id);
                }
            } else {
                hideLoading();
                showAlert(`Error submitting tasks: ${result.error}`, true);
            }
            
            return result; // Return the result to the caller
        } catch (err) {
            hideLoading();
            showAlert(`Error: ${err.message}`, true);
            
            // Return error result object
            return {
                success: false,
                error: err.message
            };
        }
    }
    
    // Update task statuses based on submission results
    function updateTaskStatusesFromSubmission(result) {
        // Mark any failed tasks
        if (result.errors && result.errors.length > 0) {
            // Handle specific error messages if available
            console.error('Submission errors:', result.errors);
        }
        
        // Update all tasks to "Processing" that were submitted successfully
        const taskRows = document.querySelectorAll('#task-container tr');
        taskRows.forEach(row => {
            // Only update tasks that were valid
            if (row.dataset.valid === 'true') {
                const statusIcon = row.querySelector('.status-icon');
                const statusText = row.querySelector('.status-text');
                
                statusIcon.className = 'status-icon status-running';
                statusIcon.textContent = '🔄';
                statusText.textContent = 'Processing';
            }
        });
    }
    
    // Status polling variables
    let pollingInterval = null;
    const POLLING_INTERVAL_MS = 5000; // Poll every 5 seconds
    
    // Start polling for task status updates
    function startStatusPolling(sessionId) {
        // Clear any existing polling
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        
        // Poll immediately the first time
        pollTaskStatus(sessionId);
        
        // Then set up regular polling
        pollingInterval = setInterval(() => {
            pollTaskStatus(sessionId);
        }, POLLING_INTERVAL_MS);
        
        console.log(`Started polling for session ${sessionId}`);
    }
    
    // Stop polling for task status updates
    function stopStatusPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
            console.log('Stopped polling for task status');
        }
    }
    
    // Poll for task status from the backend
    async function pollTaskStatus(sessionId) {
        if (!sessionId) {
            console.error('No session ID for polling');
            return;
        }
        
        try {
            const response = await fetch('/api/task_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                updateTaskStatusesFromPoll(result);
                
                // If all tasks are complete (success or failure), stop polling
                if (result.status === 'completed' || result.status === 'failed') {
                    stopStatusPolling();
                }
            } else {
                console.error('Error polling task status:', result.error);
            }
        } catch (err) {
            console.error('Error polling for task status:', err);
        }
    }
    
    // Update the UI based on poll results
    function updateTaskStatusesFromPoll(result) {
        if (!result.tasks || result.tasks.length === 0) {
            console.log('No tasks found in status update');
            return;
        }
        
        const taskRows = document.querySelectorAll('#task-container tr');
        
        // For each task in the result
        result.tasks.forEach(task => {
            // Find the matching row by source_path
            const matchingRow = findRowBySourcePath(taskRows, task.source_path);
            
            if (matchingRow) {
                const statusIcon = matchingRow.querySelector('.status-icon');
                const statusText = matchingRow.querySelector('.status-text');
                
                // Update based on task status
                switch (task.status) {
                    case 'PENDING':
                        statusIcon.className = 'status-icon status-pending';
                        statusIcon.textContent = '⏳';
                        statusText.textContent = 'Pending';
                        break;
                    case 'RUNNING':
                        statusIcon.className = 'status-icon status-running';
                        statusIcon.textContent = '🔄';
                        statusText.textContent = 'Processing';
                        break;
                    case 'SUCCESS':
                        statusIcon.className = 'status-icon status-success';
                        statusIcon.textContent = '✅';
                        statusText.textContent = 'Success';
                        break;
                    case 'FAILED':
                        statusIcon.className = 'status-icon status-error';
                        statusIcon.textContent = '❌';
                        statusText.textContent = task.message || 'Failed';
                        break;
                    default:
                        statusIcon.className = 'status-icon status-pending';
                        statusIcon.textContent = '⏳';
                        statusText.textContent = task.status;
                }
            }
        });
        
        // Update overall status
        const overallStatusDiv = document.getElementById('overall-status');
        if (overallStatusDiv) {
            overallStatusDiv.textContent = `Overall Status: ${result.status.charAt(0).toUpperCase() + result.status.slice(1)}`;
        } else {
            // Create overall status div if it doesn't exist
            const statusDiv = document.createElement('div');
            statusDiv.id = 'overall-status';
            statusDiv.className = 'overall-status';
            statusDiv.textContent = `Overall Status: ${result.status.charAt(0).toUpperCase() + result.status.slice(1)}`;
            
            // Add it after the task table
            const taskTable = document.querySelector('.task-table');
            if (taskTable) {
                taskTable.parentNode.insertBefore(statusDiv, taskTable.nextSibling);
            }
        }
    }
    
    // Find a row by matching the source path
    function findRowBySourcePath(rows, sourcePath) {
        for (const row of rows) {
            // Check both the source path input and the file input for a match
            const sourcePathInput = row.querySelector('.source-path');
            const sourceFile = row.querySelector('.source-file');
            const fileInputButton = row.querySelector('.file-input-button');
            
            // For cloud paths
            if (sourcePathInput && !sourcePathInput.classList.contains('hidden') && 
                sourcePathInput.value.trim() === sourcePath) {
                return row;
            }
            
            // For file uploads (compare filename)
            if (fileInputButton && 
                fileInputButton.textContent === sourcePath.split('/').pop()) {
                return row;
            }
        }
        return null;
    }
    
    // Submit all tasks
    submitAllBtn.addEventListener('click', async function() {
        const rows = Array.from(taskContainer.querySelectorAll('tr'));
        
        // Validate all tasks first
        rows.forEach(row => validateTask(row));
        
        // Get valid tasks
        const validRows = rows.filter(row => {
            return row.dataset.taskStatus === 'success';
        });
        
        if (validRows.length === 0) {
            showAlert('No valid tasks to submit', true);
            return;
        }
        
        showLoading();
        
        try {
            const tasksToProcess = [];
            
            // Process each row: upload local files first
            for (const row of validRows) {
                const taskData = getTaskData(row);
                
                updateStatus(row, 'pending', 'Processing...');
                
                if (taskData.source_type === 'local') {
                    // Upload the file first
                    updateStatus(row, 'pending', 'Uploading...');
                    
                    try {
                        const fileUploadResult = await uploadFile(taskData.files[0], taskData.upload_to, sessionId);
                        
                        if (fileUploadResult.success) {
                            tasksToProcess.push({
                                source_type: taskData.upload_to,
                                source_path: fileUploadResult.path,
                                action: taskData.action,
                                output_path: taskData.output_path
                            });
                        } else {
                            throw new Error(fileUploadResult.error || 'Upload failed');
                        }
                    } catch (error) {
                        updateStatus(row, 'error', 'Upload failed');
                        throw error;
                    }
                } else {
                    // Direct cloud path
                    tasksToProcess.push({
                        source_type: taskData.source_type,
                        source_path: taskData.source_path,
                        action: taskData.action,
                        output_path: taskData.output_path
                    });
                }
            }
            
            // Submit all tasks to be processed
            const result = await submitTasks(tasksToProcess);
            
            if (result.success) {
                showAlert(`Successfully submitted ${result.successful} of ${result.total} tasks.`);
                
                // Update task status
                validRows.forEach(row => {
                    updateStatus(row, 'success', 'Submitted');
                });
                
                // Check for failures
                if (result.failed > 0) {
                    console.error('Some tasks failed:', result.errors);
                    showAlert(`${result.failed} tasks failed to submit.`, true);
                }
            } else {
                throw new Error(result.error || 'Submission failed');
            }
        } catch (error) {
            console.error('Error submitting tasks:', error);
            showAlert('Error: ' + error.message, true);
        } finally {
            hideLoading();
        }
    });
    
    // Only create initial task row if the container is empty
    if (taskContainer && taskContainer.childElementCount === 0) {
        taskContainer.appendChild(window.createTaskCard());
    }

    // Test API connectivity
    async function testApiConnectivity() {
        console.log('Testing API connectivity...');
        try {
            const response = await fetch('/api/diagnostic', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ test: true })
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('API connectivity test passed:', result);
                window.apiConnectivity = true;
            } else {
                console.error('API connectivity test failed with status:', response.status);
                window.apiConnectivity = false;
                showAlert('Warning: API connectivity issues detected. Some features may not work properly.', true);
            }
        } catch (error) {
            console.error('API connectivity test error:', error);
            window.apiConnectivity = false;
            showAlert('Error: Cannot connect to API. Please check your network connection.', true);
        }
    }
}); 