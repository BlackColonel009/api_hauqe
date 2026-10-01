const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../tmp/node_modules/playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.HAUQE_TEST_BROWSER || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  });
  const page = await browser.newPage({ viewport: { width: 900, height: 700 } });
  try {
    const html = fs.readFileSync(path.join(__dirname, '../../app/templates/views/utilisateurs.html'), 'utf8');
    const css = fs.readFileSync(path.join(__dirname, '../../app/static/css/utilisateurs.css'), 'utf8');
    const source = fs.readFileSync(path.join(__dirname, '../../app/static/js/utilisateurs.js'), 'utf8')
      .replace('await import("/static/js/core/api.js")', 'window.mockApi');
    await page.setContent(html);
    await page.addStyleTag({ content: css });
    await page.evaluate(() => {
      window.mockApi = {
        apiGet: async (url) => url === '/api/v1/me'
          ? { permissions: ['UTILISATEURS.LIRE', 'UTILISATEURS.CREER'] }
          : [],
      };
      window.copiedValues = [];
      Object.defineProperty(window, 'isSecureContext', { value: false, configurable: true });
      window.originalExecCommand = document.execCommand.bind(document);
      document.execCommand = (command) => {
        if (command !== 'copy') return false;
        window.copiedValues.push(document.activeElement?.value || window.getSelection()?.toString());
        return true;
      };
    });
    await page.addScriptTag({ content: source });
    await page.locator('#credentialEmail').evaluate((node) => { node.textContent = 'agent@hauqe.tg'; });
    await page.locator('#credentialPassword').evaluate((node) => { node.textContent = 'Temporaire-2026!'; });
    await page.locator('#credentialDialog').evaluate((node) => node.showModal());
    await page.locator('[data-copy-credential="email"]').click();
    await page.locator('[data-copy-credential="password"]').click();
    await page.locator('[data-copy-credential="email"]').click();
    assert.deepEqual(await page.evaluate(() => window.copiedValues),
      ['agent@hauqe.tg', 'Temporaire-2026!', 'agent@hauqe.tg']);
    assert.equal(await page.locator('#credentialCopyFeedback').innerText(),
      'Valeur copiée dans le presse-papiers.');
    await page.locator('[data-copy-credential="email"]').evaluate((button) => {
      button.replaceWith(button.cloneNode(true));
    });
    await page.locator('[data-copy-credential="email"]').click();
    assert.equal((await page.evaluate(() => window.copiedValues)).at(-1), 'agent@hauqe.tg',
      'Un bouton recréé dans le modal doit fonctionner au premier clic.');
    await page.evaluate(() => { document.execCommand = () => false; });
    await page.locator('[data-copy-credential="password"]').click();
    assert.equal(await page.locator('#credentialCopyFeedback').innerText(),
      'Copie automatique refusée : la valeur est sélectionnée, appuyez sur Ctrl+C.');
    await page.evaluate(() => { document.execCommand = (command) => {
      if (command !== 'copy') return false;
      window.copiedValues.push(document.activeElement?.value || window.getSelection()?.toString());
      return true;
    }; });
    await page.locator('#credentialDialog').evaluate((node) => node.close());
    await page.locator('#createUserButton').click();
    await page.locator('#userEmail').fill('nouveau@hauqe.tg');
    await page.locator('#userWizardNext').click();
    await page.locator('#userInitialPassword').fill('AvantCreation-2026!');
    await page.locator('#copyUserPassword').click();
    assert.equal((await page.evaluate(() => window.copiedValues)).at(-1), 'AvantCreation-2026!');
    assert.equal(await page.locator('#userCopyFeedback').innerText(),
      'Valeur copiée dans le presse-papiers.');
    await page.evaluate(() => {
      document.execCommand = window.originalExecCommand;
      document.addEventListener('copy', () => {
        window.nativeCopySeen = true;
        window.nativeCopiedText = document.activeElement?.value;
      }, { once: true });
    });
    await page.locator('#copyUserPassword').click();
    assert.equal(await page.evaluate(() => window.nativeCopySeen), true,
      'Le navigateur doit accepter la copie native depuis le modal.');
    assert.equal(await page.evaluate(() => window.nativeCopiedText), 'AvantCreation-2026!');
    const secureContext = await browser.newContext({ permissions: ['clipboard-read', 'clipboard-write'] });
    const securePage = await secureContext.newPage();
    await securePage.route('https://hauqe-copy.test/', (route) => route.fulfill({
      status: 200, contentType: 'text/html', body: html,
    }));
    await securePage.goto('https://hauqe-copy.test/');
    await securePage.evaluate(() => {
      window.mockApi = {
        apiGet: async (url) => url === '/api/v1/me'
          ? { permissions: ['UTILISATEURS.LIRE', 'UTILISATEURS.CREER'] }
          : [],
      };
    });
    await securePage.addScriptTag({ content: source });
    await securePage.locator('#credentialEmail').evaluate((node) => { node.textContent = 'agent@hauqe.tg'; });
    await securePage.locator('#credentialPassword').evaluate((node) => { node.textContent = 'Temporaire-2026!'; });
    await securePage.locator('#credentialDialog').evaluate((node) => node.showModal());
    await securePage.locator('[data-copy-credential="email"]').click();
    assert.equal(await securePage.evaluate(() => navigator.clipboard.readText()), 'agent@hauqe.tg');
    await securePage.locator('[data-copy-credential="password"]').click();
    assert.equal(await securePage.evaluate(() => navigator.clipboard.readText()), 'Temporaire-2026!');
    const insecurePage = await secureContext.newPage();
    await insecurePage.route('http://hauqe-copy.test/', (route) => route.fulfill({
      status: 200, contentType: 'text/html', body: html,
    }));
    await insecurePage.goto('http://hauqe-copy.test/');
    await insecurePage.evaluate(() => {
      window.mockApi = {
        apiGet: async (url) => url === '/api/v1/me'
          ? { permissions: ['UTILISATEURS.LIRE', 'UTILISATEURS.CREER'] }
          : [],
      };
    });
    await insecurePage.addScriptTag({ content: source });
    await insecurePage.locator('#credentialEmail').evaluate((node) => { node.textContent = 'http@hauqe.tg'; });
    await insecurePage.locator('#credentialDialog').evaluate((node) => node.showModal());
    await insecurePage.locator('[data-copy-credential="email"]').click();
    assert.equal(await insecurePage.locator('#credentialCopyFeedback').innerText(),
      'Valeur copiée dans le presse-papiers.');
    assert.equal(await securePage.evaluate(() => navigator.clipboard.readText()), 'http@hauqe.tg',
      'La copie de secours sur HTTP doit réellement alimenter le presse-papiers.');
    await secureContext.close();
    if (process.env.HAUQE_LIVE_URL) {
      const liveOrigin = new URL(process.env.HAUQE_LIVE_URL).origin;
      const liveContext = await browser.newContext({ permissions: ['clipboard-read', 'clipboard-write'] });
      const livePage = await liveContext.newPage();
      await livePage.addInitScript(() => sessionStorage.setItem('hauqe-access-token', 'test-token'));
      await livePage.route('**/api/v1/**', (route) => {
        const url = new URL(route.request().url());
        const payload = url.pathname === '/api/v1/me'
          ? { id: '11111111-1111-1111-1111-111111111111', nom: 'Test', permissions: ['UTILISATEURS.LIRE', 'UTILISATEURS.CREER'] }
          : [];
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(payload) });
      });
      await livePage.goto(`${liveOrigin}/#/utilisateurs`);
      await livePage.locator('#createUserButton').click();
      await livePage.locator('#userEmail').fill('local@hauqe.tg');
      await livePage.locator('#userWizardNext').click();
      await livePage.locator('#userInitialPassword').fill('Live-Password-2026!');
      await livePage.locator('#copyUserPassword').click();
      assert.equal(await livePage.evaluate(() => navigator.clipboard.readText()), 'Live-Password-2026!');
      await liveContext.close();
    }
    console.log('Copie des identifiants : premier clic, répétition et échec visibles dans le modal.');
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
