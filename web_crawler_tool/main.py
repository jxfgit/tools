from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import asyncio
from typing import List, Dict, Optional
import time

app = FastAPI(title="Web Crawler Tool", version="1.0.0")

# 挂载静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 用户代理头，避免被某些网站阻止
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


class WebCrawler:
    def __init__(self, max_pages: int = 10, timeout: int = 10):
        self.max_pages = max_pages
        self.timeout = timeout
        self.visited_urls = set()
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=HEADERS, timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_url(self, url: str) -> Optional[str]:
        """获取URL内容"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Failed to fetch {url}: Status code {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None

    def extract_links(self, html: str, base_url: str) -> List[str]:
        """从HTML中提取链接"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            # 处理相对URL
            absolute_url = urljoin(base_url, href)
            # 确保URL有效且属于同一域名
            if self.is_valid_url(absolute_url, base_url):
                links.append(absolute_url)

        return links

    def is_valid_url(self, url: str, base_url: str) -> bool:
        """检查URL是否有效且属于同一域名"""
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_url)

        # 只处理HTTP和HTTPS
        if parsed_url.scheme not in ('http', 'https'):
            return False

        # 确保属于同一域名
        if parsed_url.netloc != parsed_base.netloc:
            return False

        # 避免非页面资源
        if any(ext in parsed_url.path for ext in ['.pdf', '.doc', '.docx', '.jpg', '.png', '.gif', '.zip', '.rar']):
            return False

        return True

    def extract_data(self, html: str, data_type: str) -> Dict:
        """根据数据类型从HTML中提取信息"""
        soup = BeautifulSoup(html, 'html.parser')
        result = {}

        if data_type == "links":
            links = []
            for link in soup.find_all('a', href=True):
                links.append({
                    "text": link.get_text(strip=True),
                    "url": link['href']
                })
            result["links"] = links

        elif data_type == "images":
            images = []
            for img in soup.find_all('img', src=True):
                images.append({
                    "alt": img.get('alt', ''),
                    "src": img['src']
                })
            result["images"] = images

        elif data_type == "text":
            # 移除脚本和样式元素
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text(separator='\n', strip=True)
            result["text"] = text

        elif data_type == "metadata":
            metadata = {}
            # 提取标题
            if soup.title:
                metadata["title"] = soup.title.string

            # 提取meta描述
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                metadata["description"] = meta_desc.get("content", "")

            # 提取关键词
            meta_keywords = soup.find("meta", attrs={"name": "keywords"})
            if meta_keywords:
                metadata["keywords"] = meta_keywords.get("content", "")

            result["metadata"] = metadata

        return result

    async def crawl(self, start_url: str, data_type: str, depth: int = 1) -> Dict:
        """执行爬取操作"""
        results = {}
        queue = [(start_url, 0)]  # (url, current_depth)

        async with self:
            while queue and len(self.visited_urls) < self.max_pages:
                url, current_depth = queue.pop(0)

                if url in self.visited_urls or current_depth > depth:
                    continue

                print(f"Crawling: {url} (depth: {current_depth})")
                self.visited_urls.add(url)

                html = await self.fetch_url(url)
                if not html:
                    continue

                # 提取所需数据
                page_data = self.extract_data(html, data_type)
                results[url] = page_data

                # 如果还需要继续深入，提取链接并添加到队列
                if current_depth < depth:
                    links = self.extract_links(html, url)
                    for link in links:
                        if link not in self.visited_urls:
                            queue.append((link, current_depth + 1))

                # 添加短暂延迟，避免对服务器造成过大压力
                await asyncio.sleep(0.5)

        return results


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """主页面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/crawl")
async def crawl_website(
        request: Request,
        url: str = Form(...),
        data_type: str = Form("links"),
        depth: int = Form(1),
        max_pages: int = Form(10)
):
    """处理爬取请求"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        crawler = WebCrawler(max_pages=max_pages)
        start_time = time.time()
        results = await crawler.crawl(url, data_type, depth)
        end_time = time.time()

        return JSONResponse({
            "success": True,
            "time_taken": round(end_time - start_time, 2),
            "pages_crawled": len(results),
            "results": results
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)