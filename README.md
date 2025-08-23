# FastAPI 接口自动化测试工具

下面是一个基于 FastAPI 的完整实用的 Web 网页端接口自动化测试工具实现。这个工具支持创建、管理和执行 API 测试用例，并生成测试报告。

## 项目结构
```
api-test-tool/
├── main.py
├── models.py
├── test_runner.py
├── templates/
│   └── index.html
├── static/
│   └── style.css
└── requirements.txt
```

## 安装依赖

创建 `requirements.txt` 文件：
```txt
fastapi==0.104.1
uvicorn==0.24.0
jinja2==3.1.2
aiohttp==3.8.6
pydantic==2.5.0
python-multipart==0.0.6
```

安装依赖：
```bash
pip install -r requirements.txt
```

## 实现代码

### 1. 数据模型 (models.py)
```python
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from enum import Enum

class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

class TestCase(BaseModel):
    name: str
    url: str
    method: HTTPMethod = HTTPMethod.GET
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    body: Optional[Any] = None
    expected_status: int = 200
    expected_response: Optional[Dict[str, Any]] = None
    timeout: int = 10

class TestSuite(BaseModel):
    name: str
    test_cases: List[TestCase]
    variables: Optional[Dict[str, Any]] = None

class TestResult(BaseModel):
    test_case: TestCase
    success: bool
    response_status: int
    response_data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float

class TestReport(BaseModel):
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    results: List[TestResult]
    execution_time: float
```

### 2. 测试执行器 (test_runner.py)
```python
import asyncio
import aiohttp
import json
from datetime import datetime
from models import TestCase, TestResult, TestSuite, TestReport

class TestRunner:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def execute_test_case(self, test_case: TestCase) -> TestResult:
        start_time = datetime.now()
        try:
            async with self.session.request(
                method=test_case.method,
                url=test_case.url,
                headers=test_case.headers,
                params=test_case.params,
                json=test_case.body,
                timeout=test_case.timeout
            ) as response:
                response_status = response.status
                response_data = await response.json() if response.headers.get('content-type') == 'application/json' else await response.text()
                
                success = response_status == test_case.expected_status
                if test_case.expected_response:
                    success = success and self._check_expected_response(response_data, test_case.expected_response)
                
                error = None if success else f"Expected status {test_case.expected_status}, got {response_status}"
                
        except Exception as e:
            response_status = 0
            response_data = None
            success = False
            error = str(e)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        return TestResult(
            test_case=test_case,
            success=success,
            response_status=response_status,
            response_data=response_data,
            error=error,
            execution_time=execution_time
        )
    
    def _check_expected_response(self, actual_response, expected_response):
        # 简单的响应检查，可以根据需要扩展
        if isinstance(expected_response, dict):
            for key, value in expected_response.items():
                if key not in actual_response or actual_response[key] != value:
                    return False
        return True
    
    async def execute_test_suite(self, test_suite: TestSuite) -> TestReport:
        start_time = datetime.now()
        
        async with self:
            results = []
            for test_case in test_suite.test_cases:
                result = await self.execute_test_case(test_case)
                results.append(result)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        passed_tests = sum(1 for result in results if result.success)
        failed_tests = len(results) - passed_tests
        
        return TestReport(
            suite_name=test_suite.name,
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            results=results,
            execution_time=execution_time
        )
```

### 3. 主应用 (main.py)
```python
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Optional
import json
import uuid

from models import TestCase, TestSuite, TestReport
from test_runner import TestRunner

app = FastAPI(title="API自动化测试工具", version="1.0.0")

# 设置模板和静态文件
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 内存存储测试套件（生产环境应使用数据库）
test_suites = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/test-suites")
async def get_test_suites():
    return {"suites": list(test_suites.values())}

@app.post("/test-suites")
async def create_test_suite(suite: TestSuite):
    suite_id = str(uuid.uuid4())
    test_suites[suite_id] = {"id": suite_id, **suite.dict()}
    return {"id": suite_id, "message": "Test suite created successfully"}

@app.get("/test-suites/{suite_id}")
async def get_test_suite(suite_id: str):
    if suite_id not in test_suites:
        raise HTTPException(status_code=404, detail="Test suite not found")
    return test_suites[suite_id]

@app.delete("/test-suites/{suite_id}")
async def delete_test_suite(suite_id: str):
    if suite_id not in test_suites:
        raise HTTPException(status_code=404, detail="Test suite not found")
    del test_suites[suite_id]
    return {"message": "Test suite deleted successfully"}

@app.post("/run-test/{suite_id}")
async def run_test_suite(suite_id: str):
    if suite_id not in test_suites:
        raise HTTPException(status_code=404, detail="Test suite not found")
    
    suite_data = test_suites[suite_id]
    test_suite = TestSuite(**{k: v for k, v in suite_data.items() if k != 'id'})
    
    runner = TestRunner()
    report = await runner.execute_test_suite(test_suite)
    
    return report.dict()

@app.post("/run-single-test")
async def run_single_test(test_case: TestCase):
    runner = TestRunner()
    async with runner:
        result = await runner.execute_test_case(test_case)
    return result.dict()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 4. 前端模板 (templates/index.html)
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API自动化测试工具</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <h1>API自动化测试工具</h1>
        
        <div class="tabs">
            <button class="tab-link active" onclick="openTab('single-test')">单接口测试</button>
            <button class="tab-link" onclick="openTab('test-suite')">测试套件</button>
            <button class="tab-link" onclick="openTab('test-results')">测试结果</button>
        </div>
        
        <div id="single-test" class="tab-content active">
            <h2>单接口测试</h2>
            <form id="single-test-form">
                <div class="form-group">
                    <label for="name">测试名称:</label>
                    <input type="text" id="name" name="name" required>
                </div>
                
                <div class="form-group">
                    <label for="url">请求URL:</label>
                    <input type="url" id="url" name="url" required>
                </div>
                
                <div class="form-group">
                    <label for="method">HTTP方法:</label>
                    <select id="method" name="method">
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                        <option value="DELETE">DELETE</option>
                        <option value="PATCH">PATCH</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="headers">请求头 (JSON):</label>
                    <textarea id="headers" name="headers" rows="3" placeholder='{"Content-Type": "application/json"}'></textarea>
                </div>
                
                <div class="form-group">
                    <label for="params">查询参数 (JSON):</label>
                    <textarea id="params" name="params" rows="3" placeholder='{"key": "value"}'></textarea>
                </div>
                
                <div class="form-group">
                    <label for="body">请求体 (JSON):</label>
                    <textarea id="body" name="body" rows="5" placeholder='{"key": "value"}'></textarea>
                </div>
                
                <div class="form-group">
                    <label for="expected_status">期望状态码:</label>
                    <input type="number" id="expected_status" name="expected_status" value="200">
                </div>
                
                <button type="button" onclick="runSingleTest()">运行测试</button>
            </form>
            
            <div id="single-test-result" class="result-container"></div>
        </div>
        
        <div id="test-suite" class="tab-content">
            <h2>测试套件管理</h2>
            <button onclick="showCreateSuiteForm()">创建新测试套件</button>
            
            <div id="create-suite-form" class="form-container" style="display: none;">
                <h3>创建测试套件</h3>
                <form id="suite-form">
                    <div class="form-group">
                        <label for="suite-name">套件名称:</label>
                        <input type="text" id="suite-name" name="name" required>
                    </div>
                    
                    <div id="suite-test-cases">
                        <h4>测试用例</h4>
                        <div class="test-case" id="test-case-0">
                            <h5>测试用例 #1</h5>
                            <div class="form-group">
                                <label>名称:</label>
                                <input type="text" name="test_cases-0-name" required>
                            </div>
                            <div class="form-group">
                                <label>URL:</label>
                                <input type="url" name="test_cases-0-url" required>
                            </div>
                            <div class="form-group">
                                <label>方法:</label>
                                <select name="test_cases-0-method">
                                    <option value="GET">GET</option>
                                    <option value="POST">POST</option>
                                    <option value="PUT">PUT</option>
                                    <option value="DELETE">DELETE</option>
                                    <option value="PATCH">PATCH</option>
                                </select>
                            </div>
                            <button type="button" onclick="removeTestCase(0)">移除</button>
                        </div>
                    </div>
                    
                    <button type="button" onclick="addTestCase()">添加测试用例</button>
                    <button type="button" onclick="saveTestSuite()">保存测试套件</button>
                </form>
            </div>
            
            <div id="suite-list">
                <h3>测试套件列表</h3>
                <div id="suites-container"></div>
            </div>
        </div>
        
        <div id="test-results" class="tab-content">
            <h2>测试结果</h2>
            <div id="results-container"></div>
        </div>
    </div>

    <script src="/static/script.js"></script>
</body>
</html>
```

### 5. 静态文件 (static/style.css)
```css
body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    background-color: #f4f4f4;
}

.container {
    width: 90%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background: white;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

h1, h2, h3, h4, h5 {
    color: #333;
}

.tabs {
    margin-bottom: 20px;
}

.tab-link {
    padding: 10px 20px;
    background: #ddd;
    border: none;
    cursor: pointer;
    margin-right: 5px;
}

.tab-link.active {
    background: #4CAF50;
    color: white;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

.form-group {
    margin-bottom: 15px;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

input[type="text"],
input[type="url"],
input[type="number"],
select,
textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

button {
    padding: 10px 15px;
    background: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

button:hover {
    background: #45a049;
}

.result-container {
    margin-top: 20px;
    padding: 15px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background: #f9f9f9;
}

.test-case {
    border: 1px solid #ddd;
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 4px;
    background: #f9f9f9;
}

.success {
    color: green;
}

.failure {
    color: red;
}

.test-result {
    margin-bottom: 15px;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.test-result.success {
    background: #dff0d8;
    border-color: #d6e9c6;
}

.test-result.failure {
    background: #f2dede;
    border-color: #ebccd1;
}
```

### 6. 前端JavaScript (static/script.js)
```javascript
let testCaseCount = 1;

function openTab(tabName) {
    const tabContents = document.getElementsByClassName("tab-content");
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove("active");
    }
    
    const tabLinks = document.getElementsByClassName("tab-link");
    for (let i = 0; i < tabLinks.length; i++) {
        tabLinks[i].classList.remove("active");
    }
    
    document.getElementById(tabName).classList.add("active");
    event.currentTarget.classList.add("active");
    
    if (tabName === 'test-suite') {
        loadTestSuites();
    } else if (tabName === 'test-results') {
        // 可以加载历史测试结果
    }
}

async function runSingleTest() {
    const form = document.getElementById('single-test-form');
    const formData = new FormData(form);
    
    const testCase = {
        name: formData.get('name'),
        url: formData.get('url'),
        method: formData.get('method'),
        expected_status: parseInt(formData.get('expected_status')),
        headers: formData.get('headers') ? JSON.parse(formData.get('headers')) : {},
        params: formData.get('params') ? JSON.parse(formData.get('params')) : {},
        body: formData.get('body') ? JSON.parse(formData.get('body')) : null
    };
    
    try {
        const response = await fetch('/run-single-test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testCase)
        });
        
        const result = await response.json();
        displaySingleTestResult(result);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('single-test-result').innerHTML = `
            <div class="test-result failure">
                <h3>错误</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

function displaySingleTestResult(result) {
    const resultDiv = document.getElementById('single-test-result');
    const success = result.success;
    
    resultDiv.innerHTML = `
        <div class="test-result ${success ? 'success' : 'failure'}">
            <h3>${result.test_case.name} - ${success ? '通过' : '失败'}</h3>
            <p><strong>URL:</strong> ${result.test_case.url}</p>
            <p><strong>方法:</strong> ${result.test_case.method}</p>
            <p><strong>期望状态码:</strong> ${result.test_case.expected_status}</p>
            <p><strong>实际状态码:</strong> ${result.response_status}</p>
            <p><strong>执行时间:</strong> ${result.execution_time.toFixed(3)} 秒</p>
            ${result.error ? `<p><strong>错误信息:</strong> ${result.error}</p>` : ''}
            <p><strong>响应数据:</strong></p>
            <pre>${JSON.stringify(result.response_data, null, 2)}</pre>
        </div>
    `;
}

function showCreateSuiteForm() {
    document.getElementById('create-suite-form').style.display = 'block';
}

function addTestCase() {
    const testCasesContainer = document.getElementById('suite-test-cases');
    const newTestCase = document.createElement('div');
    newTestCase.className = 'test-case';
    newTestCase.id = `test-case-${testCaseCount}`;
    
    newTestCase.innerHTML = `
        <h5>测试用例 #${testCaseCount + 1}</h5>
        <div class="form-group">
            <label>名称:</label>
            <input type="text" name="test_cases-${testCaseCount}-name" required>
        </div>
        <div class="form-group">
            <label>URL:</label>
            <input type="url" name="test_cases-${testCaseCount}-url" required>
        </div>
        <div class="form-group">
            <label>方法:</label>
            <select name="test_cases-${testCaseCount}-method">
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
                <option value="PATCH">PATCH</option>
            </select>
        </div>
        <button type="button" onclick="removeTestCase(${testCaseCount})">移除</button>
    `;
    
    testCasesContainer.appendChild(newTestCase);
    testCaseCount++;
}

function removeTestCase(id) {
    const testCaseElement = document.getElementById(`test-case-${id}`);
    if (testCaseElement) {
        testCaseElement.remove();
    }
}

async function saveTestSuite() {
    const form = document.getElementById('suite-form');
    const formData = new FormData(form);
    
    const testCases = [];
    for (let i = 0; i < testCaseCount; i++) {
        const name = formData.get(`test_cases-${i}-name`);
        if (!name) continue; // 跳过已删除的测试用例
        
        testCases.push({
            name: name,
            url: formData.get(`test_cases-${i}-url`),
            method: formData.get(`test_cases-${i}-method`),
            expected_status: 200
        });
    }
    
    const testSuite = {
        name: formData.get('name'),
        test_cases: testCases,
        variables: {}
    };
    
    try {
        const response = await fetch('/test-suites', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testSuite)
        });
        
        const result = await response.json();
        alert('测试套件保存成功!');
        document.getElementById('create-suite-form').style.display = 'none';
        loadTestSuites();
    } catch (error) {
        console.error('Error:', error);
        alert('保存测试套件时出错: ' + error.message);
    }
}

async function loadTestSuites() {
    try {
        const response = await fetch('/test-suites');
        const data = await response.json();
        displayTestSuites(data.suites);
    } catch (error) {
        console.error('Error:', error);
    }
}

function displayTestSuites(suites) {
    const container = document.getElementById('suites-container');
    
    if (suites.length === 0) {
        container.innerHTML = '<p>暂无测试套件</p>';
        return;
    }
    
    container.innerHTML = suites.map(suite => `
        <div class="test-suite">
            <h4>${suite.name}</h4>
            <p>包含 ${suite.test_cases.length} 个测试用例</p>
            <button onclick="runTestSuite('${suite.id}')">运行测试套件</button>
            <button onclick="deleteTestSuite('${suite.id}')">删除</button>
        </div>
    `).join('');
}

async function runTestSuite(suiteId) {
    try {
        const response = await fetch(`/run-test/${suiteId}`, {
            method: 'POST'
        });
        
        const report = await response.json();
        displayTestReport(report);
        openTab('test-results');
    } catch (error) {
        console.error('Error:', error);
        alert('运行测试套件时出错: ' + error.message);
    }
}

function displayTestReport(report) {
    const container = document.getElementById('results-container');
    
    container.innerHTML = `
        <h3>测试报告: ${report.suite_name}</h3>
        <p>总测试数: ${report.total_tests} | 通过: <span class="success">${report.passed_tests}</span> | 失败: <span class="failure">${report.failed_tests}</span></p>
        <p>总执行时间: ${report.execution_time.toFixed(3)} 秒</p>
        
        <h4>详细结果:</h4>
        ${report.results.map(result => `
            <div class="test-result ${result.success ? 'success' : 'failure'}">
                <h5>${result.test_case.name} - ${result.success ? '通过' : '失败'}</h5>
                <p><strong>URL:</strong> ${result.test_case.url}</p>
                <p><strong>方法:</strong> ${result.test_case.method}</p>
                <p><strong>期望状态码:</strong> ${result.test_case.expected_status}</p>
                <p><strong>实际状态码:</strong> ${result.response_status}</p>
                <p><strong>执行时间:</strong> ${result.execution_time.toFixed(3)} 秒</p>
                ${result.error ? `<p><strong>错误信息:</strong> ${result.error}</p>` : ''}
                ${result.response_data ? `<p><strong>响应数据:</strong></p><pre>${JSON.stringify(result.response_data, null, 2)}</pre>` : ''}
            </div>
        `).join('')}
    `;
}

async function deleteTestSuite(suiteId) {
    if (!confirm('确定要删除这个测试套件吗?')) return;
    
    try {
        await fetch(`/test-suites/${suiteId}`, {
            method: 'DELETE'
        });
        
        loadTestSuites();
    } catch (error) {
        console.error('Error:', error);
        alert('删除测试套件时出错: ' + error.message);
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 默认打开第一个标签页
    document.querySelector('.tab-link.active').click();
});
```

## 运行应用

1. 创建项目目录并添加上述文件
2. 安装依赖：`pip install -r requirements.txt`
3. 运行应用：`uvicorn main:app --reload`
4. 打开浏览器访问：http://localhost:8000

## 功能特点

1. **单接口测试**：可以快速测试单个API接口
2. **测试套件管理**：创建和管理多个测试用例组成的测试套件
3. **批量测试**：一键运行整个测试套件
4. **详细测试报告**：显示每个测试用例的结果和整体测试统计
5. **可视化界面**：友好的Web界面，无需编写代码即可创建测试

## 扩展建议

1. 添加数据库支持，持久化存储测试套件和测试结果
2. 增加身份验证和授权功能
3. 支持环境变量和参数化测试
4. 添加定时任务功能，定期执行测试
5. 集成CI/CD工具
6. 支持更多断言类型和响应验证

这个工具提供了一个完整的API自动化测试解决方案，可以根据实际需求进一步扩展和完善。