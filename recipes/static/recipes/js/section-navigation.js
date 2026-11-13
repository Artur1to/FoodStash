(() => {
    const page = document.querySelector('[data-ajax-page]');
    if (!page) return;

    const regions = page.hasAttribute('data-ajax-region') ? [page] : [...page.querySelectorAll('[data-ajax-region]')];
    const status = document.createElement('p');
    status.className = 'section-update-status';
    status.setAttribute('role', 'status');
    page.before(status);

    const pagePath = location.pathname;
    let renderedQuery = location.search;
    let pending;

    function canUpdate(url) {
        return url.origin === location.origin && url.pathname === pagePath && !url.hash;
    }

    async function update(url, trigger = null) {
        pending?.abort();
        const controller = new AbortController();
        pending = controller;
        status.classList.remove('section-update-status--error');
        status.textContent = 'Загрузка…';
        page.setAttribute('aria-busy', 'true');

        try {
            const response = await fetch(url, {
                headers: {'X-FoodStash-Fragment': '1'},
                signal: controller.signal,
            });
            if (response.redirected) {
                location.assign(response.url);
                return;
            }
            if (!response.ok) throw new Error('Request failed');

            const template = document.createElement('template');
            template.innerHTML = await response.text();
            const fragment = template.content.getElementById(page.id);
            const replacements = regions.map(region => region === page ? fragment
                : fragment?.querySelector(`[data-ajax-region="${region.dataset.ajaxRegion}"]`));
            if (replacements.some(replacement => !replacement)) throw new Error('Missing page section');
            if (controller.signal.aborted) return;

            const focus = document.activeElement;
            const focusHref = focus.closest('[data-ajax-link]')?.getAttribute('href');
            const moveToResults = trigger?.dataset.ajaxFocus;
            const focusedId = focus.id;
            const openFilters = trigger?.matches('[data-ajax-form]') && trigger.closest('details[open]');
            if (trigger && url.href !== location.href) history.pushState(null, '', url);

            regions.forEach((region, index) => {
                region.replaceChildren(...replacements[index].childNodes);
            });
            renderedQuery = url.search;

            if (openFilters) {
                const filters = document.getElementById(openFilters.id);
                if (filters) filters.open = true;
            }
            if (moveToResults) {
                document.getElementById(moveToResults)?.focus();
            } else if (!focus.isConnected) {
                const matchingLink = focusHref && [...page.querySelectorAll('[data-ajax-link]')]
                    .find(link => link.getAttribute('href') === focusHref);
                const replacement = (focusedId && document.getElementById(focusedId)) || matchingLink;
                replacement?.focus({preventScroll: true});
            }
            status.textContent = 'Раздел обновлён.';
        } catch {
            if (controller.signal.aborted) return;
            if (!trigger) {
                location.reload();
                return;
            }
            status.textContent = 'Не удалось обновить раздел. Повтори действие.';
            status.classList.add('section-update-status--error');
        } finally {
            if (pending === controller) {
                pending = null;
                page.removeAttribute('aria-busy');
            }
        }
    }

    page.addEventListener('click', event => {
        const link = event.target.closest('[data-ajax-link]');
        if (!link || event.defaultPrevented || event.button !== 0
            || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;

        const url = new URL(link.href);
        if (!canUpdate(url)) return;

        event.preventDefault();
        update(url, link);
    });

    page.addEventListener('submit', event => {
        const form = event.target;
        if (!form.matches('[data-ajax-form]') || event.defaultPrevented) return;

        const url = new URL(form.action);
        if (!canUpdate(url)) return;

        event.preventDefault();
        url.search = new URLSearchParams(new FormData(form, event.submitter));
        update(url, form);
    });

    window.addEventListener('popstate', () => {
        if (location.pathname !== pagePath) return;
        if (location.search !== renderedQuery) {
            update(new URL(location.href));
        } else if (pending) {
            pending.abort();
            status.textContent = '';
        }
    });
})();
