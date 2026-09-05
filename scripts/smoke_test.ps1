$urls = @('/','/lessons','/lesson/1','/register','/login','/dashboard','/admin')
foreach ($u in $urls) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:5000$u" -UseBasicParsing -MaximumRedirection 0 -TimeoutSec 10 -ErrorAction Stop
        Write-Output "$u -> $($r.StatusCode)"
    } catch [System.Net.WebException] {
        $resp = $_.Exception.Response
        if ($resp -ne $null) {
            $code = $resp.StatusCode.value__
            Write-Output "$u -> $code"
        } else {
            Write-Output "$u -> ERROR: $($_.Exception.Message)"
        }
    } catch {
        Write-Output "$u -> ERROR: $_"
    }
}
