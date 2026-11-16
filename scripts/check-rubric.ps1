# Run:  powershell -ExecutionPolicy Bypass -File scripts\check-rubric.ps1
$root = Split-Path -Parent $PSScriptRoot
$checks = @(
  @{ Item = "1.2 /health endpoint in code";        Path = "app.py";                                Pattern = "/health" },
  @{ Item = "1.3 Packaged artifact (git archive)"; Path = "Jenkinsfile";                           Pattern = "git archive" },
  @{ Item = "1.4 Jenkinsfile + SCM trigger";       Path = "Jenkinsfile";                           Pattern = "pollSCM" },
  @{ Item = "1.4 Jenkins archives artifact";       Path = "Jenkinsfile";                           Pattern = "archiveArtifacts" },
  @{ Item = "1.5A Jenkins Test stage";             Path = "Jenkinsfile";                           Pattern = "stage\('Test'\)" },
  @{ Item = "1.5A Unit tests folder";              Path = "tests";                                 Pattern = "" },
  @{ Item = "1.5B Versioned tag (SHA/build id)";   Path = "Jenkinsfile";                           Pattern = "SHORT_SHA" },
  @{ Item = "1.5C GitHub Actions workflow";        Path = ".github/workflows/ci.yml";              Pattern = "" },
  @{ Item = "2.1 Ansible inventory";               Path = "ansible/inventory";                     Pattern = "" },
  @{ Item = "2.1 Ansible variable";                Path = "ansible/group_vars/all.yml";            Pattern = "app_port" },
  @{ Item = "2.1 Ansible handler";                 Path = "ansible/roles/app/handlers/main.yml";   Pattern = "Restart app" },
  @{ Item = "2.1 Ansible role (galaxy layout)";    Path = "ansible/roles/app/tasks/main.yml";      Pattern = "" },
  @{ Item = "2.2 Dockerfile";                      Path = "Dockerfile";                            Pattern = "CMD" },
  @{ Item = "2.3 Deployment with 3 replicas";      Path = "k8s/deployment.yaml";                   Pattern = "replicas: 3" },
  @{ Item = "2.3 Service (NodePort)";              Path = "k8s/service.yaml";                      Pattern = "NodePort" },
  @{ Item = "2.5B ConfigMap";                      Path = "k8s/configmap.yaml";                    Pattern = "ConfigMap" },
  @{ Item = "2.5C Probes";                         Path = "k8s/deployment.yaml";                   Pattern = "livenessProbe" },
  @{ Item = "2.5D Multi-stage Dockerfile";         Path = "Dockerfile";                            Pattern = "AS build" }
)
$missing = 0
foreach ($c in $checks) {
  $p = Join-Path $root $c.Path
  $ok = Test-Path $p
  if ($ok -and $c.Pattern -ne "") { $ok = [bool](Select-String -Path $p -Pattern $c.Pattern -Quiet) }
  if ($ok) { Write-Host ("[ OK ] " + $c.Item) -ForegroundColor Green }
  else     { Write-Host ("[MISS] " + $c.Item) -ForegroundColor Red; $missing++ }
}
Push-Location $root
$branchCount = (git branch -a 2>$null | Measure-Object).Count
$merges = (git log --merges --oneline 2>$null | Measure-Object).Count
if ($branchCount -ge 2) { Write-Host "[ OK ] 1.1 At least two branches" -ForegroundColor Green } else { Write-Host "[MISS] 1.1 At least two branches" -ForegroundColor Red; $missing++ }
if ($merges -ge 1)      { Write-Host "[ OK ] 1.1 Merge commit present"  -ForegroundColor Green } else { Write-Host "[MISS] 1.1 Merge commit present"  -ForegroundColor Red; $missing++ }
Pop-Location
Write-Host ""
if ($missing -eq 0) { Write-Host "All rubric items present." -ForegroundColor Green } else { Write-Host "$missing item(s) missing." -ForegroundColor Yellow }