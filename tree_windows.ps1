 [CmdletBinding()]
 param (
     [string]$Path = ".",
     [string]$OutputFile = "estrutura.txt",
     [string[]]$ExcludeDirs = @("node_modules", ".git", "bin", "obj", ".venv")
 )
 
function Show-Tree {
    param (
        [string]$Path = ".",
        [string]$OutputFile = "estrutura.txt",
        [string[]]$ExcludeDirs = @("node_modules", ".git", "bin", "obj", ".venv")
    )

    # Limpa arquivo de saída
    if (Test-Path $OutputFile) { Remove-Item $OutputFile }
    New-Item -ItemType File -Path $OutputFile | Out-Null

    function Show-TreeHelper {
        param (
            [string]$CurrentPath,
            [int]$Level
        )

        $indent = " " * ($Level * 2)
        $name = (Get-Item $CurrentPath).Name

        Add-Content -Path $OutputFile -Value "$indent$name"

        # Lista diretórios
        Get-ChildItem -Path $CurrentPath -Directory | Where-Object {
            $ExcludeDirs -notcontains $_.Name
        } | ForEach-Object {
            Show-TreeHelper -CurrentPath $_.FullName -Level ($Level + 1)
        }

        # Lista arquivos
        Get-ChildItem -Path $CurrentPath -File | ForEach-Object {
            Add-Content -Path $OutputFile -Value "$indent  $($_.Name)"
        }
    }

    Show-TreeHelper -CurrentPath $Path -Level 0
}

$isDotSourced = $MyInvocation.InvocationName -eq '.'
if (-not $isDotSourced) {
    Show-Tree -Path $Path -OutputFile $OutputFile -ExcludeDirs $ExcludeDirs
}
