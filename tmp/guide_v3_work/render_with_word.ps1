$ErrorActionPreference = 'Stop'
$source = 'C:\Users\hp\Documents\APK WEB Projets R.1.3.5 et R1.4.3\output\docx\Guide_global_utilisation_SNGSC_HAUQE_v3.docx'
$target = 'C:\Users\hp\Documents\APK WEB Projets R.1.3.5 et R1.4.3\tmp\guide_v3_work\Guide_global_utilisation_SNGSC_HAUQE_v3.pdf'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $document = $word.Documents.Open($source, $false, $true)
    try {
        $document.ExportAsFixedFormat($target, 17)
    }
    finally {
        $document.Close(0)
    }
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
Write-Output $target
