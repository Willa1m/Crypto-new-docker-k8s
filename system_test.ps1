# Complete System Integration Test Script
# 加密货币监控系统完整集成测试

# Global variables
$script:PassedTests = 0
$script:FailedTests = 0
$BaseUrl = "http://127.0.0.1:8000"
$TimeoutSeconds = 10

# Helper function to write test results
function Write-TestResult {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Details = ""
    )
    
    if ($Passed) {
        Write-Host "✅ $TestName" -ForegroundColor Green
        if ($Details) {
            Write-Host "  $Details" -ForegroundColor Gray
        }
        $script:PassedTests++
    } else {
        Write-Host "❌ $TestName" -ForegroundColor Red
        if ($Details) {
            Write-Host "  $Details" -ForegroundColor Yellow
        }
        $script:FailedTests++
    }
}

# Test endpoint function
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$TestName,
        [string]$ExpectedContent = $null
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSeconds
        
        if ($response.StatusCode -eq 200) {
            if ($ExpectedContent) {
                if ($response.Content -like "*$ExpectedContent*") {
                    Write-TestResult $TestName $true "Status: $($response.StatusCode), Content found"
                } else {
                    Write-TestResult $TestName $false "Status 200 but missing expected content: $ExpectedContent"
                }
            } else {
                Write-TestResult $TestName $true "Status: $($response.StatusCode), Length: $($response.Content.Length)"
            }
        } else {
            Write-TestResult $TestName $false "Unexpected status code: $($response.StatusCode)"
        }
    }
    catch {
        Write-TestResult $TestName $false "Error: $($_.Exception.Message)"
    }
}

# Test API endpoint function
function Test-ApiEndpoint {
    param(
        [string]$Url,
        [string]$TestName
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSeconds -UseBasicParsing
        
        if ($response.StatusCode -eq 200) {
            try {
                $json = $response.Content | ConvertFrom-Json
                Write-TestResult $TestName $true "Valid JSON response, Status: $($response.StatusCode)"
            } catch {
                Write-TestResult $TestName $false "Invalid JSON response"
            }
        } else {
            Write-TestResult $TestName $false "Status: $($response.StatusCode)"
        }
    }
    catch {
        Write-TestResult $TestName $false "Error: $($_.Exception.Message)"
    }
}

# Test database connection function
function Test-DatabaseConnection {
    param(
        [string]$TestName
    )
    
    try {
        $response = Invoke-WebRequest -Uri "$BaseUrl/api/system/status" -TimeoutSec $TimeoutSeconds -UseBasicParsing
        
        if ($response.StatusCode -eq 200) {
            $json = $response.Content | ConvertFrom-Json
            if ($json.data -and $json.data.database -eq "connected") {
                Write-TestResult $TestName $true "Database connected"
            } else {
                Write-TestResult $TestName $false "Database not connected"
            }
        } else {
            Write-TestResult $TestName $false "Cannot check database status"
        }
    }
    catch {
        Write-TestResult $TestName $false "Error checking database: $($_.Exception.Message)"
    }
}

# Test Redis connection function
function Test-RedisConnection {
    param(
        [string]$TestName
    )
    
    try {
        $response = Invoke-WebRequest -Uri "$BaseUrl/api/system/status" -TimeoutSec $TimeoutSeconds -UseBasicParsing
        
        if ($response.StatusCode -eq 200) {
            $json = $response.Content | ConvertFrom-Json
            if ($json.data -and $json.data.redis -eq "connected") {
                Write-TestResult $TestName $true "Redis connected"
            } else {
                Write-TestResult $TestName $false "Redis not connected"
            }
        } else {
            Write-TestResult $TestName $false "Cannot check Redis status"
        }
    }
    catch {
        Write-TestResult $TestName $false "Error checking Redis: $($_.Exception.Message)"
    }
}

# Main test execution
Write-Host "=" * 60
Write-Host "Complete System Integration Test"
Write-Host "Base URL: $BaseUrl"
Write-Host "Testing API Health..." -ForegroundColor Yellow
Test-ApiEndpoint "$BaseUrl/api/health" "API Health Check"
Write-Host ""

# Test 2: Frontend Pages
Write-Host "Testing Frontend Pages..." -ForegroundColor Yellow
Test-Endpoint "$BaseUrl/" "Home Page" "加密货币价格监控系统"
Test-Endpoint "$BaseUrl/bitcoin" "Bitcoin Page" "比特币"
Test-Endpoint "$BaseUrl/ethereum" "Ethereum Page" "以太坊"
Test-Endpoint "$BaseUrl/kline" "K-Line Page" "K线图"
Write-Host ""

# Test 3: API Endpoints
Write-Host "Testing API Endpoints..." -ForegroundColor Yellow
Test-ApiEndpoint "$BaseUrl/api/latest_prices" "Latest Prices API"
Test-ApiEndpoint "$BaseUrl/api/chart_data" "Chart Data API"
Test-ApiEndpoint "$BaseUrl/api/btc_data" "Bitcoin Data API"
Test-ApiEndpoint "$BaseUrl/api/eth_data" "Ethereum Data API"
Test-ApiEndpoint "$BaseUrl/api/kline_data" "K-Line Data API"
Test-ApiEndpoint "$BaseUrl/api/system/status" "System Status API"
Write-Host ""

# Test 4: Static Resources
Write-Host "Testing Static Resources..." -ForegroundColor Yellow
Test-Endpoint "$BaseUrl/static/css/styles.css" "CSS File"
Test-Endpoint "$BaseUrl/static/js/crypto.js" "Main JavaScript"
Test-Endpoint "$BaseUrl/static/js/app.js" "Chart JavaScript"
Write-Host ""

# Test 5: Database Connections
Write-Host "Testing Database Connections..." -ForegroundColor Yellow
Test-DatabaseConnection "Database Connection"
Test-RedisConnection "Redis Connection"
Write-Host ""

# Summary
Write-Host "=" * 60
Write-Host "Test Results Summary"
Write-Host "=" * 60
$TotalTests = $script:PassedTests + $script:FailedTests
$SuccessRate = if ($TotalTests -gt 0) { [math]::Round(($script:PassedTests / $TotalTests) * 100, 1) } else { 0 }

Write-Host "Total Tests: $TotalTests"
Write-Host "Passed: $script:PassedTests" -ForegroundColor Green
Write-Host "Failed: $script:FailedTests" -ForegroundColor Red
Write-Host "Success Rate: $SuccessRate%"
Write-Host ""

if ($script:FailedTests -eq 0) {
    Write-Host "🎉 ALL TESTS PASSED! System is fully operational." -ForegroundColor Green
} elseif ($SuccessRate -ge 80) {
    Write-Host "⚠️ Most tests passed, minor issues detected." -ForegroundColor Yellow
} else {
    Write-Host "❌ CRITICAL! System has major failures." -ForegroundColor Red
}

Write-Host ""
Write-Host "Test completed at: $(Get-Date -Format 'MM/dd/yyyy HH:mm:ss')"