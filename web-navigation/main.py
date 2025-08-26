# 参考了FastAPI静态文件配置和模板渲染的基本用法
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import List, Optional
import json
import os

from config import CATEGORIES, SITE_DATA

# 初始化FastAPI应用
app = FastAPI(title="网页网址大全", version="1.0.0")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 初始化模板引擎
templates = Jinja2Templates(directory="templates")


# 模拟数据存储（实际应用中可使用数据库）
def load_sites():
    try:
        with open("sites.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return SITE_DATA


def save_sites(sites):
    with open("sites.json", "w", encoding="utf-8") as f:
        json.dump(sites, f, ensure_ascii=False, indent=2)


# 主页路由
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """渲染主页"""
    sites_data = load_sites()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "categories": CATEGORIES,
            "sites": sites_data
        }
    )


# 添加新网址的路由
@app.post("/add-site")
async def add_site(
        request: Request,
        name: str = Form(...),
        url: str = Form(...),
        category: str = Form(...),
        description: Optional[str] = Form("")
):
    """处理添加新网址的表单提交"""
    sites_data = load_sites()

    if category not in sites_data:
        sites_data[category] = []

    sites_data[category].append({
        "name": name,
        "url": url,
        "description": description
    })

    save_sites(sites_data)
    return RedirectResponse(url="/", status_code=303)


# 搜索网址的路由
@app.get("/search", response_class=HTMLResponse)
async def search_sites(request: Request, q: str = ""):
    """处理搜索请求"""
    if not q:
        return RedirectResponse(url="/")

    sites_data = load_sites()
    results = []

    for category, sites in sites_data.items():
        for site in sites:
            if q.lower() in site["name"].lower() or q.lower() in site["description"].lower():
                results.append({
                    "category": category,
                    **site
                })

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "categories": CATEGORIES,
            "sites": sites_data,
            "search_results": results,
            "search_query": q
        }
    )


# 启动应用
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)