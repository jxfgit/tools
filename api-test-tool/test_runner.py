import asyncio
import aiohttp
import json
from datetime import datetime
from models import TestCase, TestResult, TestSuite, TestReport


class TestRunner:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def execute_test_case(self, test_case: TestCase) -> TestResult:
        start_time = datetime.now()
        try:
            async with self.session.request(
                    method=test_case.method,
                    url=test_case.url,
                    headers=test_case.headers,
                    params=test_case.params,
                    json=test_case.body,
                    timeout=test_case.timeout
            ) as response:
                response_status = response.status
                response_data = await response.json() if response.headers.get(
                    'content-type') == 'application/json' else await response.text()

                success = response_status == test_case.expected_status
                if test_case.expected_response:
                    success = success and self._check_expected_response(response_data, test_case.expected_response)

                error = None if success else f"Expected status {test_case.expected_status}, got {response_status}"

        except Exception as e:
            response_status = 0
            response_data = None
            success = False
            error = str(e)

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        return TestResult(
            test_case=test_case,
            success=success,
            response_status=response_status,
            response_data=response_data,
            error=error,
            execution_time=execution_time
        )

    def _check_expected_response(self, actual_response, expected_response):
        # 简单的响应检查，可以根据需要扩展
        if isinstance(expected_response, dict):
            for key, value in expected_response.items():
                if key not in actual_response or actual_response[key] != value:
                    return False
        return True

    async def execute_test_suite(self, test_suite: TestSuite) -> TestReport:
        start_time = datetime.now()

        async with self:
            results = []
            for test_case in test_suite.test_cases:
                result = await self.execute_test_case(test_case)
                results.append(result)

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        passed_tests = sum(1 for result in results if result.success)
        failed_tests = len(results) - passed_tests

        return TestReport(
            suite_name=test_suite.name,
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            results=results,
            execution_time=execution_time
        )