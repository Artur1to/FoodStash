const toast = document.querySelector('[data-award-toast]');
const awardList = toast.querySelector('[data-award-list]');
const announcement = document.querySelector('[data-award-announcement]');

toast.querySelector('[data-award-close]').addEventListener('click', () => {
    toast.hidden = true;
    awardList.replaceChildren();
    announcement.textContent = '';
});

document.addEventListener('foodstash:awards', ({detail: awards}) => {
    if (!awards?.length) return;

    for (const award of awards) {
        const item = document.createElement('li');
        const icon = document.createElement('span');
        icon.setAttribute('aria-hidden', 'true');
        icon.textContent = award.icon;
        item.append(icon, ` ${award.name}`);
        awardList.append(item);
    }
    toast.hidden = false;
    announcement.textContent = `Новые достижения. ${awards.map(award => award.name).join(', ')}`;
});
