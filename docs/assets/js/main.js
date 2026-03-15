document.addEventListener('DOMContentLoaded', () => {
    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function formatPublishedDate(value) {
        const text = String(value ?? '').trim();
        if (!text) {
            return '时间未知';
        }

        if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
            return text;
        }

        const parsed = new Date(text);
        if (Number.isNaN(parsed.getTime())) {
            return text;
        }

        return new Intl.DateTimeFormat('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
        }).format(parsed);
    }

    // Set Date
    const dateEl = document.getElementById('current-date');
    const today = new Date().toISOString().split('T')[0];
    dateEl.textContent = `[${today}]`;

    // Load Data
    const listEl = document.getElementById('news-list');

    fetch('data/news.json')
        .then(res => res.json())
        .then(data => {
            if (!data || data.length === 0) {
                listEl.innerHTML = '<li>NO_DATA_FOUND</li>';
                return;
            }

            data.forEach(item => {
                const li = document.createElement('li');
                const publishedLabel = formatPublishedDate(item.published || item.fetched_at);
                li.innerHTML = `
                    <div class="post-meta">
                        <span class="tag">${item.source}</span>
                        <span class="post-date">发布时间 ${escapeHtml(publishedLabel)}</span>
                    </div>
                    <h3>
                        <a class="post-link" href="${item.link}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)}</a>
                    </h3>
                    <div class="post-summary">${escapeHtml(item.summary)}</div>
                `;
                listEl.appendChild(li);
            });
        })
        .catch(err => {
            console.error(err);
            listEl.innerHTML = '<li>SYSTEM_ERROR: LOAD_FAILED</li>';
        });
});
