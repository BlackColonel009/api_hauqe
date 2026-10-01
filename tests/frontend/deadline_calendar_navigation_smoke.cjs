const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../tmp/node_modules/playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.HAUQE_TEST_BROWSER || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  });
  const page = await browser.newPage();
  try {
    await page.setContent(`
      <span id="prevMonthSlot"></span><span id="todayButtonSlot"></span>
      <span id="nextMonthSlot"></span><span id="calendarZoomInSlot"></span>
      <span id="calendarZoomOutSlot"></span>
    `);
    const source = fs.readFileSync(
      path.join(__dirname, '../../app/static/js/echeances.js'), 'utf8',
    );
    const start = source.indexOf('  function createCalendarNavigationButton(');
    const end = source.indexOf('  function showDateDetails(', start);
    assert.ok(start >= 0 && end > start);
    const navigationCode = source.slice(start, end);
    await page.addScriptTag({ content: `
      const $ = (selector) => document.querySelector(selector);
      const e = (value) => String(value);
      let calendarScale = 'month';
      const calls = [];
      async function navigateMonth(delta) { calls.push(delta); }
      async function goToday() { calls.push('today'); }
      async function zoomIn() { calls.push('zoom-in'); }
      async function zoomOut() { calls.push('zoom-out'); }
      ${navigationCode}
      window.calendarTest = {
        hydrate: hydrateCalendarNavigation,
        calls,
        setScale: (value) => { calendarScale = value; },
      };
    ` });

    await page.evaluate(() => {
      window.calendarTest.hydrate();
      window.firstButtons = ['prevMonth', 'todayButton', 'nextMonth'].map(
        (id) => document.getElementById(id),
      );
      window.calendarTest.setScale('year');
      window.calendarTest.hydrate();
    });
    assert.equal(await page.evaluate(() => window.firstButtons.every(
      (button) => button.isConnected && document.getElementById(button.id) === button,
    )), true, 'Un rendu ne doit pas remplacer les boutons visibles.');

    await page.locator('#prevMonth').click();
    await page.locator('#todayButton').click();
    await page.locator('#nextMonth').click();
    assert.deepEqual(await page.evaluate(() => window.calendarTest.calls), [-1, 'today', 1]);
    await page.evaluate(() => { document.body.style.zoom = '200%'; });
    await page.locator('#prevMonth').click();
    await page.locator('#todayButton').click();
    await page.locator('#nextMonth').click();
    assert.deepEqual(await page.evaluate(() => window.calendarTest.calls),
      [-1, 'today', 1, -1, 'today', 1]);
    assert.equal(await page.locator('#calendarZoomIn').isDisabled(), false);
    assert.equal(await page.locator('#calendarZoomOut').isDisabled(), false);

    await page.evaluate(() => {
      window.calendarTest.setScale('decade');
      window.calendarTest.hydrate();
    });
    assert.equal(await page.locator('#calendarZoomOut').isDisabled(), true);
    assert.equal(await page.evaluate(() => window.firstButtons.every(
      (button) => document.getElementById(button.id) === button,
    )), true);
    console.log('Calendrier : trois navigations au premier clic à 100 % et 200 %, boutons stables après rendu.');
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
