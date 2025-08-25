# 使用FastAPI构建网页爬虫工具

下面是一个完整的基于FastAPI的网页爬虫工具实现。这个应用提供了一个Web界面，允许用户输入URL并选择要提取的数据类型，然后返回爬取结果。

## 项目结构
```
web_crawler_tool/
├── main.py          # FastAPI主应用
├── static/          # 静态文件目录
│   ├── style.css    # 样式表
│   └── script.js    # 前端JavaScript
├── templates/       # 模板目录
│   └── index.html   # 主页面模板
└── requirements.txt # 项目依赖
```

## 安装依赖
首先创建`requirements.txt`文件：
```
fastapi==0.104.1
uvicorn==0.24.0
aiohttp==3.9.1
beautifulsoup4==4.12.2
jinja2==3.1.2
python-multipart==0.0.6
```

安装依赖：
```bash
pip install -r requirements.txt
```

## 实现代码

### main.py
```python
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
```

### templates/index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Crawler Tool</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <h1>Web Crawler Tool</h1>
        <p>Enter a URL and select what data you want to extract from the website.</p>
        
        <form id="crawlForm">
            <div class="form-group">
                <label for="url">Website URL:</label>
                <input type="url" id="url" name="url" placeholder="https://example.com" required>
            </div>
            
            <div class="form-group">
                <label for="dataType">Data to Extract:</label>
                <select id="dataType" name="dataType">
                    <option value="links">Links</option>
                    <option value="images">Images</option>
                    <option value="text">Text Content</option>
                    <option value="metadata">Metadata</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="depth">Crawl Depth:</label>
                <input type="number" id="depth" name="depth" min="1" max="3" value="1">
                <span class="help">(1 = only this page, 2 = include linked pages, etc.)</span>
            </div>
            
            <div class="form-group">
                <label for="maxPages">Maximum Pages:</label>
                <input type="number" id="maxPages" name="maxPages" min="1" max="50" value="10">
            </div>
            
            <button type="submit" id="crawlBtn">Start Crawling</button>
        </form>
        
        <div id="loading" class="hidden">
            <div class="spinner"></div>
            <p>Crawling in progress... Please wait.</p>
        </div>
        
        <div id="results" class="hidden">
            <h2>Crawling Results</h2>
            <div class="summary">
                <p>Crawled <span id="pagesCount">0</span> pages in <span id="timeTaken">0</span> seconds.</p>
            </div>
            <div id="resultsContent"></div>
        </div>
        
        <div id="error" class="hidden">
            <h2>Error</h2>
            <p id="errorMessage"></p>
        </div>
    </div>
    
    <script src="/static/script.js"></script>
</body>
</html>
```

### static/style.css
```css
body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 20px;
    background-color: #f4f4f4;
    color: #333;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

h1 {
    color: #2c3e50;
    text-align: center;
}

.form-group {
    margin-bottom: 15px;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

input[type="url"],
input[type="number"],
select {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    box-sizing: border-box;
}

.help {
    font-size: 0.85em;
    color: #666;
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

button:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
}

.hidden {
    display: none;
}

#loading {
    text-align: center;
    margin: 20px 0;
}

.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 2s linear infinite;
    margin: 0 auto 15px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

#results, #error {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #eee;
}

.page-result {
    margin-bottom: 20px;
    padding: 15px;
    background-color: #f9f9f9;
    border-radius: 4px;
    border-left: 4px solid #3498db;
}

.page-url {
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 10px;
    display: block;
}

.data-item {
    margin-bottom: 10px;
    padding: 8px;
    background-color: white;
    border-radius: 4px;
    border: 1px solid #eee;
}

.data-item a {
    color: #3498db;
    text-decoration: none;
}

.data-item a:hover {
    text-decoration: underline;
}

.error {
    color: #e74c3c;
    padding: 10px;
    background-color: #fadbd8;
    border-radius: 4px;
}
```

### static/script.js
```javascript
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('crawlForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const crawlBtn = document.getElementById('crawlBtn');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const url = document.getElementById('url').value;
        const dataType = document.getElementById('dataType').value;
        const depth = document.getElementById('depth').value;
        const maxPages = document.getElementById('maxPages').value;
        
        // 显示加载状态，隐藏结果和错误
        loading.classList.remove('hidden');
        results.classList.add('hidden');
        errorDiv.classList.add('hidden');
        crawlBtn.disabled = true;
        
        try {
            const formData = new FormData();
            formData.append('url', url);
            formData.append('dataType', dataType);
            formData.append('depth', depth);
            formData.append('maxPages', maxPages);
            
            const response = await fetch('/crawl', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                displayResults(data);
            } else {
                showError(data.error || 'An unknown error occurred');
            }
        } catch (error) {
            showError('Network error: ' + error.message);
        } finally {
            loading.classList.add('hidden');
            crawlBtn.disabled = false;
        }
    });
    
    function displayResults(data) {
        document.getElementById('pagesCount').textContent = data.pages_crawled;
        document.getElementById('timeTaken').textContent = data.time_taken;
        
        const resultsContent = document.getElementById('resultsContent');
        resultsContent.innerHTML = '';
        
        if (data.pages_crawled === 0) {
            resultsContent.innerHTML = '<p class="error">No data could be extracted from the provided URL.</p>';
            results.classList.remove('hidden');
            return;
        }
        
        for (const [url, pageData] of Object.entries(data.results)) {
            const pageDiv = document.createElement('div');
            pageDiv.className = 'page-result';
            
            const urlHeading = document.createElement('a');
            urlHeading.className = 'page-url';
            urlHeading.href = url;
            urlHeading.target = '_blank';
            urlHeading.textContent = url;
            pageDiv.appendChild(urlHeading);
            
            // 根据数据类型显示不同内容
            if (pageData.links) {
                const linksHeading = document.createElement('h3');
                linksHeading.textContent = 'Links found:';
                pageDiv.appendChild(linksHeading);
                
                pageData.links.forEach(link => {
                    const linkDiv = document.createElement('div');
                    linkDiv.className = 'data-item';
                    
                    const linkEl = document.createElement('a');
                    linkEl.href = link.url;
                    linkEl.target = '_blank';
                    linkEl.textContent = link.text || link.url;
                    
                    linkDiv.appendChild(linkEl);
                    pageDiv.appendChild(linkDiv);
                });
            }
            
            if (pageData.images) {
                const imagesHeading = document.createElement('h3');
                imagesHeading.textContent = 'Images found:';
                pageDiv.appendChild(imagesHeading);
                
                pageData.images.forEach(image => {
                    const imgDiv = document.createElement('div');
                    imgDiv.className = 'data-item';
                    
                    const imgEl = document.createElement('img');
                    imgEl.src = image.src;
                    imgEl.alt = image.alt;
                    imgEl.style.maxWidth = '100%';
                    imgEl.style.height = 'auto';
                    
                    const altText = document.createElement('p');
                    altText.textContent = `Alt text: ${image.alt || 'None'}`;
                    
                    imgDiv.appendChild(imgEl);
                    imgDiv.appendChild(altText);
                    pageDiv.appendChild(imgDiv);
                });
            }
            
            if (pageData.text) {
                const textHeading = document.createElement('h3');
                textHeading.textContent = 'Text content:';
                pageDiv.appendChild(textHeading);
                
                const textDiv = document.createElement('div');
                textDiv.className = 'data-item';
                textDiv.textContent = pageData.text.length > 500 ? 
                    pageData.text.substring(0, 500) + '...' : 
                    pageData.text;
                pageDiv.appendChild(textDiv);
            }
            
            if (pageData.metadata) {
                const metaHeading = document.createElement('h3');
                metaHeading.textContent = 'Metadata:';
                pageDiv.appendChild(metaHeading);
                
                const metaDiv = document.createElement('div');
                metaDiv.className = 'data-item';
                
                for (const [key, value] of Object.entries(pageData.metadata)) {
                    const metaItem = document.createElement('p');
                    metaItem.innerHTML = `<strong>${key}:</strong> ${value || 'Not specified'}`;
                    metaDiv.appendChild(metaItem);
                }
                
                pageDiv.appendChild(metaDiv);
            }
            
            resultsContent.appendChild(pageDiv);
        }
        
        results.classList.remove('hidden');
    }
    
    function showError(message) {
        errorDiv.classList.remove('hidden');
        document.getElementById('errorMessage').textContent = message;
    }
});
```

## 运行应用

1. 创建项目目录结构：
```bash
mkdir -p web_crawler/{static,templates}
```

2. 将上述代码保存到相应文件中

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 运行应用：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. 打开浏览器访问：http://localhost:8000

## 功能特点

1. **用户友好界面**：提供直观的Web表单供用户输入参数
2. **多种数据提取**：支持提取链接、图片、文本内容和元数据
3. **可配置深度**：允许用户设置爬取深度（1-3级）
4. **限制页面数量**：防止过度爬取，保护目标网站
5. **异步处理**：使用aiohttp实现高效异步请求
6. **错误处理**：完善的异常处理和用户反馈
7. **结果展示**：清晰的结果展示界面

## 注意事项

1. 请遵守目标网站的robots.txt规则
2. 添加适当的延迟，避免对目标网站造成过大压力
3. 尊重版权和隐私政策
4. 考虑添加代理支持以避免IP被封
5. 可以进一步扩展支持JavaScript渲染的页面（如使用Selenium或Playwright）

这个爬虫工具提供了基本但实用的功能，可以根据需要进一步扩展和定制。