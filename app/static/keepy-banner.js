(function() {
    // Keepy Emergency Banner Script
    // Usage: <script src="https://<keepy-server>/static/keepy-banner.js" data-site-id="YOUR_SITE_ID"></script>

    const scriptTag = document.currentScript;
    const siteId = scriptTag.getAttribute('data-site-id');

    // API 주소: 이 스크립트를 불러온 Keepy 서버의 origin을 쓴다.
    // (과거엔 미지정 시 '고객 병원 사이트'의 origin으로 호출해 항상 404 — 기본 설치가 동작하지 않았다)
    const apiBase = scriptTag.getAttribute('data-api-base');
    const baseUrl = apiBase || new URL(scriptTag.src).origin;

    // siteId에 이미 쿼리스트링이 포함되어 있을 경우를 고려하여 처리
    let apiUrl;
    if (siteId && siteId.includes('?')) {
        const [id, query] = siteId.split('?');
        apiUrl = `${baseUrl}/api/sites/public/${id}/banner?${query}`;
    } else {
        apiUrl = `${baseUrl}/api/sites/public/${siteId}/banner`;
    }

    function renderBanner(message) {
        if (document.getElementById('keepy-emergency-banner')) return;

        const banner = document.createElement('div');
        banner.id = 'keepy-emergency-banner';
        banner.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background-color: #f1c40f;
            color: #2c3e50;
            text-align: center;
            padding: 12px 20px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 14px;
            font-weight: 600;
            z-index: 2147483647;
            box-shadow: 0 2px 15px rgba(0,0,0,0.15);
            display: flex;
            justify-content: center;
            align-items: center;
            line-height: 1.4;
            border-bottom: 2px solid #d4ac0d;
            transition: all 0.3s ease;
        `;

        const content = document.createElement('div');
        content.style.maxWidth = '1000px';
        const icon = document.createElement('span');
        icon.style.marginRight = '8px';
        icon.textContent = '📢';
        const text = document.createElement('span');
        text.textContent = message; // textContent: 메시지에 태그가 섞여도 스크립트로 실행되지 않게
        content.appendChild(icon);
        content.appendChild(text);

        banner.appendChild(content);

        // 최상단에 추가
        document.body.prepend(banner);

        // 페이지 상단 여백 조정 (기존 레이아웃 깨짐 방지)
        const updatePadding = () => {
            document.body.style.marginTop = banner.offsetHeight + 'px';
        };
        updatePadding();
        window.addEventListener('resize', updatePadding);
    }

    // 서버에서 상태 확인
    if (siteId) {
        fetch(apiUrl)
            .then(res => res.json())
            .then(data => {
                if (data.active) {
                    // DOM이 로드된 후 실행
                    if (document.readyState === 'loading') {
                        document.addEventListener('DOMContentLoaded', () => renderBanner(data.message));
                    } else {
                        renderBanner(data.message);
                    }
                }
            })
            .catch(err => console.error('[Keepy] Failed to fetch banner status:', err));
    }
})();
