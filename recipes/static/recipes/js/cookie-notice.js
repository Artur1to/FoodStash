(() => {
    const key = 'foodstash_cookie_notice';
    const notice = document.querySelector('[data-cookie-notice]');
    const acknowledged = document.cookie.split(';').some(cookie => cookie.trim() === `${key}=1`);
    try {
        if (localStorage.getItem(key) === '1' || acknowledged) return;
    } catch {
        if (acknowledged) return;
    }

    notice.hidden = false;
    notice.querySelector('[data-dismiss-cookie-notice]').addEventListener('click', () => {
        try {
            localStorage.setItem(key, '1');
        } catch {
            const secure = location.protocol === 'https:' ? '; Secure' : '';
            document.cookie = `${key}=1; Path=/; Max-Age=31536000; SameSite=Lax${secure}`;
        }
        notice.hidden = true;
    });
})();
