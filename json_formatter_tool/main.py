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