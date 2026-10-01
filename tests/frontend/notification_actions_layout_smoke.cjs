const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../tmp/node_modules/playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.HAUQE_TEST_BROWSER || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  });
  const page = await browser.newPage({ viewport: { width: 1490, height: 620 } });
  try {
    await page.setContent(`<div class="page-content container-fluid alerts-page">
      <section class="panel notification-center-panel"><div class="notification-center-list">
        <article class="notification-center-row unread">
          <span>◉</span>
          <div class="notification-center-content"><strong>Échéance à traiter aujourd’hui : Laiterie du Plateau — CERT-ISO22000-2026-001</strong><p>Bonjour Roland, l’échéance concernant Laiterie du Plateau arrive à son terme aujourd’hui. Identifiant entreprise HAUQE-PRODUCTIONDEL...</p><small>IN_APP · 25/09/2026 · ENVOYÉE</small></div>
          <div class="notification-center-actions"><a class="btn btn-outline-secondary app-btn" href="#/alertes">Ouvrir l’alerte</a><button class="btn btn-outline-secondary app-btn" type="button">Marquer lue</button></div>
        </article>
      </div></section>
    </div>`);
    for (const name of ['styles.css', 'alertes.css']) {
      await page.addStyleTag({ content: fs.readFileSync(path.join(__dirname, '../../app/static/css', name), 'utf8') });
    }
    for (const [width, zoom] of [[1490, '100%'], [720, '100%'], [1490, '200%'], [390, '100%']]) {
      await page.setViewportSize({ width, height: 620 });
      await page.evaluate((value) => { document.body.style.zoom = value; }, zoom);
      const layout = await page.locator('.notification-center-row').evaluate((row) => {
        const actions = row.querySelector('.notification-center-actions');
        const buttons = [...actions.querySelectorAll('.btn')];
        const rowBox = row.getBoundingClientRect();
        const boxes = buttons.map((button) => button.getBoundingClientRect());
        return {
          rowRight: rowBox.right,
          buttonWidths: boxes.map((box) => box.width),
          buttonRights: boxes.map((box) => box.right),
          buttonTextFits: buttons.map((button) => button.scrollWidth <= button.clientWidth + 2),
          pageFits: document.documentElement.scrollWidth <= document.documentElement.clientWidth + 2,
        };
      });
      assert.ok(layout.buttonWidths.every((value) => value >= 90), `Boutons trop étroits à ${width}px / zoom ${zoom}`);
      assert.ok(layout.buttonRights.every((value) => value <= layout.rowRight + 2), `Boutons hors ligne à ${width}px / zoom ${zoom}`);
      assert.ok(layout.buttonTextFits.every(Boolean), `Libellés coupés à ${width}px / zoom ${zoom}`);
      assert.equal(layout.pageFits, true, `Débordement horizontal à ${width}px / zoom ${zoom}`);
    }
    console.log('Actions des notifications lisibles à 1490/720/390 px et au zoom 200 %.');
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
