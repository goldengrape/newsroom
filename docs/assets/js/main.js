document.addEventListener("DOMContentLoaded", () => {
    const FEEDBACK_STORAGE_KEY = "newsroom.feedback.v1";

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function formatPublishedDate(value) {
        const text = String(value ?? "").trim();
        if (!text) {
            return "时间未知";
        }

        if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
            return text;
        }

        const parsed = new Date(text);
        if (Number.isNaN(parsed.getTime())) {
            return text;
        }

        return new Intl.DateTimeFormat("zh-CN", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
        }).format(parsed);
    }

    function normalizeFeedbackDate(value) {
        const text = String(value ?? "").trim();
        if (!text) {
            return new Date().toISOString().slice(0, 10);
        }

        const rawDateMatch = text.match(/^(\d{4}-\d{2}-\d{2})/);
        if (rawDateMatch) {
            return rawDateMatch[1];
        }

        const parsed = new Date(text);
        if (Number.isNaN(parsed.getTime())) {
            return new Date().toISOString().slice(0, 10);
        }
        return parsed.toISOString().slice(0, 10);
    }

    function loadFeedbackMap() {
        try {
            const raw = window.localStorage.getItem(FEEDBACK_STORAGE_KEY);
            if (!raw) {
                return {};
            }

            const parsed = JSON.parse(raw);
            return parsed && typeof parsed === "object" ? parsed : {};
        } catch (error) {
            console.error("Failed to load feedback from localStorage.", error);
            return {};
        }
    }

    function saveFeedbackMap(feedbackMap) {
        try {
            window.localStorage.setItem(
                FEEDBACK_STORAGE_KEY,
                JSON.stringify(feedbackMap, null, 2),
            );
        } catch (error) {
            console.error("Failed to save feedback to localStorage.", error);
        }
    }

    function buildFeedbackKey(item) {
        const feedbackDate = normalizeFeedbackDate(item.published || item.fetched_at);
        return `${feedbackDate}::${item.title}`;
    }

    function exportFeedback(feedbackMap) {
        const payload = Object.values(feedbackMap).sort((left, right) => {
            const leftKey = `${left.date}::${left.title}`;
            const rightKey = `${right.date}::${right.title}`;
            return leftKey.localeCompare(rightKey, "zh-CN");
        });
        const blob = new Blob([JSON.stringify(payload, null, 2)], {
            type: "application/json;charset=utf-8",
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        const today = new Date().toISOString().slice(0, 10);

        link.href = url;
        link.download = `feedback-${today}.json`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    }

    function updateToolbar(feedbackMap, countEl, exportBtn) {
        const count = Object.keys(feedbackMap).length;
        countEl.textContent = count > 0 ? `已记录 ${count} 条反馈` : "尚无反馈";
        exportBtn.disabled = count === 0;
    }

    function updateFeedbackState(cardEl, result) {
        const buttons = cardEl.querySelectorAll(".feedback-button");
        const statusEl = cardEl.querySelector(".feedback-status");

        buttons.forEach((button) => {
            button.classList.toggle("active", button.dataset.result === result);
        });

        if (!statusEl) {
            return;
        }

        if (result === "like") {
            statusEl.textContent = "已反馈：喜欢";
        } else if (result === "dislike") {
            statusEl.textContent = "已反馈：不喜欢";
        } else {
            statusEl.textContent = "未反馈";
        }
    }

    const dateEl = document.getElementById("current-date");
    const listEl = document.getElementById("news-list");
    const exportBtn = document.getElementById("export-feedback");
    const feedbackCountEl = document.getElementById("feedback-count");
    const feedbackMap = loadFeedbackMap();

    dateEl.textContent = `[${new Date().toISOString().split("T")[0]}]`;
    updateToolbar(feedbackMap, feedbackCountEl, exportBtn);

    exportBtn.addEventListener("click", () => {
        exportFeedback(feedbackMap);
    });

    fetch("data/news.json")
        .then((res) => res.json())
        .then((data) => {
            if (!data || data.length === 0) {
                listEl.innerHTML = "<li>NO_DATA_FOUND</li>";
                return;
            }

            data.forEach((item) => {
                const li = document.createElement("li");
                const publishedLabel = formatPublishedDate(item.published || item.fetched_at);
                const feedbackKey = buildFeedbackKey(item);
                const storedFeedback = feedbackMap[feedbackKey]?.result || "";

                li.innerHTML = `
                    <div class="post-meta">
                        <span class="tag">${escapeHtml(item.source)}</span>
                        <span class="post-date">发布时间 ${escapeHtml(publishedLabel)}</span>
                    </div>
                    <h3>
                        <a class="post-link" href="${item.link}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)}</a>
                    </h3>
                    <div class="post-summary">${escapeHtml(item.summary)}</div>
                    <div class="feedback-row">
                        <div class="feedback-buttons">
                            <button class="feedback-button" type="button" data-result="like">👍 喜欢</button>
                            <button class="feedback-button" type="button" data-result="dislike">👎 不喜欢</button>
                        </div>
                        <span class="feedback-status">未反馈</span>
                    </div>
                `;

                li.querySelectorAll(".feedback-button").forEach((button) => {
                    button.addEventListener("click", () => {
                        const nextResult = button.dataset.result;
                        const currentResult = feedbackMap[feedbackKey]?.result;

                        if (currentResult === nextResult) {
                            delete feedbackMap[feedbackKey];
                            updateFeedbackState(li, "");
                        } else {
                            feedbackMap[feedbackKey] = {
                                date: normalizeFeedbackDate(item.published || item.fetched_at),
                                title: item.title,
                                result: nextResult,
                            };
                            updateFeedbackState(li, nextResult);
                        }

                        saveFeedbackMap(feedbackMap);
                        updateToolbar(feedbackMap, feedbackCountEl, exportBtn);
                    });
                });

                updateFeedbackState(li, storedFeedback);
                listEl.appendChild(li);
            });
        })
        .catch((error) => {
            console.error(error);
            listEl.innerHTML = "<li>SYSTEM_ERROR: LOAD_FAILED</li>";
        });
});
