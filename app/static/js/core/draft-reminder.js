let generation = 0;
let checked = false;
let bellContext = null;
export async function ringDraftBell(count = 1, userAction = false) {
  const Audio = globalThis.AudioContext || globalThis.webkitAudioContext;
  if (!Audio) return;
  const session = generation;
  try {
    if (!bellContext || bellContext.state === 'closed') bellContext = new Audio();
    const context = bellContext;
    // Ne pas mettre un son d'apparition en attente pour un clic ultérieur.
    if (context.state !== 'running') {
      if (!userAction) return;
      await context.resume();
    }
    if (session !== generation || context.state !== 'running') return;
    for (let strike = 0; strike < count; strike += 1) {
      const start = context.currentTime + strike * .45;
      // Partiels doux et décroissants : timbre de cloche, volume modéré.
      for (const [frequency, volume] of [[880,.07],[1760,.035],[2450,.015]]) {
        const oscillator = context.createOscillator();
        const gain = context.createGain();
        oscillator.type = 'sine';
        oscillator.frequency.value = frequency;
        gain.gain.setValueAtTime(.0001, start);
        gain.gain.exponentialRampToValueAtTime(volume, start + .01);
        gain.gain.exponentialRampToValueAtTime(.0001, start + 1.1);
        oscillator.connect(gain);
        gain.connect(context.destination);
        oscillator.start(start);
        oscillator.stop(start + 1.15);
        oscillator.onended = () => { oscillator.disconnect(); gain.disconnect(); };
      }
    }
  } catch (_) { /* Le rappel et la navigation restent utilisables sans audio. */ }
}
export function clearDraftReminder() {
  generation += 1;
  checked = false;
  bellContext?.close().catch(() => {});
  bellContext = null;
  document.querySelector('#collectionDraftReminder')?.remove();
}
export async function showDraftReminder(apiGet) {
  if (checked) return;
  checked = true;
  const request = ++generation;
  try {
    const result = await apiGet('/api/v1/collectes/mes-brouillons');
    if (request !== generation || !result.total) return;
    const notice = document.createElement('aside');
    notice.id = 'collectionDraftReminder';
    notice.className = 'collection-draft-reminder';
    notice.setAttribute('role', 'status');
    notice.innerHTML = '<span class="draft-bell" aria-hidden="true">🔔</span><div><strong></strong><p>Reprenez votre saisie avant de soumettre la fiche.</p><div class="draft-links"></div></div>';
    notice.querySelector('strong').textContent = result.total === 1
      ? 'Vous avez une collecte enregistrée en brouillon.'
      : `Vous avez ${result.total} collectes enregistrées en brouillon.`;
    for (const item of result.items) {
      const link = document.createElement('a');
      link.href = `#/collectes/modifier/${encodeURIComponent(item.mission_id)}/${encodeURIComponent(item.fiche_id)}`;
      link.textContent = `${item.entreprise} — ${item.mission}`;
      link.addEventListener('click', () => { ringDraftBell(1, true); notice.remove(); });
      notice.querySelector('.draft-links').append(link);
    }
    const close = document.createElement('button');
    close.type = 'button';
    close.setAttribute('data-no-action-loader', 'true');
    close.setAttribute('aria-label', 'Fermer le rappel');
    close.textContent = '×';
    close.addEventListener('click', () => { ringDraftBell(2, true); notice.remove(); });
    notice.append(close);
    document.body.append(notice);
    ringDraftBell(1);
  } catch (error) {
    if (request === generation) checked = false;
    console.warn('Rappel des brouillons indisponible', error);
  }
}
