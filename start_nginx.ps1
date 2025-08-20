# Nginx启动脚本
# 项目升级计划 - Nginx服务管理

param(
    [string]$Action = "start",
    [string]$NginxPath = "C:\nginx",
    [string]$ConfigPath = "nginx.conf"
)

# 获取当前脚本目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDir
$FullConfigPath = Join-Path $ProjectRoot $ConfigPath

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# 检查Nginx是否已安装
function Test-NginxInstallation {
    $nginxExe = Join-Path $NginxPath "nginx.exe"
    if (Test-Path $nginxExe) {
        return $true
    }
    return $false
}

# 检查Nginx进程
function Get-NginxProcess {
    return Get-Process -Name "nginx" -ErrorAction SilentlyContinue
}

# 启动Nginx
function Start-Nginx {
    Write-ColorOutput "🚀 启动Nginx服务..." "Green"
    
    # 检查配置文件
    if (-not (Test-Path $FullConfigPath)) {
        Write-ColorOutput "❌ 配置文件不存在: $FullConfigPath" "Red"
        return $false
    }
    
    # 检查Nginx安装
    if (-not (Test-NginxInstallation)) {
        Write-ColorOutput "❌ Nginx未安装在: $NginxPath" "Red"
        Write-ColorOutput "请先安装Nginx或修改NginxPath参数" "Yellow"
        return $false
    }
    
    # 检查是否已运行
    $existingProcess = Get-NginxProcess
    if ($existingProcess) {
        Write-ColorOutput "⚠️  Nginx已在运行 (PID: $($existingProcess.Id))" "Yellow"
        return $true
    }
    
    try {
        # 切换到Nginx目录
        Push-Location $NginxPath
        
        # 启动Nginx
        $nginxExe = Join-Path $NginxPath "nginx.exe"
        Start-Process -FilePath $nginxExe -ArgumentList "-c", $FullConfigPath -WindowStyle Hidden
        
        # 等待启动
        Start-Sleep -Seconds 2
        
        # 验证启动
        $process = Get-NginxProcess
        if ($process) {
            Write-ColorOutput "✅ Nginx启动成功 (PID: $($process.Id))" "Green"
            Write-ColorOutput "📍 访问地址: http://localhost" "Cyan"
            return $true
        } else {
            Write-ColorOutput "❌ Nginx启动失败" "Red"
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ 启动Nginx时发生错误: $($_.Exception.Message)" "Red"
        return $false
    }
    finally {
        Pop-Location
    }
}

# 停止Nginx
function Stop-Nginx {
    Write-ColorOutput "🛑 停止Nginx服务..." "Yellow"
    
    $processes = Get-NginxProcess
    if (-not $processes) {
        Write-ColorOutput "ℹ️  Nginx未运行" "Gray"
        return $true
    }
    
    try {
        # 优雅停止
        if (Test-NginxInstallation) {
            Push-Location $NginxPath
            $nginxExe = Join-Path $NginxPath "nginx.exe"
            Start-Process -FilePath $nginxExe -ArgumentList "-s", "quit" -Wait -WindowStyle Hidden
            Pop-Location
        } else {
            # 强制停止
            $processes | Stop-Process -Force
        }
        
        # 等待停止
        Start-Sleep -Seconds 2
        
        # 验证停止
        $remainingProcesses = Get-NginxProcess
        if (-not $remainingProcesses) {
            Write-ColorOutput "✅ Nginx已停止" "Green"
            return $true
        } else {
            Write-ColorOutput "⚠️  部分Nginx进程仍在运行" "Yellow"
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ 停止Nginx时发生错误: $($_.Exception.Message)" "Red"
        return $false
    }
}

# 重启Nginx
function Restart-Nginx {
    Write-ColorOutput "🔄 重启Nginx服务..." "Cyan"
    
    if (Stop-Nginx) {
        Start-Sleep -Seconds 1
        return Start-Nginx
    }
    return $false
}

# 检查Nginx状态
function Get-NginxStatus {
    Write-ColorOutput "📊 Nginx服务状态" "Cyan"
    Write-ColorOutput "===================" "Cyan"
    
    # 检查进程
    $processes = Get-NginxProcess
    if ($processes) {
        Write-ColorOutput "✅ 状态: 运行中" "Green"
        foreach ($proc in $processes) {
            Write-ColorOutput "   PID: $($proc.Id), 内存: $([math]::Round($proc.WorkingSet/1MB, 2))MB" "Gray"
        }
    } else {
        Write-ColorOutput "❌ 状态: 未运行" "Red"
    }
    
    # 检查配置文件
    if (Test-Path $FullConfigPath) {
        Write-ColorOutput "✅ 配置文件: $FullConfigPath" "Green"
    } else {
        Write-ColorOutput "❌ 配置文件: 不存在" "Red"
    }
    
    # 检查Nginx安装
    if (Test-NginxInstallation) {
        Write-ColorOutput "✅ Nginx路径: $NginxPath" "Green"
    } else {
        Write-ColorOutput "❌ Nginx路径: 未找到" "Red"
    }
    
    # 测试端口
    try {
        $response = Invoke-WebRequest -Uri "http://localhost" -TimeoutSec 5 -ErrorAction Stop
        Write-ColorOutput "✅ HTTP测试: 响应正常 ($($response.StatusCode))" "Green"
    }
    catch {
        Write-ColorOutput "❌ HTTP测试: 连接失败" "Red"
    }
}

# 测试配置文件
function Test-NginxConfig {
    Write-ColorOutput "🔍 测试Nginx配置..." "Cyan"
    
    if (-not (Test-Path $FullConfigPath)) {
        Write-ColorOutput "❌ 配置文件不存在: $FullConfigPath" "Red"
        return $false
    }
    
    if (-not (Test-NginxInstallation)) {
        Write-ColorOutput "❌ Nginx未安装，无法测试配置" "Red"
        return $false
    }
    
    try {
        Push-Location $NginxPath
        $nginxExe = Join-Path $NginxPath "nginx.exe"
        $result = & $nginxExe -t -c $FullConfigPath 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ 配置文件语法正确" "Green"
            return $true
        } else {
            Write-ColorOutput "❌ 配置文件语法错误:" "Red"
            Write-ColorOutput $result "Red"
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ 测试配置时发生错误: $($_.Exception.Message)" "Red"
        return $false
    }
    finally {
        Pop-Location
    }
}

# 主逻辑
Write-ColorOutput "🌐 Nginx服务管理脚本" "Cyan"
Write-ColorOutput "项目: 加密货币监控系统" "Gray"
Write-ColorOutput "配置: $FullConfigPath" "Gray"
Write-ColorOutput "" "White"

switch ($Action.ToLower()) {
    "start" {
        Start-Nginx
    }
    "stop" {
        Stop-Nginx
    }
    "restart" {
        Restart-Nginx
    }
    "status" {
        Get-NginxStatus
    }
    "test" {
        Test-NginxConfig
    }
    default {
        Write-ColorOutput "用法: .\start_nginx.ps1 [-Action start|stop|restart|status|test] [-NginxPath C:\nginx] [-ConfigPath nginx.conf]" "Yellow"
        Write-ColorOutput "" "White"
        Write-ColorOutput "操作说明:" "Cyan"
        Write-ColorOutput "  start   - 启动Nginx服务" "White"
        Write-ColorOutput "  stop    - 停止Nginx服务" "White"
        Write-ColorOutput "  restart - 重启Nginx服务" "White"
        Write-ColorOutput "  status  - 查看服务状态" "White"
        Write-ColorOutput "  test    - 测试配置文件" "White"
    }
}