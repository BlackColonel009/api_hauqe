// Test d'interface isolé : toutes les API sont simulées, aucune donnée réelle n'est écrite.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

const origin = process.env.HAUQE_TEST_ORIGIN || 'http://127.0.0.1:8001';
const missionId = '11111111-1111-4111-8111-111111111111';
const campaignId = '22222222-2222-4222-8222-222222222222';
const zoneId = '33333333-3333-4333-8333-333333333333';
const userId = '44444444-4444-4444-8444-444444444444';
const mission = { id: missionId, campagne_id: campaignId, code: 'HAUQE-MIS-2026-0001', objet: 'Mission test', zone_id: zoneId, priorite: 'NORMALE', date_debut_prevue: '2026-09-27', date_fin_prevue: '2026-09-29' };

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.HAUQE_TEST_BROWSER || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const errors = [];
  let enterprisePosts = 0;
  let organismePosts = 0;
  page.on('pageerror', (error) => errors.push(error.message));
  await page.addInitScript(() => sessionStorage.setItem('hauqe-access-token', 'isolated-ui-test'));
  await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, (route) => route.abort());
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    let body = { items: [] };
    if (path === '/api/v1/me') body = { id: userId, permissions: ['COLLECTE.CREER', 'COLLECTE.LIRE', 'COLLECTE.AFFECTER', 'DOCUMENTS.DEPOSER', 'ORGANISMES.CREER'] };
    else if (path === '/api/v1/collectes/filters') body = { campaigns: [{ id: campaignId, label: 'Campagne test' }], zones: [{ id: zoneId, label: 'Zone test' }], collectors: [], missions: [mission] };
    else if (path === '/api/v1/missions') body = [mission];
    else if (path === `/api/v1/missions/${missionId}`) body = mission;
    else if (path === `/api/v1/missions/${missionId}/affectations`) body = [];
    else if (path === `/api/v1/campagnes/${campaignId}`) body = { id: campaignId, code: 'HAUQE-CAMP-2026-0001', nom: 'Campagne test' };
    else if (path === '/api/v1/collectes/quick-enterprises' && route.request().method() === 'POST') {
      enterprisePosts += 1;
      body = { id: '55555555-5555-4555-8555-555555555555', raison_sociale: 'Entreprise test' };
    }
    else if (path.endsWith('/fiches/quick-organismes') && route.request().method() === 'POST') {
      organismePosts += 1;
      await route.fulfill({ status: 422, contentType: 'application/json', body: JSON.stringify({ detail: 'Erreur simulée pour vérifier le retour dans le modal.' }) });
      return;
    }
    else if (path.includes('/fiches')) body = [];
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
  });
  try {
    await page.goto(`${origin}/#/collectes/nouveau/${missionId}`, { waitUntil: 'domcontentloaded' });
    await page.locator('#collectFormContent article').waitFor({ timeout: 10000 });
    assert.equal(await page.locator('#createRevision').isVisible(), false, 'révision masquée pour une nouvelle collecte');
    assert.equal(await page.locator('#submitCollect').isVisible(), false, 'soumission masquée sans permission');
    assert.match(await page.locator('#collectFormTitle').textContent(), /Nouvelle collecte/);
    await page.locator('#collectStepper [data-step="2"]').click();
    await page.locator('#openQuickEnterprise').waitFor({ timeout: 5000 }).catch(async (error) => {
      console.error('Étape:', await page.locator('#collectProgress').textContent());
      console.error('État:', await page.locator('#collectFormState').textContent());
      console.error('Erreurs JS:', errors);
      throw error;
    });
    await page.locator('#openQuickEnterprise').click();
    assert.equal(await page.locator('#quickEnterpriseDialog').evaluate((el) => el.open), true, 'précréation entreprise au premier clic');
    await page.locator('#quickEnterpriseName').fill('Entreprise test');
    for (const zoom of [1, 1.5, 2]) {
      const viewport = { width: Math.round(1280 / zoom), height: Math.round(800 / zoom) };
      await page.setViewportSize(viewport);
      const layout = await page.locator('#quickEnterpriseDialog').evaluate((dialog) => {
        const footer = dialog.querySelector('.quick-dialog-footer');
        const body = dialog.querySelector('.quick-dialog-body');
        return { dialog: dialog.getBoundingClientRect().toJSON(), footer: footer.getBoundingClientRect().toJSON(), bodyScrollable: getComputedStyle(body).overflowY === 'auto' };
      });
      assert.ok(layout.dialog.width > 300 && layout.dialog.right <= viewport.width + 1, `modal dans la fenêtre au zoom ${zoom}`);
      assert.ok(layout.footer.bottom <= viewport.height + 1 && layout.bodyScrollable, `pied et scroll du modal au zoom ${zoom}: ${JSON.stringify(layout)}`);
    }
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.locator('#quickEnterpriseDialog [data-dialog-close]').first().click();
    await page.locator('#quickEnterpriseDialog').waitFor({ state: 'hidden' });
    await page.locator('#openQuickEnterprise').click();
    await page.locator('#quickEnterpriseName').fill('Entreprise test');
    await page.locator('#quickEnterpriseForm [type="submit"]').click();
    assert.equal(enterprisePosts, 1, 'une seule requête de précréation');
    await page.locator('#collectStepper [data-step="3"]').click();
    await page.locator('#addOfferSlot button').click();
    assert.equal(await page.locator('[data-offer-row]').count(), 1, 'ajout offre au premier clic');
    await page.locator('[data-remove-new-offer-slot] button').click();
    assert.equal(await page.locator('[data-offer-row]').count(), 0, 'suppression offre au premier clic');
    await page.locator('#collectStepper [data-step="4"]').click();
    await page.locator('#addDeclaredCertSlot button').click();
    await page.locator('[name="decl_cert_body"]').fill('Organisme fictif');
    await page.locator('[data-precreate-organisme]').waitFor();
    await page.locator('[data-precreate-organisme]').click();
    assert.equal(await page.locator('#quickOrganismeDialog').evaluate((el) => el.open), true, 'précréation organisme au premier clic');
    for (const zoom of [1, 1.5, 2]) {
      const viewport = { width: Math.round(1280 / zoom), height: Math.round(800 / zoom) };
      await page.setViewportSize(viewport);
      const layout = await page.locator('#quickOrganismeDialog').evaluate((dialog) => ({
        dialog: dialog.getBoundingClientRect().toJSON(),
        footer: dialog.querySelector('.quick-dialog-footer').getBoundingClientRect().toJSON(),
        scroll: getComputedStyle(dialog.querySelector('.quick-dialog-body')).overflowY,
      }));
      assert.ok(layout.dialog.right <= viewport.width + 1 && layout.footer.bottom <= viewport.height + 1 && layout.scroll === 'auto', `modal organisme au zoom ${zoom}`);
    }
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.locator('#quickAccrediteur').fill('Accréditeur fictif');
    await page.locator('#quickOrganismeForm [type="submit"]').click();
    await page.locator('#quickOrganismeDialog .modal-form-feedback:not([hidden])').waitFor();
    assert.equal(organismePosts, 1, 'une seule requête organisme');
    await page.locator('#quickOrganismeDialog [data-dialog-close]').first().click();
    await page.evaluate(() => document.querySelector('#quickZoneDialog').showModal());
    for (const zoom of [1, 1.5, 2]) {
      const viewport = { width: Math.round(1280 / zoom), height: Math.round(800 / zoom) };
      await page.setViewportSize(viewport);
      const layout = await page.locator('#quickZoneDialog').evaluate((dialog) => ({
        dialog: dialog.getBoundingClientRect().toJSON(),
        footer: dialog.querySelector('.quick-dialog-footer').getBoundingClientRect().toJSON(),
        scroll: getComputedStyle(dialog.querySelector('.quick-dialog-body')).overflowY,
      }));
      assert.ok(layout.dialog.right <= viewport.width + 1 && layout.footer.bottom <= viewport.height + 1 && layout.scroll === 'auto', `modal zone au zoom ${zoom}`);
    }
    await page.locator('#quickZoneDialog [data-dialog-close]').first().click();
    await page.setViewportSize({ width: 1280, height: 800 });
    if (process.env.HAUQE_TEST_SCREENSHOT) {
      await page.screenshot({ path: process.env.HAUQE_TEST_SCREENSHOT, fullPage: true });
    }
    assert.equal(await page.locator('[data-declared-cert-row]').count(), 1, 'ajout certification au premier clic');
    await page.locator('[data-remove-new-cert-slot] button').click();
    assert.equal(await page.locator('[data-declared-cert-row]').count(), 0, 'suppression certification au premier clic');
    await page.locator('#addDeclaredCertSlot button').click();
    for (const zoom of [1, 1.5, 2]) {
      await page.setViewportSize({ width: Math.round(1280 / zoom), height: Math.round(800 / zoom) });
      const evidence = page.locator('.declared-cert-evidence');
      const row = page.locator('[data-declared-cert-row]');
      const evidenceBox = await evidence.boundingBox();
      const rowBox = await row.boundingBox();
      assert.ok(evidenceBox.width > rowBox.width * 0.7, `preuve non écrasée au zoom ${zoom}`);
      assert.equal(await page.locator('#collectNext').isVisible(), true);
    }
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.locator('#collectFormContent article').waitFor();
    await page.locator('#collectStepper [data-step="2"]').click();
    await page.locator('#openQuickEnterprise').click();
    await page.locator('#quickEnterpriseName').fill('Entreprise test après retour');
    await page.locator('#quickEnterpriseForm [type="submit"]').click();
    assert.equal(enterprisePosts, 2, 'une seule requête après nouvelle visite de la page');
    assert.deepEqual(errors, [], 'aucune erreur JavaScript');
    console.log('OK — premier clic, ajout/suppression offres et certifications, soumission unique, modals et zoom 100/150/200 %.');
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
