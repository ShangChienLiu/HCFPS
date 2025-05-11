/**
 * Simple connectivity test script
 * Copy and paste this entire script into your browser console to run tests
 */

async function testConnectivity() {
  console.log('=== API CONNECTIVITY TEST ===');
  console.log('Testing GET request to root endpoint...');
  
  try {
    // Test 1: Basic GET request to root
    const rootResponse = await fetch('/', {
      method: 'GET',
      headers: {
        'Accept': 'text/html'
      }
    });
    
    console.log('Root endpoint response status:', rootResponse.status);
    console.log('Root endpoint response OK:', rootResponse.ok);
    
    // Test 2: Basic GET request to health endpoint
    console.log('\nTesting GET request to /health endpoint...');
    const healthResponse = await fetch('/health', {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });
    
    console.log('Health endpoint response status:', healthResponse.status);
    console.log('Health endpoint response OK:', healthResponse.ok);
    
    if (healthResponse.ok) {
      const healthData = await healthResponse.json();
      console.log('Health data:', healthData);
    }
    
    // Test 3: Test POST request to diagnostic endpoint
    console.log('\nTesting POST request to /api/diagnostic endpoint...');
    const diagnosticResponse = await fetch('/api/diagnostic', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ test: true })
    });
    
    console.log('Diagnostic endpoint response status:', diagnosticResponse.status);
    console.log('Diagnostic endpoint response OK:', diagnosticResponse.ok);
    
    if (diagnosticResponse.ok) {
      const diagnosticData = await diagnosticResponse.json();
      console.log('Diagnostic data:', diagnosticData);
    }
    
    // Test 4: Specific test for the validate_path endpoint
    console.log('\nTesting POST request to /api/validate_path endpoint...');
    const validatePathResponse = await fetch('/api/validate_path', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ 
        path: 's3://test-bucket/test-file.txt',
        checkBucketOnly: false
      })
    });
    
    console.log('Validate path endpoint response status:', validatePathResponse.status);
    console.log('Validate path endpoint response OK:', validatePathResponse.ok);
    
    if (validatePathResponse.ok) {
      const validateData = await validatePathResponse.json();
      console.log('Validate path data:', validateData);
    } else {
      console.log('Validate path error:', await validatePathResponse.text());
    }

    // Test 5: Browser network test
    console.log('\nChecking browser network capabilities...');
    const googleResponse = await fetch('https://www.google.com/generate_204', {
      method: 'HEAD',
      mode: 'no-cors'
    });
    console.log('External network test result:', googleResponse.status, googleResponse.type);
    
    // Summary
    console.log('\n=== TEST SUMMARY ===');
    console.log('Root endpoint:', rootResponse.ok ? '✅ OK' : '❌ Failed');
    console.log('Health endpoint:', healthResponse.ok ? '✅ OK' : '❌ Failed');
    console.log('Diagnostic endpoint:', diagnosticResponse.ok ? '✅ OK' : '❌ Failed');
    console.log('Validate path endpoint:', validatePathResponse.ok ? '✅ OK' : '❌ Failed');
    
  } catch (error) {
    console.error('Connection test error:', error);
  }
}

// Run the test
testConnectivity(); 