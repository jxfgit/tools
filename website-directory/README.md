# Python FastAPI 网址大全应用

下面我将设计一个完整的网址大全应用，支持动态添加新网址，使用FastAPI作为后端，HTML/JavaScript/CSS作为前端。

## 设计思路

1. 后端使用FastAPI提供RESTful API
2. 前端使用简洁的卡片式布局展示网址
3. 使用localStorage模拟数据存储（实际应用中可替换为数据库）
4. 支持添加、删除和分类展示网址

## 完整代码实现

### 后端代码 (main.py)

```python
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import os

app = FastAPI(title="网址大全", version="1.0.0")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 数据模型
class Website(BaseModel):
    id: Optional[int] = None
    title: str
    url: str
    category: str = "未分类"
    description: Optional[str] = ""

# 模拟数据存储
DATA_FILE = "websites.json"

def load_websites():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_websites(websites):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(websites, f, ensure_ascii=False, indent=2)

# API路由
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/websites", response_model=List[Website])
async def get_websites():
    return load_websites()

@app.post("/api/websites", response_model=Website)
async def create_website(website: Website):
    websites = load_websites()
    # 生成新ID
    if websites:
        new_id = max(w.get("id", 0) for w in websites) + 1
    else:
        new_id = 1
    website_dict = website.dict()
    website_dict["id"] = new_id
    websites.append(website_dict)
    save_websites(websites)
    return website_dict

@app.delete("/api/websites/{website_id}")
async def delete_website(website_id: int):
    websites = load_websites()
    initial_length = len(websites)
    websites = [w for w in websites if w.get("id") != website_id]
    
    if len(websites) == initial_length:
        raise HTTPException(status_code=404, detail="Website not found")
    
    save_websites(websites)
    return {"message": "Website deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 前端HTML (templates/index.html)

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>网址大全</title>
    <link rel="stylesheet" href="/static/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
</head>
<body>
    <div class="container">
        <header>
            <h1><i class="fas fa-bookmark"></i> 网址大全</h1>
            <p>收集并分享有用的网站资源</p>
        </header>

        <div class="controls">
            <button id="addWebsiteBtn" class="btn-primary">
                <i class="fas fa-plus"></i> 添加新网址
            </button>
            <input type="text" id="searchInput" placeholder="搜索网址...">
            <select id="categoryFilter">
                <option value="">所有分类</option>
                <!-- 分类选项将通过JS动态添加 -->
            </select>
        </div>

        <div class="modal" id="addWebsiteModal">
            <div class="modal-content">
                <span class="close">&times;</span>
                <h2>添加新网址</h2>
                <form id="websiteForm">
                    <div class="form-group">
                        <label for="title">网站名称:</label>
                        <input type="text" id="title" required>
                    </div>
                    <div class="form-group">
                        <label for="url">网址:</label>
                        <input type="url" id="url" placeholder="https://example.com" required>
                    </div>
                    <div class="form-group">
                        <label for="category">分类:</label>
                        <input type="text" id="category" list="categories" required>
                        <datalist id="categories">
                            <!-- 分类选项将通过JS动态添加 -->
                        </datalist>
                    </div>
                    <div class="form-group">
                        <label for="description">描述 (可选):</label>
                        <textarea id="description" rows="3"></textarea>
                    </div>
                    <button type="submit" class="btn-primary">添加网址</button>
                </form>
            </div>
        </div>

        <div id="websitesContainer" class="websites-grid">
            <!-- 网址卡片将通过JS动态添加 -->
        </div>

        <footer>
            <p>© 2023 网址大全 - 使用 FastAPI 构建</p>
        </footer>
    </div>

    <script src="/static/script.js"></script>
</body>
</html>
```

### 前端CSS (static/style.css)

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f7fa;
    padding: 20px;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}

header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
    background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
    color: white;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 10px;
}

.controls {
    display: flex;
    gap: 15px;
    margin-bottom: 30px;
    flex-wrap: wrap;
    align-items: center;
}

#searchInput, #categoryFilter {
    padding: 10px 15px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 1rem;
    flex-grow: 1;
    max-width: 300px;
}

.btn-primary {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 1rem;
    transition: background-color 0.3s;
}

.btn-primary:hover {
    background-color: #45a049;
}

.websites-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.website-card {
    background-color: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s, box-shadow 0.3s;
}

.website-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

.card-header {
    padding: 15px;
    background-color: #f8f9fa;
    border-bottom: 1px solid #eee;
}

.card-header h3 {
    margin-bottom: 5px;
    color: #2c3e50;
}

.category {
    display: inline-block;
    background-color: #e1f0ff;
    color: #2c7be5;
    padding: 3px 8px;
    border-radius: 15px;
    font-size: 0.8rem;
}

.card-body {
    padding: 15px;
}

.card-body p {
    color: #666;
    margin-bottom: 15px;
}

.card-footer {
    padding: 15px;
    background-color: #f8f9fa;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: space-between;
}

.visit-btn {
    background-color: #3498db;
    color: white;
    text-decoration: none;
    padding: 8px 15px;
    border-radius: 5px;
    font-size: 0.9rem;
    transition: background-color 0.3s;
}

.visit-btn:hover {
    background-color: #2980b9;
}

.delete-btn {
    background-color: #e74c3c;
    color: white;
    border: none;
    padding: 8px 15px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.3s;
}

.delete-btn:hover {
    background-color: #c0392b;
}

.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
}

.modal-content {
    background-color: white;
    margin: 10% auto;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    width: 90%;
    max-width: 500px;
    position: relative;
}

.close {
    color: #aaa;
    float: right;
    font-size: 28px;
    font-weight: bold;
    cursor: pointer;
}

.close:hover {
    color: black;
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: 600;
}

.form-group input, .form-group textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 1rem;
}

footer {
    text-align: center;
    padding: 20px;
    color: #666;
    border-top: 1px solid #eee;
    margin-top: 30px;
}

@media (max-width: 768px) {
    .controls {
        flex-direction: column;
        align-items: stretch;
    }
    
    #searchInput, #categoryFilter {
        max-width: none;
    }
    
    .websites-grid {
        grid-template-columns: 1fr;
    }
}
```

### 前端JavaScript (static/script.js)

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // DOM元素
    const websitesContainer = document.getElementById('websitesContainer');
    const addWebsiteBtn = document.getElementById('addWebsiteBtn');
    const modal = document.getElementById('addWebsiteModal');
    const closeBtn = document.querySelector('.close');
    const websiteForm = document.getElementById('websiteForm');
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const categoriesDatalist = document.getElementById('categories');
    
    // 状态变量
    let websites = [];
    let categories = new Set();
    
    // 初始化
    loadWebsites();
    
    // 事件监听
    addWebsiteBtn.addEventListener('click', () => modal.style.display = 'block');
    closeBtn.addEventListener('click', () => modal.style.display = 'none');
    window.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });
    
    websiteForm.addEventListener('submit', handleAddWebsite);
    searchInput.addEventListener('input', filterWebsites);
    categoryFilter.addEventListener('change', filterWebsites);
    
    // 加载网址数据
    async function loadWebsites() {
        try {
            const response = await fetch('/api/websites');
            websites = await response.json();
            renderWebsites(websites);
            updateCategories(websites);
        } catch (error) {
            console.error('加载网址失败:', error);
        }
    }
    
    // 渲染网址卡片
    function renderWebsites(websitesToRender) {
        websitesContainer.innerHTML = '';
        
        if (websitesToRender.length === 0) {
            websitesContainer.innerHTML = '<p class="no-results">没有找到网址</p>';
            return;
        }
        
        websitesToRender.forEach(website => {
            const card = document.createElement('div');
            card.className = 'website-card';
            card.innerHTML = `
                <div class="card-header">
                    <h3>${website.title}</h3>
                    <span class="category">${website.category}</span>
                </div>
                <div class="card-body">
                    <p>${website.description || '暂无描述'}</p>
                </div>
                <div class="card-footer">
                    <a href="${website.url}" target="_blank" class="visit-btn">访问网站</a>
                    <button class="delete-btn" data-id="${website.id}">删除</button>
                </div>
            `;
            websitesContainer.appendChild(card);
        });
        
        // 添加删除按钮事件监听
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', () => deleteWebsite(btn.dataset.id));
        });
    }
    
    // 更新分类选项
    function updateCategories(websites) {
        // 清空现有选项
        categoryFilter.innerHTML = '<option value="">所有分类</option>';
        categoriesDatalist.innerHTML = '';
        
        // 收集所有分类
        categories = new Set(websites.map(w => w.category));
        
        // 添加分类到筛选器和datalist
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            categoryFilter.appendChild(option);
            
            const datalistOption = document.createElement('option');
            datalistOption.value = category;
            categoriesDatalist.appendChild(datalistOption);
        });
    }
    
    // 处理添加网址
    async function handleAddWebsite(e) {
        e.preventDefault();
        
        const newWebsite = {
            title: document.getElementById('title').value,
            url: document.getElementById('url').value,
            category: document.getElementById('category').value,
            description: document.getElementById('description').value
        };
        
        try {
            const response = await fetch('/api/websites', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newWebsite)
            });
            
            if (response.ok) {
                // 清空表单
                websiteForm.reset();
                // 隐藏模态框
                modal.style.display = 'none';
                // 重新加载网址
                loadWebsites();
            } else {
                alert('添加网址失败');
            }
        } catch (error) {
            console.error('添加网址错误:', error);
            alert('添加网址时发生错误');
        }
    }
    
    // 删除网址
    async function deleteWebsite(id) {
        if (!confirm('确定要删除这个网址吗？')) return;
        
        try {
            const response = await fetch(`/api/websites/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                loadWebsites();
            } else {
                alert('删除网址失败');
            }
        } catch (error) {
            console.error('删除网址错误:', error);
            alert('删除网址时发生错误');
        }
    }
    
    // 筛选网址
    function filterWebsites() {
        const searchText = searchInput.value.toLowerCase();
        const selectedCategory = categoryFilter.value;
        
        const filteredWebsites = websites.filter(website => {
            const matchesSearch = website.title.toLowerCase().includes(searchText) || 
                                (website.description && website.description.toLowerCase().includes(searchText));
            const matchesCategory = !selectedCategory || website.category === selectedCategory;
            
            return matchesSearch && matchesCategory;
        });
        
        renderWebsites(filteredWebsites);
    }
});
```

## 运行说明

1. 创建项目目录结构：
```
website-directory/
├── main.py
├── websites.json (会自动创建)
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```

2. 安装依赖：
```bash
pip install fastapi uvicorn
```

3. 运行应用：
```bash
uvicorn main:app --reload
```

4. 在浏览器中访问 http://localhost:8000

## 功能特点

- 响应式设计，适配各种屏幕尺寸
- 支持添加新网址（标题、URL、分类和描述）
- 支持按分类和关键词搜索筛选
- 支持删除网址
- 美观的卡片式布局
- 使用Font Awesome图标增强视觉效果

## 扩展建议

1. 添加用户认证系统，允许不同用户管理自己的网址集合
2. 使用数据库（如SQLite或PostgreSQL）替代JSON文件存储
3. 添加网址收藏和评分功能
4. 实现网址导入/导出功能
5. 添加网址预览功能（缩略图或OG信息抓取）

这个应用提供了完整的网址管理功能，界面简洁美观，使用起来非常直观。您可以根据需要进一步扩展功能。