Write-Output '--- Get-MpThreatDetection (first 20) ---'
Get-MpThreatDetection | Select-Object -First 20 | Format-List
Write-Output '\n--- Exclusions ---'
Get-MpPreference | Format-List -Property ExclusionProcess,ExclusionExtension,ExclusionPath
