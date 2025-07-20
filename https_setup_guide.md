# HTTPS配置指南

## 为什么需要HTTPS
现代浏览器要求在访问摄像头、麦克风等敏感设备时必须使用HTTPS协议，特别是在移动设备上。这是出于安全考虑的强制要求。

## 配置步骤

### 1. 安装OpenSSL
Windows用户需要先安装OpenSSL工具来生成SSL证书：
1. 访问 [https://slproweb.com/products/Win32OpenSSL.html](https://slproweb.com/products/Win32OpenSSL.html) 下载适合您系统的OpenSSL安装包
2. 安装时选择将OpenSSL添加到系统PATH

### 2. 生成自签名SSL证书
1. 打开命令提示符(CMD)或PowerShell
2. 导航到项目根目录：
   ```
   cd d:\Catalogue\项目\web_rider_byci_car
   ```
3. 运行以下命令生成证书：
   ```
   openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
   ```
4. 按照提示填写证书信息（可以全部留空）

执行成功后，项目根目录将生成两个文件：`cert.pem`(证书)和`key.pem`(私钥)

### 3. 修改Flask应用配置
编辑<mcfile name="app.py" path="d:\Catalogue\项目\web_rider_byci_car\app.py"></mcfile>文件，修改启动部分：

```python
if __name__ == '__main__':
    # 启用HTTPS
    app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'), debug=True)
```

### 4. 启动HTTPS服务器
在命令行中执行：
```
python app.py
```

### 5. 信任自签名证书（重要）
首次访问时，浏览器会显示安全警告：
1. Chrome/Edge浏览器：点击"高级" -> "继续访问"
2. Firefox浏览器：点击"高级" -> "添加例外" -> "确认安全例外"
3. 安卓设备：可能需要在系统设置中手动安装证书

## 访问地址
配置HTTPS后，应用访问地址变为：
`https://您的IP地址:5000`

## 注意事项
- 自签名证书仅用于开发测试，生产环境需要购买正规SSL证书
- 每次重启服务器后，可能需要重新信任证书
- 如果更换网络，局域网IP可能会变化，需要重新查看IP（使用`ipconfig`命令）