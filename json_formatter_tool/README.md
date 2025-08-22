# 使用 FastAPI 构建 JSON 格式化工具

下面我将为你创建一个基于 FastAPI 的 Web 应用，它可以格式化、验证和美化 JSON 数据。

## 项目结构

```
json_formatter_tool/
├── main.py              # FastAPI 主应用
├── static/              # 静态文件目录
│   ├── style.css        # 样式文件
│   └── script.js        # 前端JavaScript
├── templates/           # 模板目录
│   └── index.html       # 前端页面
└── requirements.txt     # 依赖文件
```

## 安装依赖

首先创建 `requirements.txt` 文件：

```txt
fastapi==0.104.1
uvicorn==0.24.0
jinja2==3.1.2
```

安装依赖：
```bash
pip install -r requirements.txt
```

## 实现代码

### 1. 主应用文件 (main.py)

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
from typing import Any, Dict

app = FastAPI(title="JSON 格式化工具", description="格式化、验证和美化 JSON 数据")

# 挂载静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def format_json(json_data: Any, indent: int = 2) -> str:
    """格式化 JSON 数据"""
    return json.dumps(json_data, indent=indent, ensure_ascii=False)

def minify_json(json_data: Any) -> str:
    """压缩 JSON 数据"""
    return json.dumps(json_data, separators=(',', ':'), ensure_ascii=False)

def validate_json(json_str: str) -> Dict[str, Any]:
    """验证 JSON 字符串是否有效"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"无效的 JSON: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """显示主页面"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/format")
async def format_json_endpoint(request: Request):
    """格式化 JSON 数据"""
    try:
        data = await request.json()
        json_input = data.get("json_input", "")
        indent = data.get("indent", 2)
        
        # 验证并解析 JSON
        parsed_json = validate_json(json_input)
        
        # 格式化 JSON
        formatted_json = format_json(parsed_json, indent)
        
        return JSONResponse({
            "success": True,
            "formatted_json": formatted_json,
            "message": "JSON 格式化成功"
        })
    except HTTPException as e:
        return JSONResponse({
            "success": False,
            "error": e.detail
        }, status_code=e.status_code)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"处理 JSON 时发生错误: {str(e)}"
        }, status_code=500)

@app.post("/minify")
async def minify_json_endpoint(request: Request):
    """压缩 JSON 数据"""
    try:
        data = await request.json()
        json_input = data.get("json_input", "")
        
        # 验证并解析 JSON
        parsed_json = validate_json(json_input)
        
        # 压缩 JSON
        minified_json = minify_json(parsed_json)
        
        return JSONResponse({
            "success": True,
            "minified_json": minified_json,
            "message": "JSON 压缩成功"
        })
    except HTTPException as e:
        return JSONResponse({
            "success": False,
            "error": e.detail
        }, status_code=e.status_code)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"处理 JSON 时发生错误: {str(e)}"
        }, status_code=500)

@app.post("/validate")
async def validate_json_endpoint(request: Request):
    """验证 JSON 数据"""
    try:
        data = await request.json()
        json_input = data.get("json_input", "")
        
        # 验证 JSON
        validate_json(json_input)
        
        return JSONResponse({
            "success": True,
            "message": "JSON 格式有效"
        })
    except HTTPException as e:
        return JSONResponse({
            "success": False,
            "error": e.detail
        }, status_code=e.status_code)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"验证 JSON 时发生错误: {str(e)}"
        }, status_code=500)

@app.post("/convert")
async def convert_json_endpoint(request: Request):
    """转换 JSON 数据类型"""
    try:
        data = await request.json()
        json_input = data.get("json_input", "")
        conversion_type = data.get("conversion_type", "python")
        
        # 验证并解析 JSON
        parsed_json = validate_json(json_input)
        
        if conversion_type == "python":
            # 转换为 Python 字典表示
            converted = str(parsed_json)
        elif conversion_type == "xml":
            # 简单转换为 XML（实际应用中可能需要更复杂的转换）
            converted = json_to_xml(parsed_json)
        else:
            raise HTTPException(status_code=400, detail="不支持的转换类型")
        
        return JSONResponse({
            "success": True,
            "converted": converted,
            "message": f"JSON 已转换为 {conversion_type.upper()}"
        })
    except HTTPException as e:
        return JSONResponse({
            "success": False,
            "error": e.detail
        }, status_code=e.status_code)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"转换 JSON 时发生错误: {str(e)}"
        }, status_code=500)

def json_to_xml(data, parent_tag="root"):
    """将 JSON 转换为简单的 XML 格式"""
    if isinstance(data, dict):
        xml = f"<{parent_tag}>"
        for key, value in data.items():
            xml += json_to_xml(value, key)
        xml += f"</{parent_tag}>"
        return xml
    elif isinstance(data, list):
        xml = ""
        for item in data:
            xml += json_to_xml(item, "item")
        return xml
    else:
        return f"<{parent_tag}>{data}</{parent_tag}>"

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
    <title>JSON 格式化工具</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>JSON 格式化工具</h1>
            <p>格式化、验证和转换 JSON 数据</p>
        </header>
        
        <div class="main-content">
            <div class="input-section">
                <h2>输入 JSON</h2>
                <textarea id="jsonInput" placeholder='粘贴您的 JSON 数据，例如: {"name": "John", "age": 30, "city": "New York"}'></textarea>
                
                <div class="controls">
                    <label for="indent">缩进:</label>
                    <select id="indent">
                        <option value="2">2 空格</option>
                        <option value="4">4 空格</option>
                        <option value="tab">制表符</option>
                    </select>
                    
                    <button id="formatBtn">格式化</button>
                    <button id="minifyBtn">压缩</button>
                    <button id="validateBtn">验证</button>
                    
                    <label for="conversionType">转换为:</label>
                    <select id="conversionType">
                        <option value="python">Python 字典</option>
                        <option value="xml">XML</option>
                    </select>
                    <button id="convertBtn">转换</button>
                    
                    <button id="clearBtn">清空</button>
                </div>
            </div>
            
            <div class="output-section">
                <h2>结果</h2>
                <div id="output" class="output-area"></div>
                <div id="error" class="error hidden"></div>
            </div>
        </div>
    </div>
    
    <script src="/static/script.js"></script>
</body>
</html>
```

### 3. 样式文件 (static/style.css)

```css
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    background-color: #f5f7f9;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

h1 {
    color: #2c3e50;
    margin-bottom: 10px;
}

.main-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.input-section, .output-section {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

h2 {
    color: #3498db;
    margin-top: 0;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
}

textarea {
    width: 100%;
    height: 300px;
    padding: 15px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 14px;
    resize: vertical;
    box-sizing: border-box;
}

.controls {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 15px;
    align-items: center;
}

button {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px 15px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: background-color 0.2s;
}

button:hover {
    background-color: #2980b9;
}

#clearBtn {
    background-color: #e74c3c;
}

#clearBtn:hover {
    background-color: #c0392b;
}

label {
    font-weight: bold;
    margin-right: 5px;
}

select {
    padding: 6px 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.output-area {
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 4px;
    padding: 15px;
    min-height: 300px;
    font-family: 'Consolas', 'Monaco', monospace;
    white-space: pre-wrap;
    overflow: auto;
}

.error {
    color: #e74c3c;
    background-color: #fadbd8;
    padding: 10px;
    border-radius: 4px;
    margin-top: 15px;
}

.hidden {
    display: none;
}

.success {
    color: #27ae60;
    margin-top: 10px;
    font-weight: bold;
}

@media (max-width: 768px) {
    .main-content {
        grid-template-columns: 1fr;
    }
}
```

### 4. JavaScript 文件 (static/script.js)

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const jsonInput = document.getElementById('jsonInput');
    const output = document.getElementById('output');
    const errorDiv = document.getElementById('error');
    const formatBtn = document.getElementById('formatBtn');
    const minifyBtn = document.getElementById('minifyBtn');
    const validateBtn = document.getElementById('validateBtn');
    const convertBtn = document.getElementById('convertBtn');
    const clearBtn = document.getElementById('clearBtn');
    const indentSelect = document.getElementById('indent');
    const conversionTypeSelect = document.getElementById('conversionType');
    
    // 格式化按钮点击事件
    formatBtn.addEventListener('click', async function() {
        const jsonText = jsonInput.value.trim();
        if (!jsonText) {
            showError('请输入 JSON 数据');
            return;
        }
        
        try {
            const indentValue = indentSelect.value === 'tab' ? '\t' : parseInt(indentSelect.value);
            const response = await fetch('/format', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    json_input: jsonText,
                    indent: indentValue
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showOutput(data.formatted_json, '格式化成功');
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('请求失败: ' + error.message);
        }
    });
    
    // 压缩按钮点击事件
    minifyBtn.addEventListener('click', async function() {
        const jsonText = jsonInput.value.trim();
        if (!jsonText) {
            showError('请输入 JSON 数据');
            return;
        }
        
        try {
            const response = await fetch('/minify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    json_input: jsonText
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showOutput(data.minified_json, '压缩成功');
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('请求失败: ' + error.message);
        }
    });
    
    // 验证按钮点击事件
    validateBtn.addEventListener('click', async function() {
        const jsonText = jsonInput.value.trim();
        if (!jsonText) {
            showError('请输入 JSON 数据');
            return;
        }
        
        try {
            const response = await fetch('/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    json_input: jsonText
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showOutput(jsonText, data.message);
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('请求失败: ' + error.message);
        }
    });
    
    // 转换按钮点击事件
    convertBtn.addEventListener('click', async function() {
        const jsonText = jsonInput.value.trim();
        if (!jsonText) {
            showError('请输入 JSON 数据');
            return;
        }
        
        try {
            const response = await fetch('/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    json_input: jsonText,
                    conversion_type: conversionTypeSelect.value
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showOutput(data.converted, data.message);
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('请求失败: ' + error.message);
        }
    });
    
    // 清空按钮点击事件
    clearBtn.addEventListener('click', function() {
        jsonInput.value = '';
        output.textContent = '';
        hideError();
    });
    
    // 显示输出
    function showOutput(content, message) {
        output.textContent = content;
        hideError();
        
        // 显示成功消息
        const successMsg = document.createElement('div');
        successMsg.className = 'success';
        successMsg.textContent = message;
        output.parentNode.insertBefore(successMsg, output.nextSibling);
        
        // 3秒后移除成功消息
        setTimeout(() => {
            if (successMsg.parentNode) {
                successMsg.parentNode.removeChild(successMsg);
            }
        }, 3000);
    }
    
    // 显示错误
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        output.textContent = '';
    }
    
    // 隐藏错误
    function hideError() {
        errorDiv.classList.add('hidden');
    }
    
    // 示例 JSON
    const exampleJson = `{
  "name": "JSON 格式化工具",
  "version": "1.0.0",
  "description": "一个用于格式化、验证和转换 JSON 数据的工具",
  "features": [
    "格式化",
    "压缩",
    "验证",
    "转换为其他格式"
  ],
  "author": {
    "name": "开发者",
    "email": "developer@example.com"
  }
}`;
    
    // 设置示例 JSON
    jsonInput.value = exampleJson;
});
```

## 运行应用

使用以下命令启动应用：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000 即可使用工具。

## 功能说明

1. **JSON 格式化**：美化 JSON 数据，支持不同的缩进选项
2. **JSON 压缩**：移除所有不必要的空格和换行符，减小 JSON 大小
3. **JSON 验证**：检查 JSON 数据是否有效，并提供错误信息
4. **格式转换**：将 JSON 转换为其他格式（Python 字典、XML 等）
5. **清空功能**：一键清除输入和输出内容

## 使用示例

1. 在输入框中粘贴或输入 JSON 数据
2. 选择需要的操作：
   - 点击"格式化"按钮美化 JSON
   - 点击"压缩"按钮减小 JSON 大小
   - 点击"验证"按钮检查 JSON 有效性
   - 选择转换类型后点击"转换"按钮转换为其他格式
3. 查看右侧的输出区域获取结果

这个工具对于开发人员、API 测试人员和任何需要处理 JSON 数据的用户都非常有用。你可以根据需要进一步扩展功能，比如添加 JSON 路径查询、差异比较、批量处理等功能。