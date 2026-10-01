$ErrorActionPreference = 'Stop'

$workspace = Split-Path -Parent $PSScriptRoot
$docxPath = Join-Path $workspace 'output\docx\Guide_global_utilisation_SNGSC_HAUQE_v3_mis_a_jour.docx'
$reviewDir = Join-Path $workspace 'tmp\guide_v3_review'
$pdfPath = Join-Path $reviewDir 'Guide_global_utilisation_SNGSC_HAUQE_v3_mis_a_jour.pdf'

New-Item -ItemType Directory -Force -Path $reviewDir | Out-Null

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$document = $null

try {
    $document = $word.Documents.Open($docxPath, $false, $false)
    foreach ($toc in $document.TablesOfContents) {
        $toc.Update()
    }
    foreach ($tof in $document.TablesOfFigures) {
        $tof.Update()
    }
    $document.Fields.Update() | Out-Null
    foreach ($section in $document.Sections) {
        foreach ($header in $section.Headers) {
            $header.Range.Fields.Update() | Out-Null
        }
        foreach ($footer in $section.Footers) {
            $footer.Range.Fields.Update() | Out-Null
        }
    }
    $document.Save()
    $document.ExportAsFixedFormat($pdfPath, 17)
}
finally {
    if ($null -ne $document) {
        $document.Close($false)
    }
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}

Write-Output $pdfPath
