Set oShell = CreateObject("WScript.Shell")

' Verificar si el servidor ya esta corriendo en puerto 8000
Dim sOutput, bRunning
bRunning = False
Set oExec = oShell.Exec("cmd /c netstat -an")
sOutput = oExec.StdOut.ReadAll()
If InStr(sOutput, ":8000") > 0 Then
    bRunning = True
End If

' Si no esta corriendo, iniciarlo silenciosamente
If Not bRunning Then
    oShell.Run "cmd /c cd /d C:\nexus && python nexus_server.py > C:\nexus\logs\server_web.log 2>&1", 0, False
    WScript.Sleep 3500
End If

' Abrir el dashboard en el navegador
oShell.Run "http://localhost:8000/dashboard"
