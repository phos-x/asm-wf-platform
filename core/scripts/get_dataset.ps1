# Script to download datasets from registry/datasets.yaml
# Downloads to datasets/raw and handles zip/tar extraction

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$ConfigFile = Join-Path $ProjectRoot "core/registry/datasets.yaml"
$RawDir = Join-Path $ProjectRoot "core/datasets/raw"

# Validate dependencies
function Test-Dependencies {
    $deps = @("curl", "tar")
    foreach ($cmd in $deps) {
        if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
            Write-Error "$cmd is required but not installed."
            exit 1
        }
    }
}

# Create raw directory if it doesn't exist
function Initialize-Directories {
    if (-not (Test-Path $RawDir)) {
        New-Item -ItemType Directory -Path $RawDir -Force | Out-Null
    }
}

# Download and extract dataset
function Get-Dataset {
    param(
        [string]$DatasetName,
        [string]$DownloadLink
    )
    
    $DatasetDir = Join-Path $RawDir $DatasetName
    New-Item -ItemType Directory -Path $DatasetDir -Force | Out-Null
    
    Write-Host "Downloading $DatasetName..."
    
    if ($DownloadLink -match '\.(tar\.gz|tar)$') {
        Invoke-WebRequest -Uri $DownloadLink -OutFile - | tar -xz -C $DatasetDir
        Write-Host "Extracted tar archive to $DatasetDir"
    }
    elseif ($DownloadLink -match '\.zip$') {
        $ZipFile = Join-Path $DatasetDir "$DatasetName.zip"
        Invoke-WebRequest -Uri $DownloadLink -OutFile $ZipFile
        Expand-Archive -Path $ZipFile -DestinationPath $DatasetDir
        Remove-Item $ZipFile
        Write-Host "Extracted zip and removed archive"
    }
    else {
        Invoke-WebRequest -Uri $DownloadLink -OutFile (Join-Path $DatasetDir "data")
        Write-Host "Downloaded to $DatasetDir"
    }
}

# Main execution
function Main {
    Test-Dependencies
    
    if (-not (Test-Path $ConfigFile)) {
        Write-Error "Config file not found at $ConfigFile"
        exit 1
    }
    
    Initialize-Directories
    
    $yaml = Get-Content $ConfigFile | ConvertFrom-Yaml
    
    foreach ($datasetName in $yaml.datasets.Keys) {
        $link = $yaml.datasets[$datasetName].link
        
        if ([string]::IsNullOrEmpty($link) -or $link -eq "null") {
            Write-Warning "No link found for dataset $datasetName"
            continue
        }
        
        Get-Dataset $datasetName $link
    }
    
    Write-Host "Dataset download complete!"
}

Main