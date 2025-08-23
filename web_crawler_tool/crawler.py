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