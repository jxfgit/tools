from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import crawler
import asyncio
import json
from typing import List, Dict
import csv
import io

app = FastAPI(title="网页爬虫工具", description="一个强大的网页内容抓取和分析工具")

# 挂载静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """显示主页面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/crawl")
async def crawl_website(
        request: Request,
        url: str = Form(...),
        depth: int = Form(1),
        max_pages: int = Form(10)
):
    """爬取网站"""
    try:
        # 验证URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # 创建爬虫实例
        async with crawler.WebCrawler(max_pages=max_pages) as crawler_instance:
            # 开始爬取
            results = await crawler_instance.crawl(url, depth)

            return JSONResponse({
                "success": True,
                "results": results,
                "total_pages": len(results),
                "message": f"成功爬取 {len(results)} 个页面"
            })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/crawl-single")
async def crawl_single_page(
        request: Request,
        url: str = Form(...),
        extract_pattern: str = Form(None)
):
    """爬取单个页面"""
    try:
        # 验证URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # 爬取单个页面
        result = await crawler.simple_crawl(url, extract_pattern)

        return JSONResponse({
            "success": True,
            "result": result
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/export-csv")
async def export_to_csv(request: Request):
    """将爬取结果导出为CSV"""
    try:
        data = await request.json()
        results = data.get("results", [])

        if not results:
            raise HTTPException(status_code=400, detail="没有数据可导出")

        # 创建CSV输出
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入标题行
        writer.writerow(["URL", "标题", "描述", "字数", "图片数", "链接数", "H1标签"])

        # 写入数据行
        for result in results:
            writer.writerow([
                result.get("url", ""),
                result.get("title", "")[:50],  # 限制标题长度
                result.get("meta_description", "")[:100],  # 限制描述长度
                result.get("word_count", 0),
                result.get("image_count", 0),
                result.get("link_count", 0),
                "; ".join(result.get("h1_tags", []))[:100]  # 限制H1标签长度
            ])

        # 准备响应
        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=crawl_results_{int(time.time())}.csv"
            }
        )
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/analyze")
async def analyze_results(request: Request):
    """分析爬取结果"""
    try:
        data = await request.json()
        results = data.get("results", [])

        if not results:
            raise HTTPException(status_code=400, detail="没有数据可分析")

        # 计算统计信息
        total_pages = len(results)
        total_words = sum(result.get("word_count", 0) for result in results)
        total_images = sum(result.get("image_count", 0) for result in results)
        total_links = sum(result.get("link_count", 0) for result in results)

        # 提取所有标题和描述
        titles = [result.get("title", "") for result in results]
        descriptions = [result.get("meta_description", "") for result in results if result.get("meta_description")]

        # 查找最常见的词语（简单实现）
        all_text = " ".join(titles + descriptions)
        words = all_text.split()
        from collections import Counter
        word_freq = Counter(words)
        common_words = word_freq.most_common(10)

        return JSONResponse({
            "success": True,
            "analysis": {
                "total_pages": total_pages,
                "total_words": total_words,
                "total_images": total_images,
                "total_links": total_links,
                "avg_words_per_page": total_words / total_pages if total_pages > 0 else 0,
                "avg_images_per_page": total_images / total_pages if total_pages > 0 else 0,
                "avg_links_per_page": total_links / total_pages if total_pages > 0 else 0,
                "common_words": common_words
            }
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)