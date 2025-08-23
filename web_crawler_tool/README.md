# 使用 FastAPI 构建网页爬虫工具

下面我将为你创建一个基于 FastAPI 的 Web 爬虫工具，它可以抓取网页内容、提取数据和生成报告。

## 项目结构

```
web_crawler_tool/
├── main.py              # FastAPI 主应用
├── crawler.py           # 爬虫功能实现
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
aiohttp==3.8.5
beautifulsoup4==4.12.2
requests==2.31.0
lxml==4.9.3
python-multipart==0.0.6
```

安装依赖：
```bash
pip install -r requirements.txt
```

## 实现代码

### 1. 爬虫功能文件 (crawler.py)

```python
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import Dict, List, Set, Optional
import time

class WebCrawler:
    def __init__(self, max_pages: int = 10, timeout: int = 10):
        self.max_pages = max_pages
        self.timeout = timeout
        self.visited_urls: Set[str] = set()
        self.session = None
        self.results = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch(self, url: str) -> Optional[str]:
        """获取网页内容"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Failed to fetch {url}: Status {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None
    
    def extract_links(self, html: str, base_url: str) -> List[str]:
        """从HTML中提取链接"""
        soup = BeautifulSoup(html, 'lxml')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            # 只处理HTTP/HTTPS链接
            if absolute_url.startswith(('http://', 'https://')):
                links.append(absolute_url)
        
        return links
    
    def extract_data(self, html: str, url: str) -> Dict:
        """从HTML中提取数据"""
        soup = BeautifulSoup(html, 'lxml')
        
        # 提取标题
        title = soup.title.string if soup.title else "无标题"
        
        # 提取元描述
        meta_desc = ""
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag and meta_tag.get('content'):
            meta_desc = meta_tag['content']
        
        # 提取所有文本
        text = soup.get_text()
        word_count = len(text.split())
        
        # 提取图片数量
        images = soup.find_all('img')
        image_count = len(images)
        
        # 提取链接数量
        links = soup.find_all('a')
        link_count = len(links)
        
        # 提取h1标签
        h1_tags = [h1.get_text().strip() for h1 in soup.find_all('h1')]
        
        # 提取所有段落
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()]
        
        return {
            'url': url,
            'title': title,
            'meta_description': meta_desc,
            'word_count': word_count,
            'image_count': image_count,
            'link_count': link_count,
            'h1_tags': h1_tags,
            'paragraphs': paragraphs[:5]  # 只取前5个段落
        }
    
    async def crawl(self, start_url: str, depth: int = 1) -> List[Dict]:
        """开始爬取"""
        if not self.session:
            async with aiohttp.ClientSession() as session:
                self.session = session
                return await self._crawl(start_url, depth)
        else:
            return await self._crawl(start_url, depth)
    
    async def _crawl(self, start_url: str, depth: int) -> List[Dict]:
        """实际的爬取逻辑"""
        self.visited_urls.clear()
        self.results.clear()
        
        # 获取域名用于限制爬取范围
        domain = urlparse(start_url).netloc
        
        # 使用队列进行广度优先爬取
        queue = [(start_url, 0)]
        
        while queue and len(self.visited_urls) < self.max_pages:
            url, current_depth = queue.pop(0)
            
            if url in self.visited_urls or current_depth > depth:
                continue
            
            print(f"Crawling: {url} (depth: {current_depth})")
            
            html = await self.fetch(url)
            if html:
                self.visited_urls.add(url)
                
                # 提取数据
                data = self.extract_data(html, url)
                self.results.append(data)
                
                # 如果还没达到最大深度，提取链接并加入队列
                if current_depth < depth:
                    links = self.extract_links(html, url)
                    for link in links:
                        # 只爬取同一域名的链接
                        if urlparse(link).netloc == domain and link not in self.visited_urls:
                            queue.append((link, current_depth + 1))
            
            # 添加延迟，避免过于频繁的请求
            await asyncio.sleep(0.5)
        
        return self.results

async def simple_crawl(url: str, extract_pattern: str = None) -> Dict:
    """简单爬取单个页面"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # 提取标题
                    title = soup.title.string if soup.title else "无标题"
                    
                    # 如果提供了提取模式，尝试提取特定内容
                    extracted_data = []
                    if extract_pattern:
                        try:
                            # 尝试使用CSS选择器
                            elements = soup.select(extract_pattern)
                            extracted_data = [elem.get_text().strip() for elem in elements if elem.get_text().strip()]
                            
                            # 如果没有找到，尝试使用正则表达式
                            if not extracted_data:
                                pattern = re.compile(extract_pattern)
                                matches = pattern.findall(html)
                                extracted_data = [match for match in matches if match]
                        except Exception as e:
                            print(f"Error extracting with pattern {extract_pattern}: {str(e)}")
                    
                    return {
                        'url': url,
                        'title': title,
                        'content': html[:1000] + "..." if len(html) > 1000 else html,  # 限制内容长度
                        'extracted_data': extracted_data,
                        'success': True
                    }
                else:
                    return {
                        'url': url,
                        'error': f"HTTP错误: {response.status}",
                        'success': False
                    }
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'success': False
            }
```

### 2. 主应用文件 (main.py)

```python
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
```

### 3. 前端模板 (templates/index.html)

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>网页爬虫工具</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <header>
        <div class="container">
            <h1>网页爬虫工具</h1>
            <p>抓取、分析和提取网页内容</p>
        </div>
    </header>
    
    <nav>
        <div class="container">
            <ul>
                <li><a href="#crawl-website">网站爬取</a></li>
                <li><a href="#single-page">单页提取</a></li>
                <li><a href="#results">结果分析</a></li>
            </ul>
        </div>
    </nav>
    
    <main class="container">
        <section id="crawl-website" class="section">
            <h2>网站爬取</h2>
            <form id="crawlForm" class="form">
                <div class="form-group">
                    <label for="url">网站URL:</label>
                    <input type="url" id="url" name="url" placeholder="https://example.com" required>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="depth">爬取深度:</label>
                        <select id="depth" name="depth">
                            <option value="1">1 - 只爬取首页</option>
                            <option value="2">2 - 首页+一层内链</option>
                            <option value="3">3 - 首页+两层内链</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="maxPages">最大页面数:</label>
                        <input type="number" id="maxPages" name="maxPages" min="1" max="50" value="10">
                    </div>
                </div>
                
                <button type="submit" id="crawlBtn">开始爬取</button>
            </form>
        </section>
        
        <section id="single-page" class="section">
            <h2>单页内容提取</h2>
            <form id="singlePageForm" class="form">
                <div class="form-group">
                    <label for="singleUrl">页面URL:</label>
                    <input type="url" id="singleUrl" name="url" placeholder="https://example.com/page" required>
                </div>
                
                <div class="form-group">
                    <label for="extractPattern">提取模式 (CSS选择器或正则表达式):</label>
                    <input type="text" id="extractPattern" name="extractPattern" placeholder="例如: h1, .content, 或正则表达式">
                </div>
                
                <button type="submit" id="singlePageBtn">提取内容</button>
            </form>
        </section>
        
        <section id="results" class="section">
            <h2>爬取结果</h2>
            <div id="loading" class="loading hidden">
                <div class="spinner"></div>
                <p>正在爬取，请稍候...</p>
            </div>
            
            <div id="error" class="error hidden"></div>
            
            <div id="resultsContainer" class="hidden">
                <div class="results-header">
                    <h3>爬取统计</h3>
                    <div class="action-buttons">
                        <button id="exportBtn">导出CSV</button>
                        <button id="analyzeBtn">分析结果</button>
                    </div>
                </div>
                
                <div id="analysisResult" class="analysis-result hidden"></div>
                
                <div class="results-grid">
                    <div class="result-card" v-for="result in results" :key="result.url">
                        <h4>{{ result.title }}</h4>
                        <p class="url">{{ result.url }}</p>
                        <p class="description" v-if="result.meta_description">{{ result.meta_description }}</p>
                        <div class="stats">
                            <span>字数: {{ result.word_count }}</span>
                            <span>图片: {{ result.image_count }}</span>
                            <span>链接: {{ result.link_count }}</span>
                        </div>
                        <div class="h1-tags" v-if="result.h1_tags && result.h1_tags.length">
                            <strong>H1标签:</strong>
                            <ul>
                                <li v-for="h1 in result.h1_tags">{{ h1 }}</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="singleResult" class="single-result hidden">
                <h3>单页提取结果</h3>
                <div v-if="singleResult.success">
                    <h4>{{ singleResult.title }}</h4>
                    <p class="url">{{ singleResult.url }}</p>
                    
                    <div v-if="singleResult.extracted_data && singleResult.extracted_data.length">
                        <h5>提取的内容:</h5>
                        <ul>
                            <li v-for="item in singleResult.extracted_data">{{ item }}</li>
                        </ul>
                    </div>
                    
                    <div class="content-preview">
                        <h5>内容预览:</h5>
                        <pre>{{ singleResult.content }}</pre>
                    </div>
                </div>
                <div v-else>
                    <p class="error">提取失败: {{ singleResult.error }}</p>
                </div>
            </div>
        </section>
    </main>
    
    <footer>
        <div class="container">
            <p>&copy; 2023 网页爬虫工具 - 使用 FastAPI 构建</p>
            <p class="disclaimer">注意: 请确保您有权限爬取目标网站，并遵守robots.txt和网站使用条款</p>
        </div>
    </footer>
    
    <!-- 引入Vue.js用于简单数据绑定 -->
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="/static/script.js"></script>
</body>
</html>
```

### 4. 样式文件 (static/style.css)

```css
/* 全局样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f7f9;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* 头部样式 */
header {
    background: linear-gradient(135deg, #3498db, #2c3e50);
    color: white;
    padding: 30px 0;
    text-align: center;
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 10px;
}

header p {
    font-size: 1.1rem;
    opacity: 0.9;
}

/* 导航样式 */
nav {
    background-color: white;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    margin-bottom: 30px;
    position: sticky;
    top: 0;
    z-index: 100;
}

nav ul {
    display: flex;
    list-style: none;
    padding: 15px 0;
    justify-content: center;
}

nav li {
    margin: 0 15px;
}

nav a {
    text-decoration: none;
    color: #2c3e50;
    font-weight: 500;
    padding: 5px 0;
    transition: color 0.2s;
}

nav a:hover {
    color: #3498db;
}

/* 主内容样式 */
.section {
    background-color: white;
    border-radius: 8px;
    padding: 25px;
    margin-bottom: 30px;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
}

.section h2 {
    color: #2c3e50;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
}

/* 表单样式 */
.form {
    margin-top: 20px;
}

.form-group {
    margin-bottom: 15px;
}

.form-row {
    display: flex;
    gap: 20px;
}

.form-row .form-group {
    flex: 1;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
    color: #2c3e50;
}

.form-group input,
.form-group select,
.form-group textarea {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

button {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    transition: background-color 0.2s;
}

button:hover {
    background-color: #2980b9;
}

button:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
}

/* 结果区域样式 */
.results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.action-buttons {
    display: flex;
    gap: 10px;
}

.results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}

.result-card {
    border: 1px solid #eee;
    border-radius: 6px;
    padding: 15px;
    transition: box-shadow 0.2s;
}

.result-card:hover {
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
}

.result-card h4 {
    margin-bottom: 10px;
    color: #2c3e50;
}

.result-card .url {
    color: #7f8c8d;
    font-size: 0.9rem;
    margin-bottom: 10px;
    word-break: break-all;
}

.result-card .description {
    color: #34495e;
    margin-bottom: 15px;
}

.result-card .stats {
    display: flex;
    gap: 15px;
    margin-bottom: 15px;
}

.result-card .stats span {
    background-color: #f8f9fa;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.85rem;
}

.h1-tags ul {
    margin-top: 5px;
    padding-left: 20px;
}

.h1-tags li {
    margin-bottom: 5px;
    font-size: 0.9rem;
}

/* 单页结果样式 */
.single-result {
    margin-top: 20px;
}

.content-preview {
    margin-top: 15px;
}

.content-preview pre {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
    overflow: auto;
    max-height: 300px;
    font-size: 0.9rem;
}

/* 分析结果样式 */
.analysis-result {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 6px;
    margin-bottom: 20px;
}

.analysis-result h4 {
    margin-bottom: 10px;
    color: #2c3e50;
}

.analysis-result .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 15px;
}

.stat-item {
    background-color: white;
    padding: 15px;
    border-radius: 6px;
    text-align: center;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #3498db;
    margin-bottom: 5px;
}

.stat-label {
    font-size: 0.9rem;
    color: #7f8c8d;
}

/* 加载和错误样式 */
.loading {
    text-align: center;
    padding: 30px;
}

.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 0 auto 15px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.error {
    background-color: #fadbd8;
    color: #c0392b;
    padding: 15px;
    border-radius: 6px;
    margin-bottom: 20px;
}

.hidden {
    display: none;
}

/* 页脚样式 */
footer {
    background-color: #2c3e50;
    color: white;
    text-align: center;
    padding: 20px 0;
    margin-top: 40px;
}

footer .disclaimer {
    font-size: 0.9rem;
    opacity: 0.8;
    margin-top: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .form-row {
        flex-direction: column;
        gap: 15px;
    }
    
    .results-grid {
        grid-template-columns: 1fr;
    }
    
    .results-header {
        flex-direction: column;
        gap: 15px;
        align-items: flex-start;
    }
    
    nav ul {
        flex-wrap: wrap;
        justify-content: center;
    }
    
    nav li {
        margin: 5px 10px;
    }
}
```

### 5. JavaScript 文件 (static/script.js)

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // 初始化Vue应用
    const { createApp } = Vue;
    
    const app = createApp({
        data() {
            return {
                results: [],
                singleResult: {}
            }
        }
    }).mount('#results');
    
    // 获取DOM元素
    const crawlForm = document.getElementById('crawlForm');
    const singlePageForm = document.getElementById('singlePageForm');
    const loading = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    const resultsContainer = document.getElementById('resultsContainer');
    const singleResult = document.getElementById('singleResult');
    const exportBtn = document.getElementById('exportBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analysisResult = document.getElementById('analysisResult');
    
    // 网站爬取表单提交
    crawlForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const url = document.getElementById('url').value;
        const depth = document.getElementById('depth').value;
        const maxPages = document.getElementById('maxPages').value;
        
        // 显示加载，隐藏错误和结果
        showLoading();
        hideError();
        hideResults();
        
        try {
            const response = await fetch('/crawl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'url': url,
                    'depth': depth,
                    'max_pages': maxPages
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                app.results = data.results;
                showResults();
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('请求失败: ' + error.message);
        } finally {
            hideLoading();
        }
    });
    
    // 单页提取表单提交
    singlePageForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const url = document.getElementById('singleUrl').value;
        const extractPattern = document.getElementById('extractPattern').value;
        
        // 显示加载，隐藏错误和结果
        showLoading();
        hideError();
        hideResults();
        
        try {
            const response = await fetch('/crawl-single', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'url': url,
                    'extract_pattern': extractPattern || ''
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                app.singleResult = data.result;
                showSingleResult();
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('请求失败: ' + error.message);
        } finally {
            hideLoading();
        }
    });
    
    // 导出CSV按钮点击
    exportBtn.addEventListener('click', async function() {
        try {
            const response = await fetch('/export-csv', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    results: app.results
                })
            });
            
            if (response.ok) {
                // 创建下载链接
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `crawl_results_${Date.now()}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const data = await response.json();
                showError(data.error || '导出失败');
            }
        } catch (error) {
            showError('导出失败: ' + error.message);
        }
    });
    
    // 分析结果按钮点击
    analyzeBtn.addEventListener('click', async function() {
        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    results: app.results
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showAnalysis(data.analysis);
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('分析失败: ' + error.message);
        }
    });
    
    // 显示/隐藏函数
    function showLoading() {
        loading.classList.remove('hidden');
    }
    
    function hideLoading() {
        loading.classList.add('hidden');
    }
    
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
    }
    
    function hideError() {
        errorDiv.classList.add('hidden');
    }
    
    function showResults() {
        resultsContainer.classList.remove('hidden');
        singleResult.classList.add('hidden');
        analysisResult.classList.add('hidden');
    }
    
    function showSingleResult() {
        singleResult.classList.remove('hidden');
        resultsContainer.classList.add('hidden');
        analysisResult.classList.add('hidden');
    }
    
    function hideResults() {
        resultsContainer.classList.add('hidden');
        singleResult.classList.add('hidden');
    }
    
    function showAnalysis(analysis) {
        analysisResult.classList.remove('hidden');
        
        // 创建分析结果HTML
        analysisResult.innerHTML = `
            <h4>分析结果</h4>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${analysis.total_pages}</div>
                    <div class="stat-label">总页面数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${analysis.total_words}</div>
                    <div class="stat-label">总字数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${analysis.total_images}</div>
                    <div class="stat-label">总图片数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${analysis.total_links}</div>
                    <div class="stat-label">总链接数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${Math.round(analysis.avg_words_per_page)}</div>
                    <div class="stat-label">平均每页字数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${Math.round(analysis.avg_images_per_page)}</div>
                    <div class="stat-label">平均每页图片数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${Math.round(analysis.avg_links_per_page)}</div>
                    <div class="stat-label">平均每页链接数</div>
                </div>
            </div>
            ${analysis.common_words.length > 0 ? `
                <div>
                    <h5>常见词汇:</h5>
                    <ul>
                        ${analysis.common_words.map(item => `<li>${item[0]} (${item[1]}次)</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        `;
    }
    
    // 平滑滚动到锚点
    document.querySelectorAll('nav a').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});
```

## 运行应用

使用以下命令启动应用：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000 即可使用网页爬虫工具。

## 功能说明

1. **网站爬取**：输入URL、设置爬取深度和最大页面数，爬取整个网站
2. **单页提取**：提取单个页面的内容，支持CSS选择器或正则表达式提取特定内容
3. **结果展示**：以卡片形式展示爬取结果，包括标题、URL、描述、字数统计等
4. **数据分析**：分析爬取结果，提供统计信息和常见词汇
5. **导出功能**：将爬取结果导出为CSV文件
6. **响应式设计**：适配各种屏幕尺寸

## 使用示例

1. **爬取整个网站**：
   - 输入URL：https://example.com
   - 设置深度：2（爬取首页和一层内链）
   - 设置最大页面数：10
   - 点击"开始爬取"

2. **提取单个页面**：
   - 输入URL：https://example.com/blog/post
   - 输入提取模式：h1（提取所有h1标签内容）
   - 点击"提取内容"

3. **分析结果**：
   - 爬取完成后，点击"分析结果"查看统计信息
   - 点击"导出CSV"将结果保存为文件

## 注意事项

1. **遵守规则**：确保您有权限爬取目标网站，并遵守robots.txt和网站使用条款
2. **频率限制**：添加适当的延迟，避免对目标网站造成过大负担
3. **错误处理**：工具包含了基本的错误处理，但可能无法处理所有异常情况
4. **性能考虑**：对于大型网站，爬取可能需要较长时间

这个网页爬虫工具可以帮助您快速抓取和分析网站内容，适用于SEO分析、内容研究和竞争分析等场景。您可以根据需要进一步扩展功能，如添加代理支持、更复杂的数据提取规则或可视化分析图表。