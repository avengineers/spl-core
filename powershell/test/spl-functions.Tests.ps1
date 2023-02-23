# to execute tests you have to
# 1. Update 'Pester': "Install-Module -Name Pester -Force -SkipPublisherCheck"
# 2. call "Invoke-Pester spl-functions.Tests.ps1" from within the test directory
# Note: I noticed that sometimes after a test was changed it will fail with a overloading problem; retry helps

BeforeAll {
  . .\..\spl-functions.ps1
}

Describe "invoking command line calls" {
  BeforeEach{
    Mock -CommandName Write-Information -MockWith {}
    $global:LASTEXITCODE = 0
  }

  It "shall not write the command to console if silent" {
    Invoke-CommandLine -CommandLine "dir" -Silent $true -StopAtError $true
    Should -Invoke -CommandName Write-Information -Times 0
  }

  It "shall write the command to console as default" {
    Invoke-CommandLine -CommandLine "dir"
    Should -Invoke -CommandName Write-Information -Times 1
  }

  It "shall print an error on failure" {
    $ErrorActionPreference = "Stop"
    Mock -CommandName Invoke-Expression -MockWith {$global:LASTEXITCODE = 1}

    Invoke-CommandLine -CommandLine "dir" -Silent $false -StopAtError $false
    Should -Invoke -CommandName Write-Information -Times 2
  }
}

Describe "running setup scripts" {
  It "shall not search for files if directory does not exist" {
    Mock -CommandName Test-Path -MockWith {$false}
    Mock -CommandName Get-ChildItem -MockWith {}

    Invoke-Setup-Script('mypath')
    Should -Invoke -CommandName Get-ChildItem -Times 0
  }

  It "shall print every file it finds and call it" {
    Mock -CommandName ForEach-Object -MockWith {}
    Mock -CommandName Test-Path -MockWith {$true}
    Mock -CommandName Get-ChildItem -MockWith {
      @(
        @{"FullName" = "file1.txt"}
        @{"FullName" = "file2.txt"}
      )
    }

    Invoke-Setup-Script('mypath')
    Should -Invoke -CommandName ForEach-Object -Times 2
  }
}

Describe "import project with transformer" {
  BeforeEach{
    Mock -CommandName Remove-Item -MockWith {}
  }

  It "shall always cleanup existing directories when called" {
    Mock -CommandName New-Item -MockWith {}
    Mock -CommandName Push-Location -MockWith {}
    Mock -CommandName git -MockWith {}
    Mock -CommandName Invoke-CommandLine -MockWith {}
    Mock -CommandName Pop-Location -MockWith {}
    Mock -CommandName Test-Path -MockWith {$true}

    Invoke-Transformer -Source "mysource" -Variant "myvariant"
    Should -Invoke -CommandName Remove-Item -Times 1
  }

  It "shall shallow clone all the time" {
    Mock -CommandName New-Item -MockWith {}
    Mock -CommandName Push-Location -MockWith {}
    Mock -CommandName git -MockWith {}
    Mock -CommandName Invoke-CommandLine -MockWith {}
    Mock -CommandName Pop-Location -MockWith {}
    Mock -CommandName Test-Path -MockWith {$true} -ParameterFilter { $Path -eq "build/import" }
    Mock -CommandName Test-Path -MockWith {$false} -ParameterFilter { $Path -eq ".git" }
    Mock -CommandName Test-Path -MockWith {$true} -ParameterFilter { $Path -eq "./build/import/transformer/.git" }

    Invoke-Transformer -Source "mysource" -Variant "myvariant" -Clean $true
    Should -Invoke -CommandName Remove-Item -Times 1
    Should -Invoke -CommandName git -Times 1
    Should -Invoke -CommandName New-Item -Times 1
  }
}

Describe "running CMake" {
  BeforeEach{
    Mock -CommandName Invoke-CommandLine -MockWith {}
  }

  It "shall run target selftests" {
    Invoke-CMake-Build -Target "selftests" -Variants "myvariant" -Filter "" -NinjaArgs "" -Clean $false -Reconfigure $false
    Should -Invoke -CommandName Invoke-CommandLine -Times 1
  }

  It "shall run target selftests and clean before and filter" {
    Mock -CommandName Remove-Item -MockWith {}
    Mock -CommandName Test-Path -MockWith {$true}

    Invoke-CMake-Build -Target "selftests" -Variants "myvariant" -Filter "abc" -NinjaArgs "" -Clean $true -Reconfigure $false
    Should -Invoke -CommandName Invoke-CommandLine -Times 1
    Should -Invoke -CommandName Remove-Item -Times 1
  }

  It "shall run multiple CLI commands for other targets and also delete files to reconfigure" {
    Mock -CommandName Remove-Item -MockWith {}
    Mock -CommandName Test-Path -MockWith {$true}

    Invoke-CMake-Build -Target "mytarget" -Variants "myvariant" -Filter "abc" -NinjaArgs "" -Clean $false -Reconfigure $true
    Should -Invoke -CommandName Invoke-CommandLine -Times 3
    Should -Invoke -CommandName Remove-Item -Times 2
  }
}
