# Run from the top-level diaries directory.
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

.\scripts\windows\validation\verify-0026-step14.ps1 `
    -EvidenceDirectory ".\build\step14-$stamp" `
    -FullResponder -Client `
    -BackupFile ".\data\database-backups\development-infrastructure\diaries-development-20260929-222038.dump" `
    -LocalBuildEnvFile ".\config\environments\local-docker-build.env" `
    -PublishedSmokeEnvFile ".\config\environments\local-published-smoke.env" `
    -InspectPublishedImages
