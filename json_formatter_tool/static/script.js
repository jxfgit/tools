document.addEventListener('DOMContentLoaded', function() {
    const jsonInput = document.getElementById('jsonInput');
    const output = document.getElementById('output');
    const errorDiv = document.getElementById('error');
    const formatBtn = document.getElementById('formatBtn');
    const minifyBtn = document.getElementById('minifyBtn');
    const validateBtn = document.getElementById('validateBtn');
    const convertBtn = document.getElementById('convertBtn');
    const clearBtn = document.getElementById('clearBtn');
    const indentSelect = document.getElementById('indent');
    const conversionTypeSelect = document.getElementById('conversionType');

    // 格式化按钮点击事件
    formatBtn.addEventListener('click', async function() {
        const jsonText = jsonInput.value.trim();
        if (!jsonText) {
            showError('请输入 JSON 数据');
            return;
        }

        try {
            const indentValue = indentSelect.value === 'tab' ? '\t' : parseInt(indentSelect.value);
            const response = await fetch('/format', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    json_input: jsonText,
                    indent: indentValue
                })
            });

            const data = await response.json();

            if (data.success) {
                showOutput(data.formatted_json, '格式化成功');
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('请求失败: ' + error.message);
        }
    });

    // 压缩按钮点击事件
    minifyBtn.addEventListener('click', async function() {
        const jsonText = jsonInput.value.trim();
        if (!jsonText) {
            showError('请输入 JSON 数据');
            return;
        }

        try {
            const response = await fetch('/minify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    json_input: jsonText
                })
            });

            const data = await response.json();

            if (data.success) {
                showOutput(data.minified_json, '压缩成功');
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('请求失败: ' + error.message);
        }
    });

    // 验证按钮点击事件
    validateBtn.addEventListener('click', async function() {
        const jsonText = jsonInput.value.trim();
        if (!jsonText) {
            showError('请输入 JSON 数据');
            return;
        }

        try {
            const response = await fetch('/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    json_input: jsonText
                })
            });

            const data = await response.json();

            if (data.success) {
                showOutput(jsonText, data.message);
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('请求失败: ' + error.message);
        }
    });

    // 转换按钮点击事件
    convertBtn.addEventListener('click', async function() {
        const jsonText = jsonInput.value.trim();
        if (!jsonText) {
            showError('请输入 JSON 数据');
            return;
        }

        try {
            const response = await fetch('/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    json_input: jsonText,
                    conversion_type: conversionTypeSelect.value
                })
            });

            const data = await response.json();

            if (data.success) {
                showOutput(data.converted, data.message);
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('请求失败: ' + error.message);
        }
    });

    // 清空按钮点击事件
    clearBtn.addEventListener('click', function() {
        jsonInput.value = '';
        output.textContent = '';
        hideError();
    });

    // 显示输出
    function showOutput(content, message) {
        output.textContent = content;
        hideError();

        // 显示成功消息
        const successMsg = document.createElement('div');
        successMsg.className = 'success';
        successMsg.textContent = message;
        output.parentNode.insertBefore(successMsg, output.nextSibling);

        // 3秒后移除成功消息
        setTimeout(() => {
            if (successMsg.parentNode) {
                successMsg.parentNode.removeChild(successMsg);
            }
        }, 3000);
    }

    // 显示错误
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        output.textContent = '';
    }

    // 隐藏错误
    function hideError() {
        errorDiv.classList.add('hidden');
    }

    // 示例 JSON
    const exampleJson = `{
  "name": "JSON 格式化工具",
  "version": "1.0.0",
  "description": "一个用于格式化、验证和转换 JSON 数据的工具",
  "features": [
    "格式化",
    "压缩",
    "验证",
    "转换为其他格式"
  ],
  "author": {
    "name": "开发者",
    "email": "developer@example.com"
  }
}`;

    // 设置示例 JSON
    jsonInput.value = exampleJson;
});