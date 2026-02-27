document.addEventListener('DOMContentLoaded', () => {
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
                li.innerHTML = `
                    <span class="post-meta">
                        <span class="tag">${item.source}</span>
                    </span>
                    <h3>
                        <a class="post-link" href="${item.link}" target="_blank">${item.title}</a>
                    </h3>
                    <div class="post-summary">${item.summary}</div>
                `;
                listEl.appendChild(li);
            });
        })
        .catch(err => {
            console.error(err);
            listEl.innerHTML = '<li>SYSTEM_ERROR: LOAD_FAILED</li>';
        });
});
