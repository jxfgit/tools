from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Optional
import json
import uuid

from models import TestCase, TestSuite, TestReport
from test_runner import TestRunner

app = FastAPI(title="API自动化测试工具", version="1.0.0")

# 设置模板和静态文件
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 内存存储测试套件（生产环境应使用数据库）
test_suites = {}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/test-suites")
async def get_test_suites():
    return {"suites": list(test_suites.values())}


@app.post("/test-suites")
async def create_test_suite(suite: TestSuite):
    suite_id = str(uuid.uuid4())
    test_suites[suite_id] = {"id": suite_id, **suite.dict()}
    return {"id": suite_id, "message": "Test suite created successfully"}


@app.get("/test-suites/{suite_id}")
async def get_test_suite(suite_id: str):
    if suite_id not in test_suites:
        raise HTTPException(status_code=404, detail="Test suite not found")
    return test_suites[suite_id]


@app.delete("/test-suites/{suite_id}")
async def delete_test_suite(suite_id: str):
    if suite_id not in test_suites:
        raise HTTPException(status_code=404, detail="Test suite not found")
    del test_suites[suite_id]
    return {"message": "Test suite deleted successfully"}


@app.post("/run-test/{suite_id}")
async def run_test_suite(suite_id: str):
    if suite_id not in test_suites:
        raise HTTPException(status_code=404, detail="Test suite not found")

    suite_data = test_suites[suite_id]
    test_suite = TestSuite(**{k: v for k, v in suite_data.items() if k != 'id'})

    runner = TestRunner()
    report = await runner.execute_test_suite(test_suite)

    return report.dict()


@app.post("/run-single-test")
async def run_single_test(test_case: TestCase):
    runner = TestRunner()
    async with runner:
        result = await runner.execute_test_case(test_case)
    return result.dict()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)