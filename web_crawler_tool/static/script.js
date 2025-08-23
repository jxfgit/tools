document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('crawlForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const crawlBtn = document.getElementById('crawlBtn');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const url = document.getElementById('url').value;
        const dataType = document.getElementById('dataType').value;
        const depth = document.getElementById('depth').value;
        const maxPages = document.getElementById('maxPages').value;

        // 显示加载状态，隐藏结果和错误
        loading.classList.remove('hidden');
        results.classList.add('hidden');
        errorDiv.classList.add('hidden');
        crawlBtn.disabled = true;

        try {
            const formData = new FormData();
            formData.append('url', url);
            formData.append('dataType', dataType);
            formData.append('depth', depth);
            formData.append('maxPages', maxPages);

            const response = await fetch('/crawl', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                displayResults(data);
            } else {
                showError(data.error || 'An unknown error occurred');
            }
        } catch (error) {
            showError('Network error: ' + error.message);
        } finally {
            loading.classList.add('hidden');
            crawlBtn.disabled = false;
        }
    });

    function displayResults(data) {
        document.getElementById('pagesCount').textContent = data.pages_crawled;
        document.getElementById('timeTaken').textContent = data.time_taken;

        const resultsContent = document.getElementById('resultsContent');
        resultsContent.innerHTML = '';

        if (data.pages_crawled === 0) {
            resultsContent.innerHTML = '<p class="error">No data could be extracted from the provided URL.</p>';
            results.classList.remove('hidden');
            return;
        }

        for (const [url, pageData] of Object.entries(data.results)) {
            const pageDiv = document.createElement('div');
            pageDiv.className = 'page-result';

            const urlHeading = document.createElement('a');
            urlHeading.className = 'page-url';
            urlHeading.href = url;
            urlHeading.target = '_blank';
            urlHeading.textContent = url;
            pageDiv.appendChild(urlHeading);

            // 根据数据类型显示不同内容
            if (pageData.links) {
                const linksHeading = document.createElement('h3');
                linksHeading.textContent = 'Links found:';
                pageDiv.appendChild(linksHeading);

                pageData.links.forEach(link => {
                    const linkDiv = document.createElement('div');
                    linkDiv.className = 'data-item';

                    const linkEl = document.createElement('a');
                    linkEl.href = link.url;
                    linkEl.target = '_blank';
                    linkEl.textContent = link.text || link.url;

                    linkDiv.appendChild(linkEl);
                    pageDiv.appendChild(linkDiv);
                });
            }

            if (pageData.images) {
                const imagesHeading = document.createElement('h3');
                imagesHeading.textContent = 'Images found:';
                pageDiv.appendChild(imagesHeading);

                pageData.images.forEach(image => {
                    const imgDiv = document.createElement('div');
                    imgDiv.className = 'data-item';

                    const imgEl = document.createElement('img');
                    imgEl.src = image.src;
                    imgEl.alt = image.alt;
                    imgEl.style.maxWidth = '100%';
                    imgEl.style.height = 'auto';

                    const altText = document.createElement('p');
                    altText.textContent = `Alt text: ${image.alt || 'None'}`;

                    imgDiv.appendChild(imgEl);
                    imgDiv.appendChild(altText);
                    pageDiv.appendChild(imgDiv);
                });
            }

            if (pageData.text) {
                const textHeading = document.createElement('h3');
                textHeading.textContent = 'Text content:';
                pageDiv.appendChild(textHeading);

                const textDiv = document.createElement('div');
                textDiv.className = 'data-item';
                textDiv.textContent = pageData.text.length > 500 ?
                    pageData.text.substring(0, 500) + '...' :
                    pageData.text;
                pageDiv.appendChild(textDiv);
            }

            if (pageData.metadata) {
                const metaHeading = document.createElement('h3');
                metaHeading.textContent = 'Metadata:';
                pageDiv.appendChild(metaHeading);

                const metaDiv = document.createElement('div');
                metaDiv.className = 'data-item';

                for (const [key, value] of Object.entries(pageData.metadata)) {
                    const metaItem = document.createElement('p');
                    metaItem.innerHTML = `<strong>${key}:</strong> ${value || 'Not specified'}`;
                    metaDiv.appendChild(metaItem);
                }

                pageDiv.appendChild(metaDiv);
            }

            resultsContent.appendChild(pageDiv);
        }

        results.classList.remove('hidden');
    }

    function showError(message) {
        errorDiv.classList.remove('hidden');
        document.getElementById('errorMessage').textContent = message;
    }
});