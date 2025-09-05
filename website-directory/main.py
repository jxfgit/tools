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