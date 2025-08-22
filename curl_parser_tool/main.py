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