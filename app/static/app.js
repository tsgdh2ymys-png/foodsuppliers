// Плавающая панель сравнения на странице каталога.
// Запоминает выбор в sessionStorage, чтобы он не терялся при пагинации/фильтрах.
(function () {
  const boxes = document.querySelectorAll('input.cmp');
  if (!boxes.length) return;

  const KEY = 'cmp_ids';
  const bar = document.getElementById('compare-bar');
  const countEl = document.getElementById('cmp-count');
  const goEl = document.getElementById('cmp-go');
  const clearEl = document.getElementById('cmp-clear');

  const load = () => {
    try { return new Set(JSON.parse(sessionStorage.getItem(KEY) || '[]')); }
    catch (e) { return new Set(); }
  };
  const save = (set) => sessionStorage.setItem(KEY, JSON.stringify([...set]));

  let selected = load();

  function syncUI() {
    countEl.textContent = selected.size;
    goEl.href = '/compare?ids=' + [...selected].join(',');
    bar.classList.toggle('translate-y-full', selected.size === 0);
    // дизейблим лишние чекбоксы при достижении лимита (макс. 4 для читаемого сравнения)
    boxes.forEach(b => {
      const id = +b.value;
      b.checked = selected.has(id);
      b.disabled = !b.checked && selected.size >= 4;
    });
  }

  boxes.forEach(b => {
    b.addEventListener('change', () => {
      const id = +b.value;
      if (b.checked) selected.add(id); else selected.delete(id);
      save(selected);
      syncUI();
    });
  });

  clearEl?.addEventListener('click', () => {
    selected = new Set();
    save(selected);
    syncUI();
  });

  syncUI();
})();
