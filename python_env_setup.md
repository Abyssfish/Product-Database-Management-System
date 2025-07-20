# Python环境配置指南

## 1. 创建虚拟环境
在项目根目录打开终端，执行以下命令创建虚拟环境：
```powershell
python -m venv venv
```

## 2. 激活虚拟环境
### Windows系统
```powershell
# 使用Command Prompt
venv\Scripts\activate.bat

# 使用PowerShell
venv\Scripts\Activate.ps1
```
激活成功后，终端提示符前会显示 `(venv)`

## 3. 安装依赖
在激活的虚拟环境中执行：
```powershell
pip install -r requirements.txt
```

## 4. 退出虚拟环境
```powershell
deactivate
```

## 5. 常见问题
- **虚拟环境创建失败**：确保Python已添加到系统PATH，或使用完整路径如 `C:\Python310\python.exe -m venv venv`
- **PowerShell执行权限问题**：以管理员身份运行PowerShell，执行 `Set-ExecutionPolicy RemoteSigned` 并选择 Y
- **依赖安装缓慢**：可使用国内镜像源 `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`