// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 添加网址表单验证
    const addForm = document.querySelector('.add-site-section form');
    if (addForm) {
        addForm.addEventListener('submit', function(e) {
            const urlInput = addForm.querySelector('input[type="url"]');
            if (urlInput.value && !urlInput.value.startsWith('http://') && !urlInput.value.startsWith('https://')) {
                e.preventDefault();
                alert('网址必须以 http:// 或 https:// 开头');
                urlInput.focus();
            }
        });
    }

    // 搜索框增强功能
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        // 保存搜索历史到本地存储
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                const searchQuery = searchInput.value.trim();
                if (searchQuery) {
                    saveSearchHistory(searchQuery);
                }
            }
        });

        // 显示搜索建议（可选功能）
        searchInput.addEventListener('input', debounce(function() {
            const query = searchInput.value.trim();
            if (query.length > 2) {
                showSearchSuggestions(query);
            }
        }, 300));
    }

    // 初始化显示搜索历史
    displaySearchHistory();
});

// 保存搜索历史
function saveSearchHistory(query) {
    let history = JSON.parse(localStorage.getItem('searchHistory') || '[]');

    // 避免重复
    history = history.filter(item => item !== query);

    // 添加到开头
    history.unshift(query);

    // 限制历史记录数量
    if (history.length > 10) {
        history = history.slice(0, 10);
    }

    localStorage.setItem('searchHistory', JSON.stringify(history));
}

// 显示搜索历史
function displaySearchHistory() {
    const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
    if (history.length > 0) {
        // 这里可以实现在搜索框下方显示历史记录
        console.log('搜索历史:', history);
    }
}

// 显示搜索建议（需要后端API支持，这里是前端示例）
function showSearchSuggestions(query) {
    console.log('正在搜索:', query);
    // 实际应用中这里可以发送请求到后端获取建议
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this, args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func.apply(context, args);
        }, wait);
    };
}

// 复制网址功能（可选增强功能）
function copyUrl(url) {
    navigator.clipboard.writeText(url).then(() => {
        alert('网址已复制到剪贴板');
    }).catch(err => {
        console.error('无法复制网址:', err);
    });
}