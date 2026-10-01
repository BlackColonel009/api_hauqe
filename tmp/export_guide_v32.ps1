$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$sourceName = if ($args.Count -gt 0) { $args[0] } else { 'Guide_global_utilisation_SNGSC_HAUQE_v3_mis_a_jour.docx' }
$docxPath = Join-Path $workspace (Join-Path 'output\docx' $sourceName)
$reviewDir = Join-Path $workspace 'tmp\guide_v3_review_v32'
$pdfPath = Join-Path $reviewDir ([System.IO.Path]::GetFileNameWithoutExtension($sourceName) + '.htm')
New-Item -ItemType Directory -Force -Path $reviewDir | Out-Null
$tracePath = Join-Path $reviewDir 'word_export_trace.txt'
Set-Content -Path $tracePath -Value ('start ' + (Get-Date -Format o))

$word = New-Object -ComObject Word.Application
$word.Options.UpdateLinksAtOpen = $false
$word.AutomationSecurity = 3
$word.Visible = $false
$word.DisplayAlerts = 0
$word.ScreenUpdating = $false
$doc = $null
try {
    Add-Content -Path $tracePath -Value ('before-open ' + (Get-Date -Format o))
    $doc = $word.Documents.Open($docxPath, $false, $true, $false)
    Add-Content -Path $tracePath -Value ('after-open ' + (Get-Date -Format o))
    $doc.SaveAs2($pdfPath, 10)
    Add-Content -Path $tracePath -Value ('after-export ' + (Get-Date -Format o))
    Write-Output $pdfPath
}
finally {
    if ($null -ne $doc) { $doc.Close($false) }
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
