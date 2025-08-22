# 使用 FastAPI 构建 cURL 解析与 API 调用工具

下面我将为你创建一个基于 FastAPI 的 Web 应用，它可以解析 cURL 命令并调用相应的 API 接口。

## 项目结构

```
curl_parser_tool/
├── main.py              # FastAPI 主应用
├── static/              # 静态文件目录
│   └── style.css        # 样式文件
├── templates/           # 模板目录
│   └── index.html       # 前端页面
└── requirements.txt     # 依赖文件
```

## 安装依赖

首先创建 `requirements.txt` 文件：

```txt
fastapi==0.104.1
uvicorn==0.24.0
requests==2.31.0
jinja2==3.1.2
python-multipart==0.0.6
```

安装依赖：
```bash
pip install -r requirements.txt
```

## 实现代码

### 1. 主应用文件 (main.py)

```python
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import re
import shlex
import requests
from urllib.parse import urlparse
import json
from typing import Dict, Any, List, Optional

app = FastAPI(title="cURL 解析工具", description="解析 cURL 命令并调用 API 接口")

# 挂载静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def parse_curl(curl_command: str) -> Dict[str, Any]:
    """解析 cURL 命令，提取请求方法、URL、头部和数据"""
    
    # 初始化解析结果
    parsed = {
        'method': 'GET',
        'url': '',
        'headers': {},
        'data': None,
        'json': None,
        'auth': None,
        'verify_ssl': True
    }
    
    # 移除换行符和多余空格
    curl_command = ' '.join(curl_command.split())
    
    # 使用 shlex 分割命令行参数，正确处理引号
    try:
        tokens = shlex.split(curl_command)
    except:
        # 如果解析失败，尝试简单分割
        tokens = curl_command.split()
    
    # 确保第一个 token 是 curl
    if not tokens or tokens[0] != 'curl':
        raise ValueError("不是有效的 cURL 命令")
    
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token == '-X' or token == '--request':
            i += 1
            parsed['method'] = tokens[i].upper()
        elif token == '-H' or token == '--header':
            i += 1
            header = tokens[i]
            if ':' in header:
                key, value = header.split(':', 1)
                parsed['headers'][key.strip()] = value.strip()
        elif token == '-d' or token == '--data' or token == '--data-raw':
            i += 1
            data_str = tokens[i]
            # 尝试解析为 JSON
            try:
                parsed['json'] = json.loads(data_str)
            except json.JSONDecodeError:
                parsed['data'] = data_str
        elif token == '-u' or token == '--user':
            i += 1
            auth_parts = tokens[i].split(':', 1)
            if len(auth_parts) == 2:
                parsed['auth'] = (auth_parts[0], auth_parts[1])
        elif token == '--url':
            i += 1
            parsed['url'] = tokens[i]
        elif token == '-k' or token == '--insecure':
            parsed['verify_ssl'] = False
        elif token.startswith('http://') or token.startswith('https://'):
            parsed['url'] = token
        i += 1
    
    return parsed

def make_request(parsed_curl: Dict[str, Any]) -> Dict[str, Any]:
    """根据解析结果发起请求"""
    try:
        # 准备请求参数
        request_kwargs = {
            'method': parsed_curl['method'],
            'url': parsed_curl['url'],
            'headers': parsed_curl['headers'],
            'verify': parsed_curl['verify_ssl']
        }
        
        # 添加认证信息
        if parsed_curl['auth']:
            request_kwargs['auth'] = parsed_curl['auth']
        
        # 添加数据或JSON
        if parsed_curl['data']:
            request_kwargs['data'] = parsed_curl['data']
        elif parsed_curl['json']:
            request_kwargs['json'] = parsed_curl['json']
        
        # 发送请求
        response = requests.request(**request_kwargs)
        
        # 准备响应结果
        result = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.text,
            'elapsed': str(response.elapsed)
        }
        
        # 尝试解析JSON响应
        try:
            result['json'] = response.json()
        except:
            pass
            
        return result
    except Exception as e:
        return {'error': str(e)}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """显示主页面"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/parse-curl")
async def parse_curl_command(curl_command: str = Form(...)):
    """解析 cURL 命令并调用 API"""
    try:
        # 解析 cURL 命令
        parsed = parse_curl(curl_command)
        
        # 发起请求
        response = make_request(parsed)
        
        # 返回结果
        return JSONResponse({
            "success": True,
            "parsed": parsed,
            "response": response
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. 前端模板 (templates/index.html)

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>cURL 解析工具</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <h1>cURL 解析工具</h1>
        <p>粘贴您的 cURL 命令，工具将解析并执行该请求</p>
        
        <form id="curlForm">
            <div class="form-group">
                <label for="curlCommand">cURL 命令:</label>
                <textarea id="curlCommand" name="curl_command" rows="6" placeholder="例如: curl -X GET https://api.example.com/data -H 'Authorization: Bearer token'"></textarea>
            </div>
            <button type="submit">解析并执行</button>
        </form>
        
        <div id="results" class="hidden">
            <h2>解析结果</h2>
            <div class="result-section">
                <h3>请求详情</h3>
                <pre id="parsedDetails"></pre>
            </div>
            
            <div class="result-section">
                <h3>响应结果</h3>
                <div class="response-info">
                    <p>状态码: <span id="statusCode"></span></p>
                    <p>耗时: <span id="elapsedTime"></span></p>
                </div>
                <pre id="responseContent"></pre>
            </div>
        </div>
        
        <div id="error" class="error hidden"></div>
    </div>
    
    <script>
        document.getElementById('curlForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const curlCommand = document.getElementById('curlCommand').value;
            const resultsDiv = document.getElementById('results');
            const errorDiv = document.getElementById('error');
            
            // 隐藏之前的结果和错误
            resultsDiv.classList.add('hidden');
            errorDiv.classList.add('hidden');
            
            try {
                const response = await fetch('/parse-curl', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams({
                        'curl_command': curlCommand
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // 显示解析结果
                    document.getElementById('parsedDetails').textContent = 
                        JSON.stringify(data.parsed, null, 2);
                    
                    // 显示响应结果
                    document.getElementById('statusCode').textContent = 
                        data.response.status_code || 'N/A';
                    document.getElementById('elapsedTime').textContent = 
                        data.response.elapsed || 'N/A';
                    
                    if (data.response.json) {
                        document.getElementById('responseContent').textContent = 
                            JSON.stringify(data.response.json, null, 2);
                    } else {
                        document.getElementById('responseContent').textContent = 
                            data.response.content || '无内容';
                    }
                    
                    resultsDiv.classList.remove('hidden');
                } else {
                    // 显示错误
                    errorDiv.textContent = '错误: ' + data.error;
                    errorDiv.classList.remove('hidden');
                }
            } catch (error) {
                errorDiv.textContent = '请求失败: ' + error.message;
                errorDiv.classList.remove('hidden');
            }
        });
    </script>
</body>
</html>
```

### 3. 样式文件 (static/style.css)

```css
body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
    color: #333;
}

.container {
    max-width: 900px;
    margin: 0 auto;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

h1 {
    color: #2c3e50;
    border-bottom: 2px solid #eee;
    padding-bottom: 10px;
}

.form-group {
    margin-bottom: 15px;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-family: monospace;
    resize: vertical;
}

button {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
}

button:hover {
    background-color: #2980b9;
}

.result-section {
    margin-top: 20px;
    padding: 15px;
    background-color: #f9f9f9;
    border-radius: 4px;
    border-left: 4px solid #3498db;
}

.response-info {
    display: flex;
    gap: 20px;
    margin-bottom: 10px;
}

pre {
    background-color: #f8f8f8;
    padding: 10px;
    border-radius: 4px;
    overflow: auto;
    white-space: pre-wrap;
}

.hidden {
    display: none;
}

.error {
    color: #e74c3c;
    background-color: #fadbd8;
    padding: 10px;
    border-radius: 4px;
    margin-top: 20px;
}
```

## 运行应用

使用以下命令启动应用：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000 即可使用工具。

## 功能说明

1. **cURL 解析**：支持解析常见的 cURL 选项，如：
   - `-X`/`--request`：请求方法
   - `-H`/`--header`：请求头
   - `-d`/`--data`/`--data-raw`：请求数据
   - `-u`/`--user`：基本认证
   - `-k`/`--insecure`：忽略 SSL 证书验证

2. **API 调用**：使用解析后的参数发送 HTTP 请求

3. **结果展示**：以友好格式显示请求详情和响应结果

## 使用示例

在文本框中输入 cURL 命令，例如：
```
curl -X POST https://jsonplaceholder.typicode.com/posts \
  -H "Content-Type: application/json" \
  -d '{"title": "test", "body": "test body", "userId": 1}'
```

点击"解析并执行"按钮，工具将显示解析后的请求详情和 API 响应结果。

这个工具对于调试 API 请求、学习和测试 cURL 命令非常有用。你可以根据需要进一步扩展功能，比如添加请求历史记录、保存常用请求等。