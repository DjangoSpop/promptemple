# PowerShell script for PromptCraft project setup and management
param (
    [switch]$Setup,
    [switch]$Run, 
    [switch]$Docker,
    [switch]$InitializeDb,
    [switch]$SampleData,
    [switch]$CreateAdmin
)

$WorkingDirectory = $PSScriptRoot
$VirtualEnvPath = Join-Path -Path $WorkingDirectory -ChildPath "venv"
$BackendPath = $WorkingDirectory

# Function to print colored messages
function Write-ColoredMessage {
    param (
        [string]$Message,
        [string]$Color = "White"
    )
    
    Write-Host $Message -ForegroundColor $Color
}

# Function to check if a command exists
function Test-Command {
    param (
        [string]$Command
    )
    
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Function to create virtual environment
function New-VirtualEnvironment {
    Write-ColoredMessage "Creating Python virtual environment..." "Cyan"
    
    if (-not (Test-Path -Path $VirtualEnvPath)) {
        python -m venv $VirtualEnvPath
        Write-ColoredMessage "Virtual environment created at: $VirtualEnvPath" "Green"
    } else {
        Write-ColoredMessage "Virtual environment already exists at: $VirtualEnvPath" "Yellow"
    }
}

# Function to activate virtual environment
function Enter-VirtualEnvironment {
    Write-ColoredMessage "Activating virtual environment..." "Cyan"
    
    $ActivateScript = Join-Path -Path $VirtualEnvPath -ChildPath "Scripts\Activate.ps1"
    if (Test-Path -Path $ActivateScript) {
        & $ActivateScript
        Write-ColoredMessage "Virtual environment activated" "Green"
    } else {
        Write-ColoredMessage "Virtual environment activation script not found at: $ActivateScript" "Red"
        exit 1
    }
}

# Function to install requirements
function Install-Requirements {
    Write-ColoredMessage "Installing requirements..." "Cyan"
    
    $RequirementsFile = Join-Path -Path $BackendPath -ChildPath "requirements.txt"
    if (Test-Path -Path $RequirementsFile) {
        pip install -r $RequirementsFile
        Write-ColoredMessage "Requirements installed" "Green"
    } else {
        Write-ColoredMessage "Requirements file not found at: $RequirementsFile" "Red"
        exit 1
    }
}

# Function to create .env file if it doesn't exist
function New-EnvFile {
    Write-ColoredMessage "Checking for .env file..." "Cyan"
    
    $EnvFile = Join-Path -Path $WorkingDirectory -ChildPath ".env"
    $EnvSampleFile = Join-Path -Path $WorkingDirectory -ChildPath ".env.sample"
    
    if (-not (Test-Path -Path $EnvFile)) {
        if (Test-Path -Path $EnvSampleFile) {
            Copy-Item -Path $EnvSampleFile -Destination $EnvFile
            Write-ColoredMessage ".env file created from .env.sample" "Green"
        } else {
            Write-ColoredMessage ".env.sample file not found. Creating basic .env file..." "Yellow"
            
            $EnvContent = @"
# Django settings
SECRET_KEY=django-insecure-$(Get-Random)
DEBUG=True
DJANGO_ENVIRONMENT=development
ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
DATABASE_URL=sqlite:///db.sqlite3

# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379

# AI API Keys
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# CORS settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
"@
            
            Set-Content -Path $EnvFile -Value $EnvContent
            Write-ColoredMessage "Basic .env file created" "Green"
        }
    } else {
        Write-ColoredMessage ".env file already exists" "Yellow"
    }
}

# Function to initialize the database
function Initialize-Database {
    param (
        [switch]$WithSampleData,
        [switch]$CreateAdmin
    )
    
    Write-ColoredMessage "Initializing database..." "Cyan"
    
    $InitParams = ""
    if ($WithSampleData) {
        $InitParams += " --sample-data"
    }
    
    if ($CreateAdmin) {
        $InitParams += " --admin"
    }
    
    & python manage.py initialize_project $InitParams
    Write-ColoredMessage "Database initialized" "Green"
}

# Function to run server
function Start-Server {
    Write-ColoredMessage "Starting development server..." "Cyan"
    
    & python manage.py runserver 0.0.0.0:8000
}

# Function to start Docker containers
function Start-DockerContainers {
    Write-ColoredMessage "Starting Docker containers..." "Cyan"
    
    if (-not (Test-Command "docker")) {
        Write-ColoredMessage "Docker is not installed or not in PATH" "Red"
        exit 1
    }
    
    if (-not (Test-Command "docker-compose")) {
        Write-ColoredMessage "Docker Compose is not installed or not in PATH" "Red"
        exit 1
    }
    
    docker-compose up -d
    Write-ColoredMessage "Docker containers started" "Green"
}

# Main script execution
if ($Setup) {
    Write-ColoredMessage "Setting up PromptCraft development environment..." "Magenta"
    
    # Check Python installation
    if (-not (Test-Command "python")) {
        Write-ColoredMessage "Python is not installed or not in PATH" "Red"
        exit 1
    }
    
    # Create virtual environment
    New-VirtualEnvironment
    
    # Activate virtual environment
    Enter-VirtualEnvironment
    
    # Install requirements
    Install-Requirements
    
    # Create .env file
    New-EnvFile
    
    Write-ColoredMessage "PromptCraft development environment setup complete!" "Magenta"
}

if ($InitializeDb) {
    # Activate virtual environment if not already activated
    if (-not ($env:VIRTUAL_ENV)) {
        Enter-VirtualEnvironment
    }
    
    # Initialize database
    Initialize-Database -WithSampleData:$SampleData -CreateAdmin:$CreateAdmin
}

if ($Docker) {
    # Start Docker containers
    Start-DockerContainers
}

if ($Run) {
    # Activate virtual environment if not already activated
    if (-not ($env:VIRTUAL_ENV)) {
        Enter-VirtualEnvironment
    }
    
    # Start server
    Start-Server
}

# If no parameters provided, show help
if (-not ($Setup -or $Run -or $Docker -or $InitializeDb)) {
    Write-ColoredMessage "PromptCraft Development Setup Script" "Cyan"
    Write-ColoredMessage "Usage:" "White"
    Write-ColoredMessage "  .\setup.ps1 -Setup              # Set up development environment" "White"
    Write-ColoredMessage "  .\setup.ps1 -InitializeDb       # Initialize database" "White"
    Write-ColoredMessage "  .\setup.ps1 -SampleData         # Create sample data (use with -InitializeDb)" "White"
    Write-ColoredMessage "  .\setup.ps1 -CreateAdmin        # Create admin user (use with -InitializeDb)" "White"
    Write-ColoredMessage "  .\setup.ps1 -Run                # Run development server" "White"
    Write-ColoredMessage "  .\setup.ps1 -Docker             # Start Docker containers" "White"
    Write-ColoredMessage "Examples:" "Yellow"
    Write-ColoredMessage "  .\setup.ps1 -Setup -InitializeDb -SampleData -CreateAdmin" "Yellow"
    Write-ColoredMessage "  .\setup.ps1 -Run" "Yellow"
}
