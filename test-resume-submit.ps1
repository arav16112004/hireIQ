function Submit-Resume {
    param(
        [Parameter(Mandatory=$true)]
        [string]$PdfPath,
        
        [Parameter(Mandatory=$true)]
        [string]$JobDescription,
        
        [Parameter(Mandatory=$true)]
        [int]$JobId,
        
        [Parameter(Mandatory=$false)]
        [string]$BaseUrl = "http://127.0.0.1:8000"
    )
    
    # Validate PDF file exists
    if (-not (Test-Path $PdfPath)) {
        Write-Error "PDF file not found: $PdfPath"
        return
    }
    
    Write-Host "Submitting resume: $PdfPath" -ForegroundColor Cyan
    Write-Host "Job ID: $JobId" -ForegroundColor Cyan
    Write-Host "Endpoint: $BaseUrl/candidates/ingest" -ForegroundColor Cyan
    
    try {
        # PowerShell 6+ (PowerShell Core) supports -Form parameter directly
        if ($PSVersionTable.PSVersion.Major -ge 6) {
            Write-Host "Using PowerShell 6+ form submission..." -ForegroundColor Green
            
            $form = @{
                file = Get-Item $PdfPath
                job_id = $JobId
                job_description = $JobDescription
            }
            
            $response = Invoke-RestMethod -Uri "$BaseUrl/candidates/ingest" `
                -Method Post `
                -Form $form `
                -ErrorAction Stop
        }
        else {
            # PowerShell 5.1 - Use HttpClient for proper multipart/form-data
            Write-Host "Using PowerShell 5.1 HttpClient approach..." -ForegroundColor Green
            
            Add-Type -AssemblyName System.Net.Http
            
            $httpClient = New-Object System.Net.Http.HttpClient
            $content = New-Object System.Net.Http.MultipartFormDataContent
            
            # Add file
            $fileStream = [System.IO.File]::OpenRead($PdfPath)
            $fileName = (Get-Item $PdfPath).Name
            $fileContent = New-Object System.Net.Http.StreamContent($fileStream)
            $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("application/pdf")
            $content.Add($fileContent, "file", $fileName)
            
            # Add job_id
            $jobIdContent = New-Object System.Net.Http.StringContent($JobId.ToString())
            $content.Add($jobIdContent, "job_id")
            
            # Add job_description
            $jobDescContent = New-Object System.Net.Http.StringContent($JobDescription)
            $content.Add($jobDescContent, "job_description")
            
            # Make request
            $responseTask = $httpClient.PostAsync("$BaseUrl/candidates/ingest", $content)
            $response = $responseTask.Result
            
            if ($response.IsSuccessStatusCode) {
                $responseBody = $response.Content.ReadAsStringAsync().Result
                $response = $responseBody | ConvertFrom-Json
            }
            else {
                $errorBody = $response.Content.ReadAsStringAsync().Result
                Write-Error "HTTP $($response.StatusCode): $errorBody"
                return
            }
            
            # Cleanup
            $fileStream.Close()
            $httpClient.Dispose()
            $content.Dispose()
        }
        
        # Display results
        Write-Host "`n=== Response ===" -ForegroundColor Green
        $response | ConvertTo-Json -Depth 10 | Write-Host
        
        return $response
    }
    catch {
        Write-Error "Request failed: $_"
        if ($_.Exception.Response) {
            try {
                $stream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream)
                $responseBody = $reader.ReadToEnd()
                Write-Host "`nError Response: $responseBody" -ForegroundColor Red
            }
            catch {
                Write-Host "Could not read error response" -ForegroundColor Red
            }
        }
        throw
    }
}

# Example usage:
# Submit-Resume -PdfPath "C:\path\to\resume.pdf" -JobDescription "Software Engineer position with experience in Python and FastAPI" -JobId 1

# Test with a sample call (uncomment to use):
# Submit-Resume -PdfPath "./sample_resume.pdf" -JobDescription "Backend Developer" -JobId 1
