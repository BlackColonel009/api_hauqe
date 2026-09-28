// Recette isolée : API simulée, aucun courriel ni écriture en base.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

const origin = process.env.HAUQE_TEST_ORIGIN || 'http://127.0.0.1:8001';
const userId = '22222222-2222-4222-8222-222222222222';
const otherId = '33333333-3333-4333-8333-333333333333';
let admin = true;
const enabled = { [userId]: true, [otherId]: true };
const saved = [];

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.HAUQE_TEST_BROWSER || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 1100, height: 750 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(() => sessionStorage.setItem('hauqe-access-token', 'isolated-ui-test'));
  await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, route => route.abort());
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    const roles = admin ? ['ADMIN_HAUQE'] : ['VERIFICATEUR'];
    let body = {};
    if (path === '/api/v1/me') body = { id: userId, roles, permissions: [] };
    else if (path === '/api/v1/me/profile') body = { id: userId, email: 'admin@hauqe.test', prenoms: 'Test', nom: 'Admin', roles, permissions: [], statut: 'ACTIF', mfa_active: false, created_at: '2026-01-01', langue: 'fr', fuseau_horaire: 'Africa/Lome' };
    else if (path === '/api/v1/me/notification-preferences') body = { alertes_critiques: true, affectations: true, corrections: true, rapports_planifies: false, resume_hebdomadaire: true, actualisation_automatique_active: true, actualisation_intervalle_secondes: 30, actualisation_au_retour: true };
    else if (path === '/api/v1/me/admin/system-email-policies') body = [
      { utilisateur_id: userId, nom: 'Agent Exemple', email: 'agent@hauqe.test', statut: 'ACTIF', courriels_systeme_actifs: enabled[userId] },
      { utilisateur_id: otherId, nom: 'Second Agent', email: 'second@hauqe.test', statut: 'ACTIF', courriels_systeme_actifs: enabled[otherId] },
    ];
    else if (path.startsWith('/api/v1/me/admin/system-email-policies/')) {
      const value = route.request().postDataJSON();
      saved.push(value);
      const target = path.split('/').pop();
      enabled[target] = value.courriels_systeme_actifs;
      body = { utilisateur_id: target, nom: target === userId ? 'Agent Exemple' : 'Second Agent', email: target === userId ? 'agent@hauqe.test' : 'second@hauqe.test', statut: 'ACTIF', courriels_systeme_actifs: enabled[target] };
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
  });
  try {
    await page.goto(`${origin}/#/profil`, { waitUntil: 'domcontentloaded' });
    await page.locator('[data-profile-tab="notifications"]').click();
    await page.locator('#adminEmailUser').waitFor();
    assert.equal(await page.locator('[data-admin-email-remove]').count(), 2, 'tous présents par défaut');
    await page.locator(`[data-admin-email-remove="${userId}"]`).uncheck();
    await page.waitForFunction(() => document.querySelectorAll('[data-admin-email-remove]').length === 1, null, { timeout: 5000 });
    assert.deepEqual(saved, [{ courriels_systeme_actifs: false }], 'enregistrement au premier clic');
    await page.locator('#adminEmailUser').selectOption(userId);
    await page.locator('#adminEmailAdd').click();
    await page.waitForFunction(() => document.querySelectorAll('[data-admin-email-remove]').length === 2, null, { timeout: 5000 });
    assert.deepEqual(saved, [{ courriels_systeme_actifs: false }, { courriels_systeme_actifs: true }], 'réajout au premier clic');
    await page.setViewportSize({ width: 640, height: 400 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, 'aucun débordement au zoom');
    assert.equal(await page.locator('#adminEmailList').evaluate(el => getComputedStyle(el).overflowY), 'auto', 'liste défilante au zoom');
    admin = false;
    await page.reload();
    await page.locator('[data-profile-tab="notifications"]').click();
    await page.locator('#notificationPreferencesForm').waitFor();
    assert.equal(await page.locator('#adminEmailUser').count(), 0, 'réglage invisible au non-admin');
    assert.deepEqual(errors, [], 'aucune erreur JavaScript');
    console.log('Profil : réglage admin, premier clic, confidentialité et largeur réduite OK.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
