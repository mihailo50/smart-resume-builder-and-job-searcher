# PowerShell script to test AI analysis endpoints
# Usage: .\test_ai_endpoints.ps1 -ResumeId "your-resume-id" -Token "your-auth-token"

param(
    [Parameter(Mandatory=$true)]
    [string]$ResumeId,
    
    [Parameter(Mandatory=$true)]
    [string]$Token,
    
    [string]$BaseUrl = "http://localhost:8000"
)

$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $Token"
}

Write-Host "Testing AI Analysis Endpoint..." -ForegroundColor Cyan
Write-Host "=" * 50

# Test 1: Analyze Resume with job description
$analyzeBody = @{
    resume_id = $ResumeId
    job_desc = "Looking for developer with docker, aws, heroku experience."
} | ConvertTo-Json

Write-Host "`n1. Testing analyze-resume endpoint..." -ForegroundColor Yellow
Write-Host "Request body:" -ForegroundColor Gray
Write-Host $analyzeBody

try {
    $analyzeResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/ai/analyze-resume/" `
        -Method POST `
        -Headers $headers `
        -Body $analyzeBody `
        -ErrorAction Stop
    
    Write-Host "`nResponse:" -ForegroundColor Green
    $analyzeResponse | ConvertTo-Json -Depth 10
    
    Write-Host "`nKey Results:" -ForegroundColor Cyan
    Write-Host "  ATS Score: $($analyzeResponse.ats_score)"
    Write-Host "  Missing Keywords: $($analyzeResponse.missing_keywords -join ', ')"
    Write-Host "  Readability Score: $($analyzeResponse.readability_score)"
    Write-Host "  Bullet Strength: $($analyzeResponse.bullet_strength)"
    Write-Host "  Quantifiable Achievements: $($analyzeResponse.quantifiable_achievements)"
    
    # Check if keywords are correctly detected
    $missing = $analyzeResponse.missing_keywords
    if ($missing -contains "docker" -or $missing -contains "aws" -or $missing -contains "heroku") {
        Write-Host "`n⚠️  WARNING: Keywords 'docker', 'aws', or 'heroku' are in missing_keywords!" -ForegroundColor Red
        Write-Host "   They should be found if present in optimized_summary, projects, or certifications." -ForegroundColor Yellow
    } else {
        Write-Host "`n✅ Keywords correctly detected (not in missing_keywords)" -ForegroundColor Green
    }
    
} catch {
    Write-Host "`n❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

Write-Host "`n" + ("=" * 50)
Write-Host "Testing Apply Suggestions Endpoint..." -ForegroundColor Cyan

# Test 2: Apply Suggestions
$applyBody = @{
    resume_id = $ResumeId
    suggestions = @(
        @{
            type = "keyword"
            text = "Add Kubernetes keyword"
            priority = "high"
        }
    )
    missing_keywords = @("kubernetes")
} | ConvertTo-Json -Depth 10

Write-Host "`n2. Testing apply-suggestions endpoint..." -ForegroundColor Yellow
Write-Host "Request body:" -ForegroundColor Gray
Write-Host $applyBody

try {
    $applyResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/ai/apply-suggestions/" `
        -Method POST `
        -Headers $headers `
        -Body $applyBody `
        -ErrorAction Stop
    
    Write-Host "`nResponse:" -ForegroundColor Green
    $applyResponse | ConvertTo-Json -Depth 10
    
    Write-Host "`nKey Results:" -ForegroundColor Cyan
    Write-Host "  Changes Applied: $($applyResponse.changes_applied -join ', ')"
    
    if ($applyResponse.resume_data) {
        Write-Host "  Resume Data Updated: ✅"
        Write-Host "  Skills Count: $($applyResponse.resume_data.skills.Count)"
    } else {
        Write-Host "  Resume Data Updated: ❌ (missing)"
    }
    
} catch {
    Write-Host "`n❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

Write-Host "`n" + ("=" * 50)
Write-Host "Tests Complete!" -ForegroundColor Cyan



