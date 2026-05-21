CDP 全称 Chrome DevTools Protocol（Chrome开发协议工具）

### 1.CDP启动

#### Windows 系统启动 CDP 端口
```bash
"chrome安装路径\chrome.exe" --remote-debugging-port=9222 --user-data-dir="用户数据路径"

"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="D:\temp\chrome_data"
```

#### macOS 系统启动 CDP 端口
```

```

#### Linux 系统启动 CDP 端口
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="用户数据路径"
```

启动成功后，浏览器会自动打开，访问``` http://127.0.0.1:9222/json/version ```，就会看到如下``` JSON ```数据返回
```json
{
    "Browser": "Chrome/148.0.7778.168",
    "Protocol-Version": "1.3",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "V8-Version": "14.8.178.21",
    "WebKit-Version": "537.36 (@58ae0c621a34b558c60db5c6209d9dd9063084b7)",
    "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/browser/49d0c25c-8060-42fb-ad7b-f5e26d97286f"
}
```
``` webSocketDebuggerUrl ```就是你需要的 CDP 连接地址

#### 当你想要查看打开了哪些标签页，可以访问 ``` http://127.0.0.1:9222/json/list ```
```json
[
    {
        "description": "",
        "devtoolsFrontendUrl": "https://chrome-devtools-frontend.appspot.com/serve_rev/@58ae0c621a34b558c60db5c6209d9dd9063084b7/inspector.html?ws=127.0.0.1:9222/devtools/page/AB3C3FCA22AF28AAC6ED5B6D9CBF63D2",
        "id": "AB3C3FCA22AF28AAC6ED5B6D9CBF63D2",
        "title": "新标签页",
        "type": "page",
        "url": "chrome://newtab/",
        "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/AB3C3FCA22AF28AAC6ED5B6D9CBF63D2"
    },
    {
        "description": "",
        "devtoolsFrontendUrl": "https://chrome-devtools-frontend.appspot.com/serve_rev/@58ae0c621a34b558c60db5c6209d9dd9063084b7/inspector.html?ws=127.0.0.1:9222/devtools/page/4BE8A8383B49565C043B6A8BC757B1CD",
        "id": "4BE8A8383B49565C043B6A8BC757B1CD",
        "parentId": "AB3C3FCA22AF28AAC6ED5B6D9CBF63D2",
        "title": "chrome-untrusted://new-tab-page/one-google-bar?paramsencoded=",
        "type": "iframe",
        "url": "chrome-untrusted://new-tab-page/one-google-bar?paramsencoded=",
        "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/4BE8A8383B49565C043B6A8BC757B1CD"
    }
]
```

### 2.使用 CDP 协议操控浏览器

* 在 `Postman` 新建一个 ```WebSocket Request```
* 在 url 栏粘贴 `webSocketDebuggerUrl`
* 点击 `Connect`
接下来就可以执行相应的方法调用了（`jsonrpc`）

#### 1. 控制页面跳转（Page.navigate）
在 Postman 的 Message 发送框输入：
```json
{
    "id": 1,
    "method": "Page.navigate",
    "params": {
        "url": "https://www.bilibili.com"
    }
}
```

#### 2. 执行 JavaScript（Runtime.evaluate）
```json
{
    "id": 2,
    "method": "Runtime.evaluate",
    "params": {
        "expression": "alert('controled by Postman')"
    }
}
```

#### 获取当前页面的 `Title` 
```json
{
    "id": 3,
    "method": "Runtime.evaluate",
    "params": {
        "expression": "document.title",
        "returnByValue": true
    }
}
```

#### 3. 截图（Page.captureScreenshot）
```json
{
    "id": 4,
    "method": "Page.captureScreenshot",
    "params": {
        "format": "png"
    }
}
```

#### 4.修改定位（虚拟地理位置）
```
{
    "id": 30,
    "method": "Emulation.setGeolocationOverride",
    "params": {
        "latitude": -80.0000,
        "longitude": 0.0000,
        "accuracy": 1
    }
}
```



