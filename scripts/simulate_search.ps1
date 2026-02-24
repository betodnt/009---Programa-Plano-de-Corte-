# Simula busca por arquivos .cnc com progresso
$searchPath = '\\servidor\PRODUCAO\8. CONTROLE DE PRODUÇÃO\1. SAÍDAS A CORTAR'
if (-not (Test-Path $searchPath)) {
    $temp = Join-Path $PWD 'test_search'
    if (-not (Test-Path $temp)) {
        Write-Host "Criando pasta de teste: $temp"
        New-Item -ItemType Directory -Path $temp | Out-Null
        for ($i=1; $i -le 2000; $i++) {
            $name = ('P{0:D5}_X_{1}.cnc' -f ($i % 1000), $i)
            New-Item -Path (Join-Path $temp $name) -ItemType File -Force | Out-Null
        }
        # arquivo correspondente para o pedido 00042
        New-Item -Path (Join-Path $temp 'P00042_match_S1.cnc') -ItemType File -Force | Out-Null
    }
    $searchPath = $temp
} else {
    Write-Host "Usando caminho UNC existente: $searchPath"
}

Write-Host "Iniciando busca em: $searchPath"
$files = Get-ChildItem -Path $searchPath -Recurse -Filter '*.cnc' -File
$total = $files.Count
Write-Host "Total de arquivos encontrados: $total"
$i = 0
$pedido = '00042'
$prefix = 'P'
$matches = @()

foreach ($f in $files) {
    $i++
    $percent = [int](($i / $total) * 100)
    Write-Progress -Activity 'Buscando .cnc' -Status "$i de $total" -PercentComplete $percent
    $base = $f.Name
    $parts = $base -split '_'
    foreach ($p in $parts) {
        if ($p.StartsWith($prefix) -and $p.Substring(1) -eq $pedido) {
            $matches += $f.FullName
            break
        }
    }
    Start-Sleep -Milliseconds 1
}

Write-Host "Busca completa. Achados: $($matches.Count)"
if ($matches.Count -gt 0) {
    $matches | Select-Object -First 10 | ForEach-Object { Write-Host "  " $_ }
}
