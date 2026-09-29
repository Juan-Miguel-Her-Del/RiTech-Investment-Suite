$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path -LiteralPath '.env')) {
    $randomBytes = New-Object byte[] 32
    $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    $generator.GetBytes($randomBytes)
    $databasePassword = [BitConverter]::ToString($randomBytes).Replace('-', '')
    $generator.GetBytes($randomBytes)
    $signingSecret = [BitConverter]::ToString($randomBytes).Replace('-', '')
    $generator.Dispose()
    $template = Get-Content -LiteralPath '.env.example' -Raw
    $template = $template.Replace('POSTGRES_PASSWORD=', "POSTGRES_PASSWORD=$databasePassword")
    $template = $template.Replace('JWT_SECRET=', "JWT_SECRET=$signingSecret")
    $template = $template.Replace('CAMBIAR', $databasePassword)
    Set-Content -LiteralPath '.env' -Value $template -Encoding utf8
    Write-Host 'Archivo .env creado con secretos aleatorios locales.'
}
docker compose up --build -d --wait
if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar el entorno. Verifica que Docker Desktop esté iniciado.' }
