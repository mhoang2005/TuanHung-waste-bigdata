param([Parameter(Mandatory=$true)][string]$InputDocx,[Parameter(Mandatory=$true)][string]$OutputPdf)
$ErrorActionPreference='Stop'
$wordApp=$null
$wordDocument=$null
try {
    $wordApp=New-Object -ComObject Word.Application
    $wordApp.Visible=$false
    $wordApp.DisplayAlerts=0
    $wordDocument=$wordApp.Documents.Open($InputDocx,$false,$true)
    $wordDocument.Repaginate()
    $wordDocument.ExportAsFixedFormat($OutputPdf,17)
    Write-Output "Exported $OutputPdf"
} finally {
    if ($null -ne $wordDocument) { $wordDocument.Close(0); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordDocument) }
    if ($null -ne $wordApp) { $wordApp.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordApp) }
}
