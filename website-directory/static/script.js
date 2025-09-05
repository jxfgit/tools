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