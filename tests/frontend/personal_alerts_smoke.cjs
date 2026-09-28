// Recette isolée : API simulée, aucun courriel ni écriture en base.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

const origin = process.env.HAUQE_TEST_ORIGIN || 'http://127.0.0.1:8001';

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.HAUQE_TEST_BROWSER || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const errors = [];
  const requestedAlerts = [];
  let globalAllowed = false;
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(() => sessionStorage.setItem('hauqe-access-token', 'isolated-ui-test'));
  await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, route => route.abort());
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    let body = { items: [], total: 0 };
    if (path === '/api/v1/me') body = { id: '11111111-1111-4111-8111-111111111111', permissions: globalAllowed ? ['NOTIFICATIONS.LIRE', 'ALERTES.LIRE'] : ['NOTIFICATIONS.LIRE'] };
    else if (path.includes('/workspace/alerts')) {
      requestedAlerts.push(path);
      body = { items: [{
        id: '22222222-2222-4222-8222-222222222222', titre: 'Mission attribuée — Atelier Exemple',
        message: 'Entreprise : Atelier Exemple', type_alerte: 'MISSION_AFFECTEE',
        niveau: 2, statut: 'NOUVELLE', date_detection: '2026-09-27',
        resource_label: 'Mission de collecte', resource_route: '#/collectes',
      }], total: 1, summary: { total: 1, active: 1, level_1: 0, level_2: 1, level_3: 0, level_4: 0, resolved: 0 } };
    } else if (path === '/api/v1/notifications') body = { items: [], total: 0, unread_count: 0 };
    else if (path.includes('/alert-filters')) body = { alert_types: ['MISSION_AFFECTEE'], alert_statuses: ['NOUVELLE'] };
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
  });
  try {
    await page.goto(`${origin}/#/alertes`, { waitUntil: 'domcontentloaded' });
    await page.locator('#alertsList [data-alert]').waitFor({ timeout: 10000 });
    assert.equal(await page.locator('#allAlertsScope').isVisible(), false);
    assert.ok(requestedAlerts.includes('/api/v1/veille/workspace/alerts/mine'));
    await page.locator('[data-alert-tab="notifications"]').click();
    assert.equal(await page.locator('#notificationsTab').isVisible(), true, 'notifications au premier clic');
    await page.locator('[data-alert-tab="alerts"]').click();
    await page.locator('#alertsList [data-alert]').click();
    assert.equal(await page.locator('#alertDetailDialog').evaluate(dialog => dialog.open), true, 'alerte au premier clic');
    await page.locator('#alertDetailDialog [data-close-alert-detail]').first().click();
    globalAllowed = true;
    await page.reload();
    await page.locator('#allAlertsScope').waitFor({ state: 'visible', timeout: 10000 });
    await page.locator('#allAlertsScope').click();
    assert.ok(requestedAlerts.includes('/api/v1/veille/workspace/alerts'), 'registre général seulement après clic autorisé');
    for (const size of [{ width: 850, height: 480 }, { width: 640, height: 360 }]) {
      await page.setViewportSize(size);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, 'pas de débordement horizontal');
    }
    assert.deepEqual(errors, [], 'aucune erreur JavaScript');
    console.log('Alertes personnelles : premier clic, séparation des accès et responsive OK.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
