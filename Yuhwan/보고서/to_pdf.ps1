# build_report.py output docx -> Word: insert footnotes, update TOC, save PDF
# usage: powershell -ExecutionPolicy Bypass -File to_pdf.ps1 <docx> <footnotes.json>
param([string]$docx, [string]$fnjson, [string]$pdf = "")
if (-not $pdf) { $pdf = [IO.Path]::ChangeExtension($docx, ".pdf") }
$fn = [IO.File]::ReadAllText($fnjson, [Text.Encoding]::UTF8) | ConvertFrom-Json

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open($docx)
try {
    # replace each {{fn:key}} marker with a real footnote (Word numbers them in document order)
    foreach ($p in $fn.PSObject.Properties) {
        $token = '{{fn:' + $p.Name + '}}'
        $rng = $doc.Content
        if ($rng.Find.Execute($token)) {
            $rng.Text = ''
            [void]$doc.Footnotes.Add($rng, [Type]::Missing, $p.Value)
        } else { Write-Output ('marker not found: ' + $p.Name) }
    }
    $left = $doc.Content; if ($left.Find.Execute('{{fn:')) { Write-Output 'leftover marker found' }
    $st = $doc.Styles.Item(-30)            # wdStyleFootnoteText
    $st.Font.Name = 'Malgun Gothic'; $st.Font.Size = 7.5; $st.ParagraphFormat.SpaceAfter = 1; $st.ParagraphFormat.LineSpacingRule = 0
    $doc.TablesOfContents.Item(1).Update()
    $doc.Save()
    $doc.SaveAs([ref]$pdf, [ref]17)
    Write-Output ('footnotes ' + $doc.Footnotes.Count + ', pages ' + $doc.ComputeStatistics(2))
} finally {
    if ($doc) { $doc.Close([ref]0) }
    $word.Quit()
}
