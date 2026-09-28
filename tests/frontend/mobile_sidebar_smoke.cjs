// Reproduit le vrai gestionnaire du shell, sans API ni écriture en base.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

(async () => {
  const source = fs.readFileSync(path.join(__dirname, '../../app/static/js/core/app-shell.js'), 'utf8');
  const begin = source.indexOf('function initMobileSidebar() {');
  const end = source.indexOf('\ninitMobileSidebar();', begin);
  assert.ok(begin >= 0 && end > begin, 'gestionnaire mobile présent');
  const mobileHandler = source.slice(begin, end + '\ninitMobileSidebar();'.length);

  const browser = await chromium.launch({ headless: true, executablePath: process.env.HAUQE_TEST_BROWSER || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  try {
    await page.setContent('<meta name="viewport" content="width=device-width,initial-scale=1"><button id="menuToggle" type="button">Menu</button><aside id="sidebar"><a class="nav-link" href="#/dashboard">Accueil</a></aside>');
    await page.addScriptTag({ content: mobileHandler });
    await page.locator('#menuToggle').tap();
    assert.equal(await page.locator('#sidebar').evaluate(el => el.classList.contains('open')), true, 'un appui tactile ouvre le menu');
    await page.evaluate(() => window.dispatchEvent(new CustomEvent('hauqe:page-ready', { detail: { refresh: true } })));
    assert.equal(await page.locator('#sidebar').evaluate(el => el.classList.contains('open')), true, 'une actualisation ne ferme pas le menu');
    await page.evaluate(() => { location.hash = '#/dashboard'; });
    await page.waitForFunction(() => !document.querySelector('#sidebar').classList.contains('open'));

    await page.evaluate(() => document.querySelector('#menuToggle').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerType: 'touch' })));
    await page.waitForTimeout(700);
    assert.equal(await page.locator('#sidebar').evaluate(el => el.classList.contains('open')), false, 'pointerdown seul ne bascule pas le menu');
    await page.locator('#menuToggle').click();
    assert.equal(await page.locator('#sidebar').evaluate(el => el.classList.contains('open')), true, 'clic retardé ouvre une seule fois');
    await page.locator('#sidebarBackdrop').click();
    assert.equal(await page.locator('#sidebar').evaluate(el => el.classList.contains('open')), false, 'fond ferme le menu');
    assert.deepEqual(errors, [], 'aucune erreur JavaScript');
    console.log('Menu mobile : appui tactile, clic retardé et actualisation silencieuse OK.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
