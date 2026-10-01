const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../tmp/node_modules/playwright');

const root = path.join(__dirname, '../..');
const css = ['styles.css', 'dialog-system.css', 'echeances.css', 'alertes.css', 'modal-echeances-standard.css']
  .map((name) => fs.readFileSync(path.join(root, 'app/static/css', name), 'utf8'));
function dialogFrom(file, id) {
  const html = fs.readFileSync(path.join(root, 'app/templates/views', file), 'utf8');
  const match = html.match(new RegExp(`<dialog\\s+id="${id}"[\\s\\S]*?<\\/dialog>`));
  assert.ok(match, `Modal introuvable : ${id}`);
  return match[0];
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.HAUQE_TEST_BROWSER || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  });
  try {
    for (const config of [
      { file: 'alertes.html', id: 'specialAlertDialog', last: '#specialAlertRule' },
      { file: 'echeances.html', id: 'deadlineDialog', last: '#deadlineDescription' },
    ]) {
      const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
      await page.setContent(`<!doctype html><html><body>${dialogFrom(config.file, config.id)}</body></html>`);
      for (const sheet of css) await page.addStyleTag({ content: sheet });
      await page.evaluate((id) => {
        if (id === 'deadlineDialog') {
          document.querySelector('[data-deadline-panel="1"]').hidden = true;
          document.querySelector('[data-deadline-panel="3"]').hidden = false;
        } else if (id === 'specialAlertDialog') {
          document.querySelector('[data-special-alert-panel="1"]').hidden = true;
          document.querySelector('[data-special-alert-panel="3"]').hidden = false;
        }
        document.getElementById(id).showModal();
      }, config.id);
      for (const [width, height, zoom] of [[1280, 720, '200%'], [390, 720, '100%'], [640, 360, '100%'], [420, 240, '100%']]) {
        await page.setViewportSize({ width, height });
        await page.evaluate((value) => { document.body.style.zoom = value; }, zoom);
        const result = await page.evaluate((selector) => {
          const dialog = document.querySelector('dialog');
          const form = dialog.querySelector('form');
          const target = document.querySelector(selector);
          target.scrollIntoView({ block: 'center' });
          const bounds = dialog.getBoundingClientRect();
          const field = target.getBoundingClientRect();
          return {
            hasScroll: form.scrollHeight > form.clientHeight,
            visible: field.top >= bounds.top - 2 && field.bottom <= bounds.bottom + 2,
            dialog: [bounds.top, bounds.bottom], field: [field.top, field.bottom],
            form: [form.scrollTop, form.scrollHeight, form.clientHeight],
          };
        }, config.last);
        assert.ok(result.visible, `${config.id}: dernier champ inaccessible à ${width}px / ${zoom}: ${JSON.stringify(result)}`);
        if (width === 420 && height === 240) {
          const directory = path.join(root, 'tmp/modal-zoom-qa');
          fs.mkdirSync(directory, { recursive: true });
          await page.screenshot({ path: path.join(directory, `${config.id}.png`) });
        }
      }
      await page.close();
    }
    const wizardPage = await browser.newPage();
    await wizardPage.setContent(`<!doctype html><html><body>${dialogFrom('echeances.html', 'deadlineDialog')}</body></html>`);
    for (const sheet of css) await wizardPage.addStyleTag({ content: sheet });
    const script = fs.readFileSync(path.join(root, 'app/static/js/echeances.js'), 'utf8');
    const start = script.indexOf('  function setDeadlineStep(');
    const end = script.indexOf('  function showDetail(', start);
    assert.ok(start >= 0 && end > start);
    await wizardPage.addScriptTag({ content: `
      const $ = (selector) => document.querySelector(selector);
      const $$ = (selector) => [...document.querySelectorAll(selector)];
      const icons = () => {};
      let deadlineStep = 1;
      ${script.slice(start, end)}
      $('#deadlineNext').onclick = nextDeadlineStep;
      $('#deadlinePrevious').onclick = () => setDeadlineStep(deadlineStep - 1);
      window.getStep = () => deadlineStep;
      setDeadlineStep(1);
      $('#deadlineDialog').showModal();
    ` });
    await wizardPage.locator('#deadlineNext').click();
    assert.equal(await wizardPage.evaluate(() => window.getStep()), 1, 'Champs requis non contrôlés.');
    await wizardPage.locator('#deadlineCertification').evaluate((field) => {
      field.innerHTML = '<option value="cert">Certification exemple</option>';
      field.value = 'cert';
    });
    await wizardPage.locator('#deadlineType').fill('SUIVI_DOCUMENTAIRE');
    await wizardPage.locator('#deadlineNext').click();
    assert.equal(await wizardPage.evaluate(() => window.getStep()), 2);
    await wizardPage.locator('#deadlineTitle').fill('Vérifier le renouvellement');
    await wizardPage.locator('#deadlineDate').fill('2026-10-10');
    await wizardPage.locator('#deadlineNext').click();
    assert.equal(await wizardPage.evaluate(() => window.getStep()), 3);
    assert.equal(await wizardPage.locator('#saveDeadline').isVisible(), true);
    await wizardPage.locator('#deadlinePrevious').click();
    assert.equal(await wizardPage.evaluate(() => window.getStep()), 2);
    await wizardPage.close();
    const alertPage = await browser.newPage();
    await alertPage.setContent(`<!doctype html><html><body>${dialogFrom('alertes.html', 'specialAlertDialog')}</body></html>`);
    for (const sheet of css) await alertPage.addStyleTag({ content: sheet });
    const alertScript = fs.readFileSync(path.join(root, 'app/static/js/alertes.js'), 'utf8');
    const alertStart = alertScript.indexOf('  function setSpecialAlertStep(');
    const alertEnd = alertScript.indexOf('  function notificationTime(', alertStart);
    assert.ok(alertStart >= 0 && alertEnd > alertStart);
    await alertPage.addScriptTag({ content: `
      const $ = (selector) => document.querySelector(selector);
      const $$ = (selector) => [...document.querySelectorAll(selector)];
      const icons = () => {};
      let specialAlertStep = 1;
      ${alertScript.slice(alertStart, alertEnd)}
      $('#specialAlertNext').onclick = nextSpecialAlertStep;
      $('#specialAlertPrevious').onclick = () => setSpecialAlertStep(specialAlertStep - 1);
      window.getStep = () => specialAlertStep;
      setSpecialAlertStep(1);
      $('#specialAlertDialog').showModal();
    ` });
    await alertPage.locator('#specialAlertNext').click();
    assert.equal(await alertPage.evaluate(() => window.getStep()), 1, 'Certification et type requis non contrôlés.');
    await alertPage.locator('#specialAlertCertification').evaluate((field) => {
      field.innerHTML = '<option value="cert">Certification exemple</option>';
      field.value = 'cert';
    });
    await alertPage.locator('#specialAlertType').fill('SUSPICION_DOCUMENTAIRE');
    await alertPage.locator('#specialAlertNext').click();
    assert.equal(await alertPage.evaluate(() => window.getStep()), 2);
    await alertPage.locator('#specialAlertNext').click();
    assert.equal(await alertPage.evaluate(() => window.getStep()), 3);
    assert.equal(await alertPage.locator('#saveSpecialAlert').isVisible(), true);
    await alertPage.locator('#specialAlertPrevious').click();
    assert.equal(await alertPage.evaluate(() => window.getStep()), 2);
    await alertPage.close();
    console.log('Modals Alertes et Échéances : derniers champs accessibles, y compris en viewport réduit 420 × 240.');
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
