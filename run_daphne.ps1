# PowerShell script for running Daphne ASGI server on Windows
# Enhanced production setup for WebSocket handling

param(
    [string]$Environment = "development",
    [string]$Port = "8000",
    [string]$Host = "0.0.0.0",
    [string]$SSL_CERT = "",
    [string]$SSL_KEY = ""
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-ColorOutput {
    param($Message, $Color)
    Write-Host $Message -ForegroundColor $Color
}

function Test-Dependencies {
    Write-ColorOutput "Checking dependencies..." $Blue
    
    # Check if Python is available
    try {
        $pythonVersion = python --version 2>&1
        Write-ColorOutput "✓ Python: $pythonVersion" $Green
    }
    catch {
        Write-ColorOutput "✗ Python not found. Please install Python." $Red
        exit 1
    }
    
    # Check if Daphne is installed
    try {
        $daphneVersion = python -c "import daphne; print(daphne.__version__)" 2>&1
        Write-ColorOutput "✓ Daphne: $daphneVersion" $Green
    }
    catch {
        Write-ColorOutput "✗ Daphne not installed. Installing..." $Yellow
        pip install daphne
    }
    
    # Check if Redis is running (optional)
    try {
        $redisTest = redis-cli ping 2>&1
        if ($redisTest -eq "PONG") {
            Write-ColorOutput "✓ Redis: Running" $Green
        }
        else {
            Write-ColorOutput "⚠ Redis: Not running (WebSocket features may be limited)" $Yellow
        }
    }
    catch {
        Write-ColorOutput "⚠ Redis: Not available (install Redis for full WebSocket support)" $Yellow
    }
}

function Start-Daphne {
    param($Config)
    
    Write-ColorOutput "Starting Daphne ASGI server..." $Blue
    Write-ColorOutput "Environment: $Environment" $Blue
    Write-ColorOutput "Port: $Port" $Blue
    Write-ColorOutput "Host: $Host" $Blue
    
    # Create logs directory if it doesn't exist
    if (!(Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs"
        Write-ColorOutput "Created logs directory" $Green
    }
    
    # Set Django settings
    $env:DJANGO_SETTINGS_MODULE = "promptcraft.settings"
    
    # Build Daphne command
    $daphneArgs = @(
        "--bind", $Host,
        "--port", $Port,
        "--proxy-headers",
        "--access-log", "logs/daphne_access.log",
        "--application-close-timeout", "30",
        "--websocket-timeout", "86400",
        "--websocket-connect-timeout", "10",
        "--verbosity", "2"
    )
    
    # Add SSL configuration if provided
    if ($SSL_CERT -and $SSL_KEY) {
        $daphneArgs += "--tls-cert", $SSL_CERT, "--tls-key", $SSL_KEY
        Write-ColorOutput "SSL/TLS enabled" $Green
    }
    
    # Add environment-specific configurations
    if ($Environment -eq "production") {
        $daphneArgs += "--access-log", "logs/daphne_access.log"
        Write-ColorOutput "Production mode enabled" $Green
    }
    
    # Final application parameter
    $daphneArgs += "promptcraft.asgi:application"
    
    Write-ColorOutput "Command: daphne $($daphneArgs -join ' ')" $Blue
    
    try {
        # Start Daphne
        & daphne @daphneArgs
    }
    catch {
        Write-ColorOutput "Failed to start Daphne: $($_.Exception.Message)" $Red
        exit 1
    }
}

function Test-WebSocket {
    Write-ColorOutput "Testing WebSocket connection..." $Blue
    
    $testScript = @"
import asyncio
import websockets
import json
import sys

async def test_websocket():
    try:
        uri = "ws://localhost:$Port/ws/chat/test/"
        async with websockets.connect(uri) as websocket:
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Wait for pong
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "pong":
                print("✓ WebSocket test successful")
                return True
            else:
                print(f"✗ Unexpected response: {data}")
                return False
                
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")
        return False

# Run test
result = asyncio.run(test_websocket())
sys.exit(0 if result else 1)
"@
    
    # Save test script to temp file
    $testFile = "temp_ws_test.py"
    $testScript | Out-File -FilePath $testFile -Encoding UTF8
    
    try {
        # Run test
        $result = python $testFile
        Write-ColorOutput $result $Green
    }
    catch {
        Write-ColorOutput "WebSocket test failed" $Red
    }
    finally {
        # Clean up
        if (Test-Path $testFile) {
            Remove-Item $testFile
        }
    }
}

function Show-Help {
    Write-Host @"
Daphne ASGI Server Manager for PromptCraft

Usage: .\run_daphne.ps1 [OPTIONS]

Options:
    -Environment    Set environment (development/production) [default: development]
    -Port          Set port number [default: 8000]
    -Host          Set host address [default: 0.0.0.0]
    -SSL_CERT      Path to SSL certificate file
    -SSL_KEY       Path to SSL private key file

Examples:
    .\run_daphne.ps1                                    # Development mode
    .\run_daphne.ps1 -Environment production            # Production mode
    .\run_daphne.ps1 -Port 8080                        # Custom port
    .\run_daphne.ps1 -SSL_CERT cert.pem -SSL_KEY key.pem  # With SSL

Features:
    ✓ WebSocket support with Django Channels
    ✓ Real-time prompt optimization
    ✓ Template search with AI enhancement
    ✓ Sentry error monitoring integration
    ✓ Redis backend for channel layers
    ✓ Production-ready configuration
"@
}

# Main execution
switch ($args[0]) {
    "test" {
        Test-Dependencies
        Test-WebSocket
    }
    "help" {
        Show-Help
    }
    default {
        Write-ColorOutput "=== PromptCraft Daphne ASGI Server ===" $Blue
        Test-Dependencies
        Start-Daphne
    }
}