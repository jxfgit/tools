let testCaseCount = 1;

function openTab(tabName) {
    const tabContents = document.getElementsByClassName("tab-content");
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove("active");
    }

    const tabLinks = document.getElementsByClassName("tab-link");
    for (let i = 0; i < tabLinks.length; i++) {
        tabLinks[i].classList.remove("active");
    }

    document.getElementById(tabName).classList.add("active");
    event.currentTarget.classList.add("active");

    if (tabName === 'test-suite') {
        loadTestSuites();
    } else if (tabName === 'test-results') {
        // 可以加载历史测试结果
    }
}

async function runSingleTest() {
    const form = document.getElementById('single-test-form');
    const formData = new FormData(form);

    const testCase = {
        name: formData.get('name'),
        url: formData.get('url'),
        method: formData.get('method'),
        expected_status: parseInt(formData.get('expected_status')),
        headers: formData.get('headers') ? JSON.parse(formData.get('headers')) : {},
        params: formData.get('params') ? JSON.parse(formData.get('params')) : {},
        body: formData.get('body') ? JSON.parse(formData.get('body')) : null
    };

    try {
        const response = await fetch('/run-single-test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testCase)
        });

        const result = await response.json();
        displaySingleTestResult(result);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('single-test-result').innerHTML = `
            <div class="test-result failure">
                <h3>错误</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

function displaySingleTestResult(result) {
    const resultDiv = document.getElementById('single-test-result');
    const success = result.success;

    resultDiv.innerHTML = `
        <div class="test-result ${success ? 'success' : 'failure'}">
            <h3>${result.test_case.name} - ${success ? '通过' : '失败'}</h3>
            <p><strong>URL:</strong> ${result.test_case.url}</p>
            <p><strong>方法:</strong> ${result.test_case.method}</p>
            <p><strong>期望状态码:</strong> ${result.test_case.expected_status}</p>
            <p><strong>实际状态码:</strong> ${result.response_status}</p>
            <p><strong>执行时间:</strong> ${result.execution_time.toFixed(3)} 秒</p>
            ${result.error ? `<p><strong>错误信息:</strong> ${result.error}</p>` : ''}
            <p><strong>响应数据:</strong></p>
            <pre>${JSON.stringify(result.response_data, null, 2)}</pre>
        </div>
    `;
}

function showCreateSuiteForm() {
    document.getElementById('create-suite-form').style.display = 'block';
}

function addTestCase() {
    const testCasesContainer = document.getElementById('suite-test-cases');
    const newTestCase = document.createElement('div');
    newTestCase.className = 'test-case';
    newTestCase.id = `test-case-${testCaseCount}`;

    newTestCase.innerHTML = `
        <h5>测试用例 #${testCaseCount + 1}</h5>
        <div class="form-group">
            <label>名称:</label>
            <input type="text" name="test_cases-${testCaseCount}-name" required>
        </div>
        <div class="form-group">
            <label>URL:</label>
            <input type="url" name="test_cases-${testCaseCount}-url" required>
        </div>
        <div class="form-group">
            <label>方法:</label>
            <select name="test_cases-${testCaseCount}-method">
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
                <option value="PATCH">PATCH</option>
            </select>
        </div>
        <button type="button" onclick="removeTestCase(${testCaseCount})">移除</button>
    `;

    testCasesContainer.appendChild(newTestCase);
    testCaseCount++;
}

function removeTestCase(id) {
    const testCaseElement = document.getElementById(`test-case-${id}`);
    if (testCaseElement) {
        testCaseElement.remove();
    }
}

async function saveTestSuite() {
    const form = document.getElementById('suite-form');
    const formData = new FormData(form);

    const testCases = [];
    for (let i = 0; i < testCaseCount; i++) {
        const name = formData.get(`test_cases-${i}-name`);
        if (!name) continue; // 跳过已删除的测试用例

        testCases.push({
            name: name,
            url: formData.get(`test_cases-${i}-url`),
            method: formData.get(`test_cases-${i}-method`),
            expected_status: 200
        });
    }

    const testSuite = {
        name: formData.get('name'),
        test_cases: testCases,
        variables: {}
    };

    try {
        const response = await fetch('/test-suites', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testSuite)
        });

        const result = await response.json();
        alert('测试套件保存成功!');
        document.getElementById('create-suite-form').style.display = 'none';
        loadTestSuites();
    } catch (error) {
        console.error('Error:', error);
        alert('保存测试套件时出错: ' + error.message);
    }
}

async function loadTestSuites() {
    try {
        const response = await fetch('/test-suites');
        const data = await response.json();
        displayTestSuites(data.suites);
    } catch (error) {
        console.error('Error:', error);
    }
}

function displayTestSuites(suites) {
    const container = document.getElementById('suites-container');

    if (suites.length === 0) {
        container.innerHTML = '<p>暂无测试套件</p>';
        return;
    }

    container.innerHTML = suites.map(suite => `
        <div class="test-suite">
            <h4>${suite.name}</h4>
            <p>包含 ${suite.test_cases.length} 个测试用例</p>
            <button onclick="runTestSuite('${suite.id}')">运行测试套件</button>
            <button onclick="deleteTestSuite('${suite.id}')">删除</button>
        </div>
    `).join('');
}

async function runTestSuite(suiteId) {
    try {
        const response = await fetch(`/run-test/${suiteId}`, {
            method: 'POST'
        });

        const report = await response.json();
        displayTestReport(report);
        openTab('test-results');
    } catch (error) {
        console.error('Error:', error);
        alert('运行测试套件时出错: ' + error.message);
    }
}

function displayTestReport(report) {
    const container = document.getElementById('results-container');

    container.innerHTML = `
        <h3>测试报告: ${report.suite_name}</h3>
        <p>总测试数: ${report.total_tests} | 通过: <span class="success">${report.passed_tests}</span> | 失败: <span class="failure">${report.failed_tests}</span></p>
        <p>总执行时间: ${report.execution_time.toFixed(3)} 秒</p>
        
        <h4>详细结果:</h4>
        ${report.results.map(result => `
            <div class="test-result ${result.success ? 'success' : 'failure'}">
                <h5>${result.test_case.name} - ${result.success ? '通过' : '失败'}</h5>
                <p><strong>URL:</strong> ${result.test_case.url}</p>
                <p><strong>方法:</strong> ${result.test_case.method}</p>
                <p><strong>期望状态码:</strong> ${result.test_case.expected_status}</p>
                <p><strong>实际状态码:</strong> ${result.response_status}</p>
                <p><strong>执行时间:</strong> ${result.execution_time.toFixed(3)} 秒</p>
                ${result.error ? `<p><strong>错误信息:</strong> ${result.error}</p>` : ''}
                ${result.response_data ? `<p><strong>响应数据:</strong></p><pre>${JSON.stringify(result.response_data, null, 2)}</pre>` : ''}
            </div>
        `).join('')}
    `;
}

async function deleteTestSuite(suiteId) {
    if (!confirm('确定要删除这个测试套件吗?')) return;

    try {
        await fetch(`/test-suites/${suiteId}`, {
            method: 'DELETE'
        });

        loadTestSuites();
    } catch (error) {
        console.error('Error:', error);
        alert('删除测试套件时出错: ' + error.message);
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 默认打开第一个标签页
    document.querySelector('.tab-link.active').click();
});