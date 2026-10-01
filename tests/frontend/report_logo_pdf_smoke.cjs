const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../tmp/node_modules/playwright');

(async () => {
  const root = path.join(__dirname, '../..');
  const logo = fs.readFileSync(path.join(root, 'app/static/logo.jpg'));
  const source = fs.readFileSync(path.join(root, 'app/static/js/rapports.js'), 'utf8');
  const start = source.indexOf('  async function pdfLogoPixels()');
  const end = source.indexOf('  function download(', start);
  assert.ok(start >= 0 && end > start);
  const functions = source.slice(start, end).replace(
    '"/static/logo.jpg"',
    `"data:image/jpeg;base64,${logo.toString('base64')}"`,
  );
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.HAUQE_TEST_BROWSER || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  });
  try {
    const page = await browser.newPage();
    await page.setContent('<!doctype html><html><body></body></html>');
    await page.addScriptTag({ content: `
      const me = { prenoms: 'Agent', nom: 'HAUQE' };
      const selected = { title: 'Situation des entreprises', category: 'Registre' };
      const selectedExportFilters = () => ({ start: '2026-09-01', end: '2026-09-30' });
      const flatten = (value) => value;
      const displayKey = (value) => value;
      const frDate = (value) => value;
      ${functions}
      window.makeReport = pdfContent;
    ` });
    const pdf = await page.evaluate(() => window.makeReport([{ Entreprise: 'Exemple', Statut: 'Active' }]));
    assert.match(pdf, /\/Subtype \/Image/);
    assert.match(pdf, /\/Im1 Do/);
    const output = path.join(root, 'tmp/pdfs/hauqe_logo_generic_qa.pdf');
    fs.mkdirSync(path.dirname(output), { recursive: true });
    fs.writeFileSync(output, pdf, 'ascii');
    console.log('Rapport PDF générique : logo incorporé.');
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
