param(
    [Parameter(Mandatory=$true)]
    [string]$CsvPath,

    [Parameter(Mandatory=$true)]
    [string]$XlsxPath
)

$ErrorActionPreference = "Stop"

$csvFull = (Resolve-Path $CsvPath).Path
$xlsxFull = [System.IO.Path]::GetFullPath($XlsxPath)

try {
    $excel = New-Object -ComObject Excel.Application
} catch {
    Write-Host "Microsoft Excel COM automation is unavailable; keeping the Excel-friendly CSV." -ForegroundColor Yellow
    exit 0
}

$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    # Localized semicolon-separated UTF-8 text.
    # 65001 = UTF-8 code page.
    $excel.Workbooks.OpenText(
        $csvFull,
        65001,
        1,
        1,
        1,
        $false,
        $true,
        $false,
        $false,
        $false,
        $false
    )

    $wb = $excel.ActiveWorkbook
    $ws = $wb.Worksheets.Item(1)
    $ws.Name = "Deep Audit"

    $used = $ws.UsedRange
    $used.EntireColumn.AutoFit() | Out-Null

    # Freeze header row.
    $ws.Activate()
    $excel.ActiveWindow.SplitRow = 1
    $excel.ActiveWindow.FreezePanes = $true

    # Add AutoFilter to header row / used range.
    $used.AutoFilter() | Out-Null

    # 51 = xlOpenXMLWorkbook (.xlsx)
    $wb.SaveAs($xlsxFull, 51)
    $wb.Close($false)

    Write-Host "Excel workbook created: $xlsxFull" -ForegroundColor Green
}
finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
