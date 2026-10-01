$ErrorActionPreference = 'Stop'

$workspace = Split-Path -Parent $PSScriptRoot
$docxPath = Join-Path $workspace 'output\docx\Guide_global_utilisation_SNGSC_HAUQE_v3_mis_a_jour.docx'
$reviewDir = Join-Path $workspace 'tmp\guide_v3_review'
$pdfPath = Join-Path $reviewDir 'Guide_global_utilisation_SNGSC_HAUQE_v3_mis_a_jour.pdf'
$donePath = Join-Path $reviewDir 'export.done'
$errorPath = Join-Path $reviewDir 'export.error.txt'

New-Item -ItemType Directory -Force -Path $reviewDir | Out-Null
Remove-Item -LiteralPath $donePath -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $errorPath -Force -ErrorAction SilentlyContinue

$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($docxPath, $false, $true)
    $document.ExportAsFixedFormat($pdfPath, 17)
    Set-Content -LiteralPath $donePath -Value 'ok' -Encoding ascii
}
catch {
    Set-Content -LiteralPath $errorPath -Value $_.Exception.ToString() -Encoding utf8
}
finally {
    if ($null -ne $document) { $document.Close($false) }
    if ($null -ne $word) {
        $word.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    }
}
