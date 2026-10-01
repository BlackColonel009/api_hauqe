param(
    [string]$SourceName = 'Guide_global_utilisation_SNGSC_HAUQE_v3_mis_a_jour.docx'
)

$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$docxPath = Join-Path $workspace (Join-Path 'output\docx' $SourceName)
$outDir = Join-Path $workspace 'tmp\guide_v32_word_pages'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Get-ChildItem -LiteralPath $outDir -File -ErrorAction SilentlyContinue | Remove-Item -Force

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.Options.UpdateLinksAtOpen = $false
$word.AutomationSecurity = 3
$doc = $null

try {
    $doc = $word.Documents.Open($docxPath, $false, $true, $false)
    $doc.Repaginate()
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    foreach ($tof in $doc.TablesOfFigures) { $tof.Update() }
    $doc.Fields.Update() | Out-Null
    foreach ($section in $doc.Sections) {
        foreach ($header in $section.Headers) { $header.Range.Fields.Update() | Out-Null }
        foreach ($footer in $section.Footers) { $footer.Range.Fields.Update() | Out-Null }
    }
    $doc.Repaginate()
    $window = $doc.ActiveWindow
    $window.View.Type = 3
    $pageCount = $doc.ComputeStatistics(2)
    $renderableCount = $window.Panes.Item(1).Pages.Count
    Write-Output "pages=$pageCount renderable=$renderableCount"

    for ($index = 1; $index -le $pageCount; $index++) {
        $page = $window.Panes.Item(1).Pages.Item($index)
        $bytes = $page.EnhMetaFileBits
        $emfPath = Join-Path $outDir ('page-{0:D3}.emf' -f $index)
        [System.IO.File]::WriteAllBytes($emfPath, $bytes)
        Write-Output $emfPath
    }
}
finally {
    if ($null -ne $doc) { $doc.Close($false) }
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
