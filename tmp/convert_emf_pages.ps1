$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$workspace = Split-Path -Parent $PSScriptRoot
$sourceDir = Join-Path $workspace 'tmp\guide_v32_word_pages'
$outputDir = Join-Path $workspace 'tmp\guide_v32_word_pngs'
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
Get-ChildItem -LiteralPath $outputDir -File -ErrorAction SilentlyContinue | Remove-Item -Force

foreach ($file in (Get-ChildItem -LiteralPath $sourceDir -Filter '*.emf' | Sort-Object Name)) {
    $meta = New-Object System.Drawing.Imaging.Metafile($file.FullName)
    try {
        $unit = [System.Drawing.GraphicsUnit]::Pixel
        $bounds = $meta.GetBounds([ref]$unit)
        $targetWidth = 1240
        $targetHeight = [int][Math]::Round($targetWidth * $bounds.Height / $bounds.Width)
        $bitmap = New-Object System.Drawing.Bitmap($targetWidth, $targetHeight)
        try {
            $bitmap.SetResolution(150, 150)
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            try {
                $graphics.Clear([System.Drawing.Color]::White)
                $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
                $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                $graphics.DrawImage($meta, 0, 0, $targetWidth, $targetHeight)
            }
            finally { $graphics.Dispose() }
            $outPath = Join-Path $outputDir ($file.BaseName + '.png')
            $bitmap.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally { $bitmap.Dispose() }
    }
    finally { $meta.Dispose() }
}

Write-Output ((Get-ChildItem -LiteralPath $outputDir -Filter '*.png').Count)
