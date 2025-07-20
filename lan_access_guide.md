# 局域网访问配置指南

## 1. 确保Flask服务正确配置
已在<mcfile name="app.py" path="d:\Catalogue\项目\web_rider_byci_car\app.py"></mcfile>中设置：
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```
`host='0.0.0.0'` 确保服务监听所有网络接口，支持局域网访问。

## 2. 获取主机局域网IP地址
### Windows系统
1. 打开命令提示符(Win+R → 输入`cmd` → 回车)
2. 执行命令：
   ```powershell
   ipconfig
   ```
3. 在输出结果中找到 **无线局域网适配器 WLAN** 或 **以太网适配器 以太网** 下的 **IPv4 地址**，例如：
   ```
   IPv4 地址. . . . . . . . . . . . : 192.168.1.100
   ```
   记录此IP地址（如`192.168.1.100`）

## 3. 局域网设备访问方法
在同一网络中的其他设备浏览器中输入：
```
http://[主机IP]:5000
```
例如：`http://192.168.1.100:5000`

## 4. 防火墙设置（如访问失败）
### 允许端口通过防火墙
1. 打开 **控制面板 → 系统和安全 → Windows Defender 防火墙 → 高级设置**
2. 选择 **入站规则 → 新建规则**
3. 规则类型选择 **端口** → 下一步
4. 选择 **TCP**，特定本地端口填写 `5000` → 下一步
5. 选择 **允许连接** → 下一步
6. 勾选所有网络类型（域/专用/公用）→ 下一步
7. 名称填写 `Flask-5000` → 完成

### 临时关闭防火墙测试（谨慎操作）
```powershell
# 仅测试用，测试后建议重新开启
netsh advfirewall set allprofiles state off
```

## 5. 常见问题排查
- **IP地址变化**：路由器重启可能导致IP变化，建议在路由器中为电脑设置静态IP
- **端口冲突**：若5000端口被占用，修改<mcfile name="app.py" path="d:\Catalogue\项目\web_rider_byci_car\app.py"></mcfile>中的`port`参数（如改为5001）
- **手机无法访问**：确保手机和电脑连接同一WiFi，关闭手机VPN