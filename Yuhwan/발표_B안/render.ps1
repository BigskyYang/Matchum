param([string]$pptx, [string]$pdf)
$pp = New-Object -ComObject PowerPoint.Application
$p = $pp.Presentations.Open($pptx, $true, $false, $false)
$p.SaveAs($pdf, 32)
$n = $p.Slides.Count
$p.Close()
$pp.Quit()
Write-Output "slides $n"
