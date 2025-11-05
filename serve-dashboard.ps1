$path = "C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra"
$url = "http://localhost:3030/"

Write-Host "Starting simple HTTP server for Cost Dashboard at $url" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add($url)
$listener.Start()

Write-Host "Server is running. Opening browser..." -ForegroundColor Green
Start-Process $url

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response
        
        $filePath = $path + $request.Url.LocalPath
        if ($request.Url.LocalPath -eq "/") {
            $filePath = $path + "/cost-dashboard.html"
        }
        
        if (Test-Path $filePath -PathType Leaf) {
            $content = [System.IO.File]::ReadAllBytes($filePath)
            $response.ContentLength64 = $content.Length
            $response.OutputStream.Write($content, 0, $content.Length)
        } else {
            $response.StatusCode = 404
        }
        
        $response.Close()
    }
} finally {
    $listener.Stop()
}
