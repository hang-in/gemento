# Stage 2C Task 04 — H4 재검증 3 condition 차례 실행 스크립트
#
# 사용:
#   cd D:\privateProject\gemento
#   .\experiments\exp_h4_recheck\run_all.ps1
#
# 동작:
#   1) solo_1call (~1h) → 2) solo_budget (~8h) → 3) abc (~10h) 차례 실행
#   각 condition 별 별도 결과 파일. 한 condition 이 fatal abort 시 다음 condition 도 중단
#   (Stage 2A healthcheck 신호가 의미 있는 정보 — 사용자 호출 의무).
#
# 환경:
#   - LM Studio at http://192.168.1.179:1234
#   - .venv\Scripts\python.exe
#   - Stage 2A healthcheck/abort + Stage 2B FailureLabel 모두 적용 (commit f16aaef 기준)

$ErrorActionPreference = "Stop"
$env:GEMENTO_API_BASE_URL = "http://192.168.1.179:1234"

$python = ".\.venv\Scripts\python.exe"
$module = "experiments.exp_h4_recheck.run"
$conditions = @("solo_1call", "solo_budget", "abc")

$startedAt = Get-Date
Write-Host ""
Write-Host "================================================================================"
Write-Host "  H4 재검증 (Stage 2C Task 04) — 3 condition 차례 실행"
Write-Host "  시작: $($startedAt.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "  endpoint: $($env:GEMENTO_API_BASE_URL)"
Write-Host "  taskset: 15 task × 3 condition × 5 trial = 225 trial 예상"
Write-Host "================================================================================"
Write-Host ""

foreach ($cond in $conditions) {
    $condStart = Get-Date
    Write-Host ""
    Write-Host "################################################################################"
    Write-Host "# [$($conditions.IndexOf($cond) + 1)/$($conditions.Count)] CONDITION: $cond"
    Write-Host "# 시작: $($condStart.ToString('HH:mm:ss'))"
    Write-Host "################################################################################"
    Write-Host ""

    $outName = "h4_recheck_$cond.json"
    & $python -m $module `
        --conditions $cond `
        --trials 5 `
        --max-cycles 8 `
        --out-name $outName

    $exitCode = $LASTEXITCODE
    $condEnd = Get-Date
    $elapsed = $condEnd - $condStart

    Write-Host ""
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host "  CONDITION 완료: $cond"
    Write-Host "  소요: $($elapsed.ToString('hh\:mm\:ss'))"
    Write-Host "  exit code: $exitCode"
    Write-Host "  출력 파일: experiments\exp_h4_recheck\results\$outName"
    Write-Host "--------------------------------------------------------------------------------"

    if ($exitCode -ne 0) {
        Write-Host ""
        Write-Host "[ABORT] $cond exit code $exitCode — fatal abort 또는 reject 발동"
        Write-Host "[ABORT] 남은 condition ($($conditions[($conditions.IndexOf($cond) + 1)..($conditions.Count - 1)] -join ', ')) 진행 중단"
        Write-Host "[ABORT] 사용자 호출 권장 — Stage 2A healthcheck 신호 분석 후 결정"
        exit $exitCode
    }
}

$endedAt = Get-Date
$totalElapsed = $endedAt - $startedAt
Write-Host ""
Write-Host "================================================================================"
Write-Host "  H4 재검증 완료"
Write-Host "  시작: $($startedAt.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "  종료: $($endedAt.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "  총 소요: $($totalElapsed.ToString('hh\:mm\:ss'))"
Write-Host "  출력 파일 (3개):"
foreach ($cond in $conditions) {
    Write-Host "    experiments\exp_h4_recheck\results\h4_recheck_$cond.json"
}
Write-Host "================================================================================"
Write-Host ""
Write-Host "다음 단계: 출력 파일 경로를 Architect 에게 전달 → Task 05 분석/문서 갱신 진행"
