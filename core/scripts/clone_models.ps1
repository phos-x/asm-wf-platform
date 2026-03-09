param(
    [string]$Root = ".."
)

Import-Module powershell-yaml -ErrorAction Stop

function New-SafeDirectory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

$projectRoot = Resolve-Path $Root
$configPath = Join-Path $projectRoot "config/models.yaml"

if (-not (Test-Path -LiteralPath $configPath)) {
    Write-Error "config/models.yaml not found at $configPath"
    exit 1
}

$config = Get-Content $configPath -Raw | ConvertFrom-Yaml
$models = $config.models

foreach ($modelKey in $models.Keys) {
    $m = $models[$modelKey]
    $repo       = $m.repo
    $branch     = $m.branch
    $targetDir  = Join-Path $projectRoot $m.target_dir
    $trainPath  = Join-Path $targetDir $m.train_script
    $inferPath  = Join-Path $targetDir $m.infer_script
    $configFile = Join-Path $targetDir $m.config_path

    Write-Host "==> Processing model '$modelKey' from $repo (branch: $branch)" -ForegroundColor Cyan
    New-SafeDirectory $targetDir

    if (-not (Test-Path -LiteralPath (Join-Path $targetDir ".git"))) {
        Write-Host "   Cloning into $targetDir..."
        git clone $repo $targetDir
    } else {
        Write-Host "   Repo already exists, skipping clone."
    }

    Push-Location $targetDir
    try {
        git fetch origin
        git checkout $branch
        git pull origin $branch
    } finally {
        Pop-Location
    }

    if (-not (Test-Path -LiteralPath $trainPath)) {
        Write-Error "Train script not found for '$modelKey': $trainPath"
    }
    if (-not (Test-Path -LiteralPath $inferPath)) {
        Write-Error "Infer script not found for '$modelKey': $inferPath"
    }
    if (-not (Test-Path -LiteralPath $configFile)) {
        Write-Error "Config file not found for '$modelKey': $configFile"
    }

    $runSetup = $false
    if ($m.PSObject.Properties.Name -contains "run_setup") {
        $runSetup = [bool]$m.run_setup
    }

    if ($runSetup -and $m.setup) {
        Write-Host "   Running setup commands for '$modelKey'..."
        Push-Location $targetDir
        try {
            foreach ($cmd in $m.setup) {
                Write-Host "     > $cmd"
                & bash -lc $cmd 2>&1
            }
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "   Setup skipped for '$modelKey' (run_setup=false or no commands)."
    }
}
