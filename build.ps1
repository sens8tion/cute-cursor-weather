# Build script for Weather Station Data Collector

# Function to write colored output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Function to check if a command exists
function Test-CommandExists {
    param ($command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try {
        if (Get-Command $command) { return $true }
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $oldPreference
    }
}

# Check if Python is installed
if (-not (Test-CommandExists python)) {
    Write-ColorOutput Red "Python is not installed or not in PATH"
    exit 1
}

# Check if pip is installed
if (-not (Test-CommandExists pip)) {
    Write-ColorOutput Red "pip is not installed or not in PATH"
    exit 1
}

Write-ColorOutput Green "Starting build process..."

# Install dependencies
Write-ColorOutput Yellow "Installing dependencies..."
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Failed to install dependencies"
    exit 1
}

# Run unit tests
Write-ColorOutput Yellow "Running unit tests..."
python -m pytest test_weather_collector.py -v
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Unit tests failed"
    exit 1
}

# Run coverage report
Write-ColorOutput Yellow "Generating coverage report..."
python -m pytest --cov=weather_collector test_weather_collector.py
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Coverage report generation failed"
    exit 1
}

# Test the main script
Write-ColorOutput Yellow "Testing main script..."
python weather_collector.py
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Main script test failed"
    exit 1
}

Write-ColorOutput Green "Build completed successfully!" 