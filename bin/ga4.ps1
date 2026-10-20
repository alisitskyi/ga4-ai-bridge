$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& python "$ScriptDir\..\src\ga4_ai\cli.py" $args
