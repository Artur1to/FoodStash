(() => {
    const editor = document.querySelector('.profile-edit');
    const nicknameStyle = editor.querySelector('#id_nickname_style');
    const nicknamePreview = editor.querySelector('[data-profile-nickname]');
    let nicknameClass = [...nicknamePreview.classList].find(className => className.startsWith('nick-'));

    function updateNicknamePreview() {
        const selectedClass = `nick-${nicknameStyle.value || 'default'}`;
        nicknamePreview.classList.replace(nicknameClass, selectedClass);
        nicknameClass = selectedClass;
    }

    nicknameStyle.addEventListener('change', updateNicknamePreview);
    updateNicknamePreview();

    for (const picker of editor.querySelectorAll('[data-profile-file]')) {
        const input = picker.querySelector('input[type="file"]');
        const clear = picker.querySelector('input[type="checkbox"]');
        const fileName = picker.querySelector('.profile-edit__file-name');
        const reselect = picker.parentElement.querySelector('[data-file-reselect]');
        const image = editor.querySelector(`[data-profile-preview="${picker.dataset.profileFile}"]`);
        const savedSource = image.getAttribute('src');
        let objectUrl;

        function updatePreview() {
            if (objectUrl) URL.revokeObjectURL(objectUrl);

            const file = input.files[0];
            objectUrl = file ? URL.createObjectURL(file) : null;
            const source = clear?.checked ? null : objectUrl || savedSource;
            if (source) {
                image.src = source;
            } else {
                image.removeAttribute('src');
            }
            image.hidden = !source;
            fileName.textContent = file?.name || '';
            if (reselect) reselect.hidden = Boolean(file || clear?.checked);
        }

        image.addEventListener('error', () => {
            image.hidden = true;
        });
        input.addEventListener('change', () => {
            if (clear && input.files.length) clear.checked = false;
            updatePreview();
        });
        clear?.addEventListener('change', () => {
            if (clear.checked) input.value = '';
            updatePreview();
        });
        updatePreview();
    }

    editor.classList.add('profile-edit--enhanced');
})();
