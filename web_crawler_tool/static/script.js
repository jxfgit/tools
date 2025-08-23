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