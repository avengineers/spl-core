if (Test-Path -Path .git) {
    git config --local pull.rebase true
    Write-Host "git config --local pull.rebase was set to 'true'"
    git config --local fetch.prune true
    Write-Host "git config --local fetch.prune was set to 'true'"
} else {
    Write-Output "This is not a git repository, therefore no configuration was changed."
}
