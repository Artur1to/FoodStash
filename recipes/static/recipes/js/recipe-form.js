(() => {
    const form = document.querySelector('.recipe-form');
    const ingredients = form.querySelector('[data-ingredient-list]');
    const addIngredient = form.querySelector('[data-add-ingredient]');
    const ingredientTemplate = document.querySelector('[data-ingredient-template]');
    const totalForms = form.elements.namedItem(ingredients.dataset.ingredientList + '-TOTAL_FORMS');
    const initialForms = Number(form.elements.namedItem(ingredients.dataset.ingredientList + '-INITIAL_FORMS').value);

    function hideIngredient(row) {
        row.hidden = true;
        for (const input of row.querySelectorAll('.form-input')) input.disabled = true;
    }

    function visibleIngredients() {
        return [...ingredients.querySelectorAll('.recipe-ingredient:not([hidden])')];
    }

    let hasVisibleIngredient = false;
    for (const row of ingredients.children) {
        const deleted = row.querySelector('input[type="checkbox"]').checked;
        const hasValue = [...row.querySelectorAll('.form-input')].some(input => input.value);
        if (deleted || (hasVisibleIngredient && !hasValue && !row.querySelector('.errorlist'))) {
            hideIngredient(row);
        } else {
            hasVisibleIngredient = true;
        }
    }

    addIngredient.addEventListener('click', () => {
        const last = visibleIngredients().at(-1);
        // Deleted existing rows must keep their IDs in the submission.
        const firstAvailableIndex = Math.max(initialForms, last ? Number(last.dataset.ingredientIndex) + 1 : 0);
        const slot = [...ingredients.children].find(row => row.hidden && Number(row.dataset.ingredientIndex) >= firstAvailableIndex);
        const index = slot?.dataset.ingredientIndex ?? totalForms.value;
        const row = ingredientTemplate.content.firstElementChild.cloneNode(true);
        row.dataset.ingredientIndex = index;

        for (const element of row.querySelectorAll('[name], [id], [for]')) {
            for (const attribute of ['name', 'id', 'for']) {
                const value = element.getAttribute(attribute);
                if (value) element.setAttribute(attribute, value.replace('__prefix__', index));
            }
        }

        if (slot) {
            slot.replaceWith(row);
        } else {
            ingredients.append(row);
            totalForms.value = Number(totalForms.value) + 1;
        }
        row.querySelector('select').focus();
    });

    ingredients.addEventListener('click', event => {
        const remove = event.target.closest('[data-remove-ingredient]');
        if (!remove) return;

        const row = remove.closest('.recipe-ingredient');
        const rows = visibleIngredients();
        const index = rows.indexOf(row);
        row.querySelector('input[type="checkbox"]').checked = true;
        hideIngredient(row);

        const next = rows[index + 1] || rows[index - 1];
        (next?.querySelector('select') || addIngredient).focus();
    });

    const photo = form.querySelector('.recipe-photo');
    const photoInput = photo.querySelector('input[type="file"]');
    const preview = photo.querySelector('[data-photo-preview]');
    const photoName = photo.querySelector('[data-photo-name]');
    const choosePhoto = photo.querySelector('.recipe-photo__choose');
    const removePhoto = photo.querySelector('[data-remove-photo]');
    const reselectHint = photo.querySelector('[data-file-reselect]');
    const savedPhoto = preview.getAttribute('src');
    let photoUrl;

    function updatePhoto() {
        if (photoUrl) URL.revokeObjectURL(photoUrl);

        const file = photoInput.files[0];
        photoUrl = file ? URL.createObjectURL(file) : null;
        const src = photoUrl || savedPhoto;
        if (src) {
            if (preview.getAttribute('src') !== src) preview.src = src;
        } else {
            preview.removeAttribute('src');
        }
        preview.hidden = !src || (preview.complete && !preview.naturalWidth);
        photoName.textContent = file?.name || '';
        choosePhoto.textContent = file || savedPhoto ? 'Заменить фото' : 'Выбрать фото';
        removePhoto.hidden = !file;
        if (reselectHint) reselectHint.hidden = Boolean(file);
    }

    preview.addEventListener('load', () => { preview.hidden = false; });
    preview.addEventListener('error', () => { preview.hidden = true; });
    photoInput.addEventListener('change', updatePhoto);
    removePhoto.addEventListener('click', () => {
        photoInput.value = '';
        updatePhoto();
        photoInput.focus();
    });
    updatePhoto();

    addIngredient.hidden = false;
    form.classList.add('recipe-form--enhanced');
})();
