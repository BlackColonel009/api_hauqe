const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.HAUQE_TEST_BROWSER || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' });
  const page = await browser.newPage();
  try {
    const css = fs.readFileSync(path.join(__dirname, '../../app/static/css/echeances.css'), 'utf8');
    await page.setContent(`<style>${css}</style><span class="registry-status en_retard">En retard</span>`);
    await page.locator('.registry-status.en_retard').waitFor();
    await page.waitForFunction(() => getComputedStyle(document.querySelector('.registry-status.en_retard')).backgroundColor !== 'rgba(0, 0, 0, 0)');
    const light = await page.locator('.registry-status.en_retard').evaluate(el => ({ color: getComputedStyle(el).color, background: getComputedStyle(el).backgroundColor }));
    assert.deepEqual(light, { color: 'rgb(175, 52, 53)', background: 'rgb(255, 235, 232)' });
    await page.evaluate(() => document.documentElement.dataset.theme = 'dark');
    const dark = await page.locator('.registry-status.en_retard').evaluate(el => ({ color: getComputedStyle(el).color, background: getComputedStyle(el).backgroundColor }));
    assert.deepEqual(dark, { color: 'rgb(255, 184, 180)', background: 'rgb(77, 36, 41)' });
    console.log('Statut En retard : rouge en thèmes clair et sombre.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
