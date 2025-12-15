<#
=========X=========X=========X=========X=========X=========X=========X=========X

Script ps1 Script-PS-Func.ps1

Auteur : Rahman AYSAN

Version : 11 Decembre 2025

Description : Test de scripts Powershell. Ce script fonctionne et a été testé pour 
se connecter sur un serveur Windows de test et exécuter des commandes Powershell à distance

On peut se connecter via nos identifiants Admin et copier des fichiers depuis le serveur distant 
vers notre machine locale.

Utilisation : en mode administrateur

Si le script ne s'execute pas, faire la commande suivante : 

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

NOTE : 

Pour supprimer la strategie d'execution pour tous les utilisateurs de l'ordinateur local :

Set-ExecutionPolicy -ExecutionPolicy Undefined -Scope LocalMachine

ou pour supprimer la strategie d'execution de l'utilisateur actuel

Set-ExecutionPolicy -ExecutionPolicy Undefined -Scope CurrentUser

=========X=========X=========X=========X=========X=========X=========X=========X
#>
cls

Get-Service -Name W32Time

Write-Host ("`nVersion de Powershell : ")
$PSVersionTable.PSVersion
$curTime = get-date -format HH:mm
$curDate = get-date -format dd/MM/yyyy

Write-Host ("`nL'heure : {0}`nLa date : {1}" -f $curTime, $curDate)

$host1 = hostname

$host2 = [Environment]::MachineName

Write-Host ("`nLe nom de la machine : {0}`nHostname : {1}" -f $host1, $host2)

$workflow = Resolve-DnsName -Name 192.168.17.6 | Select-Object -ExpandProperty NameHost
Write-Host ("`nWorkflow TEST Server DNS : https://{0}" -f $workflow)

# Get-ComputerInfo -Property CSName

$host3 = $env:COMPUTERNAME

Write-Host ("`nCurrent Local ComputerName : {0}`n" -f $host3)

$cred = Get-Credential
$session = New-PSSession -ComputerName "192.168.17.6" -Credential $cred

# Copier le fichier depuis la machine distante vers la machine locale

$USER = (Get-WmiObject -Class Win32_ComputerSystem).UserName
$LOCAL_USER = $USER.Split('\')[1]

$sourcePath = "C:\Apache24\htdocs\test-func.php"
$destinationPath = "C:\Users\$LOCAL_USER\Desktop\test-func.php"

Copy-Item -Path $sourcePath -Destination $destinationPath -FromSession $session

# Vérifier si la copie a réussi
Write-Host "`nLe fichier a été copié vers : $destinationPath"

Write-Host "`nBonjour $LOCAL_USER,"

Write-Host "`nLa session locale est : $session"

Enter-PSSession -Session $session

# Cela doit être fait dans la session distante après être entré en mode interactif avec Enter-PSSession

# Exécuter une commande à distance pour afficher le nom de la machine distante
Invoke-Command -Session $session -ScriptBlock {
    Write-Host "`nVous êtes maintenant connecté à la machine distante : $env:COMPUTERNAME"
}

# Fermer la session distante lorsque vous avez terminé
Exit-PSSession

Write-Host "`n**********FIN DE LA SESSION**********"

# Fermer la session
Remove-PSSession -Session $session
