const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../tmp/node_modules/playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.HAUQE_TEST_BROWSER || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  });
  const page = await browser.newPage({ viewport: { width: 1490, height: 600 } });
  try {
    await page.setContent(`<div class="page-content container-fluid sncc-page scoring-workspace-page">
      <section class="panel score-history scoring-enterprises-panel">
        <div class="scoring-entity-list"><article class="scoring-entity-row">
          <span>◎</span>
          <div><strong>CERT-ISO22000-2026-002</strong><small>AgroNoura SARL · ISO 22000</small></div>
          <div class="scoring-latest-result"><strong>Aucun classement courant</strong><small>Disponible pour un premier classement</small></div>
          <span class="sncc-ineligible"><svg viewBox="0 0 16 16"><circle cx="8" cy="8" r="6"/></svg>En attente INFC</span>
        </article></div>
      </section>
    </div>`);
    for (const name of ['styles.css', 'scoring.css']) {
      await page.addStyleTag({ content: fs.readFileSync(path.join(__dirname, '../../app/static/css', name), 'utf8') });
    }
    for (const [width, zoom] of [[1490, '100%'], [800, '100%'], [1490, '200%'], [390, '100%']]) {
      await page.setViewportSize({ width, height: 600 });
      await page.evaluate((value) => { document.body.style.zoom = value; }, zoom);
      const layout = await page.locator('.scoring-entity-row').evaluate((row) => {
        const badge = row.querySelector('.sncc-ineligible');
        const rowBox = row.getBoundingClientRect();
        const badgeBox = badge.getBoundingClientRect();
        return {
          rowBottom: rowBox.bottom, rowRight: rowBox.right,
          badgeBottom: badgeBox.bottom, badgeRight: badgeBox.right,
          badgeWidth: badgeBox.width,
          textFits: badge.scrollWidth <= badge.clientWidth + 2,
          pageFits: document.documentElement.scrollWidth <= document.documentElement.clientWidth + 2,
        };
      });
      assert.ok(layout.badgeWidth >= 95, `Badge SNCC comprimé à ${width}px / zoom ${zoom}`);
      assert.ok(layout.badgeBottom <= layout.rowBottom + 2, `Badge sort sous la ligne à ${width}px / zoom ${zoom}`);
      assert.ok(layout.badgeRight <= layout.rowRight + 2, `Badge sort à droite à ${width}px / zoom ${zoom}`);
      assert.equal(layout.textFits, true, `Texte du badge coupé à ${width}px / zoom ${zoom}`);
      assert.equal(layout.pageFits, true, `Débordement de page à ${width}px / zoom ${zoom}`);
    }
    console.log('Badge « En attente INFC » contenu dans sa ligne à 1490/800/390 px et au zoom 200 %.');
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
