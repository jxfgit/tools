from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from enum import Enum

class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

class TestCase(BaseModel):
    name: str
    url: str
    method: HTTPMethod = HTTPMethod.GET
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    body: Optional[Any] = None
    expected_status: int = 200
    expected_response: Optional[Dict[str, Any]] = None
    timeout: int = 10

class TestSuite(BaseModel):
    name: str
    test_cases: List[TestCase]
    variables: Optional[Dict[str, Any]] = None

class TestResult(BaseModel):
    test_case: TestCase
    success: bool
    response_status: int
    response_data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float

class TestReport(BaseModel):
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    results: List[TestResult]
    execution_time: float