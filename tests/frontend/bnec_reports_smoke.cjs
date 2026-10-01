const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../tmp/node_modules/playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.HAUQE_TEST_BROWSER || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
  try {
    const html = fs.readFileSync(path.join(__dirname, '../../app/templates/views/rapports.html'), 'utf8');
    const css = fs.readFileSync(path.join(__dirname, '../../app/static/css/rapports.css'), 'utf8');
    const source = fs.readFileSync(path.join(__dirname, '../../app/static/js/rapports.js'), 'utf8')
      .replace('await import("/static/js/core/api.js")', 'window.mockApi');
    await page.setContent(html);
    await page.addStyleTag({ content: css });
    await page.evaluate(() => {
      window.calls = [];
      window.companyRows = [
        { id: '11111111-1111-1111-1111-111111111111', identifiant_national: 'HAUQE-ENT-2026-0001', raison_sociale: 'Entreprise Alpha', zone_siege_id: 'zone-1', statut: 'ACTIF', created_at: '2026-09-01T08:00:00Z' },
        { id: '22222222-2222-2222-2222-222222222222', identifiant_national: 'HAUQE-ENT-2026-0002', raison_sociale: 'Entreprise Bêta', zone_siege_id: 'zone-2', statut: 'INACTIF', created_at: '2026-09-02T08:00:00Z' },
      ];
      window.certificationRows = [
        { id: '33333333-3333-3333-3333-333333333333', identifiant_national: 'CERT-ISO22000-2026-001', norme_id: 'norm-1', statut: 'ACTIF', created_at: '2026-09-04T08:00:00Z' },
        { id: '44444444-4444-4444-4444-444444444444', identifiant_national: 'CERT-ISO9001-2026-001', norme_id: 'norm-2', statut: 'ACTIF', created_at: '2026-09-05T08:00:00Z' },
      ];
      window.mockApi = {
        apiGet: async (url) => window.mockApi.apiRequest(url),
        apiRequest: async (url, options) => {
          window.calls.push([url, options?.body || null]);
          if (url === '/api/v1/me') return { prenoms: 'Agent', nom: 'Test' };
          if (url === '/api/v1/reports/configurations' && options?.method === 'POST') {
            if (window.rejectConfigSave) throw new Error('Enregistrement refusé');
            window.savedConfig = { ...options.body, code_modele: `EXPORT_CONFIG_${options.body.model_id.toUpperCase()}`, nom_modele: 'Situation des entreprises' };
            return window.savedConfig;
          }
          if (url === '/api/v1/reports/configurations') return { total: window.savedConfig ? 1 : 0, items: window.savedConfig ? [window.savedConfig] : [] };
          if (url.startsWith('/api/v1/reports?')) return { total: 0, items: [] };
          if (url.startsWith('/api/v1/entreprises?')) return { total: window.companyRows.length, items: window.companyRows };
          if (url === '/api/v1/entreprises/filters') return { zones: [{ id: 'zone-1', nom: 'Lomé' }, { id: 'zone-2', nom: 'Kara' }] };
          if (url.startsWith('/api/v1/certifications?')) return { total: window.certificationRows.length, items: window.certificationRows };
          if (url === '/api/v1/certifications/filters') return { norms: [{ id: 'norm-1', code: 'ISO 22000', label: 'ISO 22000' }, { id: 'norm-2', code: 'ISO 9001', label: 'ISO 9001' }] };
          if (url.startsWith('/api/v1/reports/bnec/preview')) {
            const params = new URL(url, 'http://localhost').searchParams;
            if (window.slowQuarter && params.get('type') === 'TRIMESTRIEL') {
              await new Promise((resolve) => setTimeout(resolve, 350));
            }
            return { title: `Bilan ${params.get('type')}`, period_label: `${params.get('type')} ${params.get('year')}`, start: params.get('type') === 'ANNUEL' ? '2026-01-01' : '2026-07-01', end: params.get('type') === 'ANNUEL' ? '2026-12-31' : '2026-09-30', data_as_of: '2026-10-01', provisional: params.get('type') === 'ANNUEL', rows: [['En bref', "Le bilan présente l'INFC du trimestre et l'état actuel du registre, des risques et des répartitions."], ['Chiffres à retenir — INFC moyen', '82. Moyenne des INFC calculés pour le trimestre choisi.']] };
          }
          if (url === '/api/v1/reports/bnec/generate') return { id: '12345678-1234-1234-1234-123456789abc', format: 'PDF' };
          return { items: [], total: 0 };
        },
        apiBlob: async (url) => { window.calls.push([url, 'blob']); return new Blob(['%PDF-1.4'], { type: 'application/pdf' }); },
      };
    });
    await page.addScriptTag({ content: source });
    await page.locator('[data-bnec-type="TRIMESTRIEL"]').click();
    assert.equal(await page.locator('#bnecReportQuarterField').isVisible(), true);
    assert.equal(await page.locator('#bnecReportMonthField').isVisible(), false);
    await page.locator('#bnecReportYear').fill('2026');
    await page.locator('#bnecReportQuarter').selectOption('3');
    await page.locator('#bnecReportPreview').click();
    await page.getByText('En bref').first().waitFor();
    await page.locator('#bnecReportPreview').click();
    await page.getByText('Bilan TRIMESTRIEL — TRIMESTRIEL 2026').waitFor();
    assert.equal(await page.evaluate(() => window.calls.filter(([url]) => url.startsWith('/api/v1/reports/bnec/preview')).length), 2,
      'Le même aperçu trimestriel doit pouvoir être rouvert sans rechargement.');
    const download = page.waitForEvent('download');
    await page.locator('#bnecReportGenerate').click();
    await download;
    const call = await page.evaluate(() => window.calls.find(([url]) => url === '/api/v1/reports/bnec/generate'));
    assert.deepEqual(call[1], { type: 'TRIMESTRIEL', year: 2026, month: null, quarter: 3, format: 'PDF' });
    await page.evaluate(() => { document.body.style.zoom = '200%'; });
    await page.locator('[data-bnec-type="ANNUEL"]').click();
    assert.equal(await page.locator('#bnecReportQuarterField').isVisible(), false);
    assert.equal(await page.locator('#bnecReportYear').isVisible(), true);
    assert.equal(await page.locator('#bnecReportGenerate').isDisabled(), false);
    await page.locator('#bnecReportPreview').click();
    await page.getByText('Bilan ANNUEL — ANNUEL 2026').waitFor();
    await page.getByText('Bilan provisoire : données arrêtées au 01/10/2026.', { exact: false }).waitFor();
    await page.locator('#bnecReportPreview').click();
    assert.equal(await page.evaluate(() => window.calls.filter(([url]) => url.startsWith('/api/v1/reports/bnec/preview')).length), 4,
      'L’aperçu annuel doit rester utilisable plusieurs fois sans rechargement.');
    await page.evaluate(() => { window.slowQuarter = true; });
    await page.locator('[data-bnec-type="TRIMESTRIEL"]').click();
    await page.locator('#bnecReportPreview').click();
    await page.getByText('Calcul de l’aperçu en cours…').waitFor();
    await page.locator('[data-bnec-type="ANNUEL"]').click();
    await page.locator('#bnecReportPreview').click();
    await page.getByText('Bilan ANNUEL — ANNUEL 2026').waitFor();
    await page.waitForTimeout(450);
    assert.equal(await page.getByText('Bilan ANNUEL — ANNUEL 2026').isVisible(), true,
      'Une réponse trimestrielle tardive ne doit pas remplacer l’aperçu annuel.');
    assert.equal(await page.evaluate(() => {
      const section = document.querySelector('.bnec-report-workspace');
      return section.scrollWidth <= section.clientWidth + 2;
    }), true, 'La rubrique BNEC ne doit pas masquer ses contrôles au zoom 200 %.');
    assert.equal(await page.evaluate(() => {
      const panel = document.querySelector('#bnecReportPreviewPanel');
      return panel.scrollWidth <= panel.clientWidth + 2;
    }), true, 'Les explications longues doivent rester lisibles au zoom 200 %.');
    await page.evaluate(() => { document.body.style.zoom = '100%'; });
    await page.setViewportSize({ width: 640, height: 450 });
    assert.equal(await page.locator('#bnecReportPreview').innerText(), 'Aperçu du bilan BNEC');
    assert.equal(await page.locator('#previewReport').innerText(), 'Aperçu');
    assert.equal(await page.locator('.report-config>section').count(), 3);
    assert.equal(await page.locator('#reportRegion').isVisible(), true,
      'Le périmètre historique ne doit pas disparaître quand les bilans BNEC sont ajoutés.');
    assert.equal(await page.locator('#reportOptions').isVisible(), true,
      'Le choix du contenu historique doit rester accessible.');
    assert.equal(await page.locator('#saveReportConfig').isVisible(), true);
    await page.locator('#reportPeriod').selectOption('custom');
    await page.locator('#reportStart').fill('2026-01-01');
    await page.locator('#reportEnd').fill('2026-12-31');
    await page.locator('#reportRegion').selectOption('zone-1');
    await page.locator('#reportStatus').selectOption('ACTIF');
    await page.locator('#reportOptions input[data-section="details"]').uncheck();
    await page.locator('#saveReportConfig').click();
    assert.equal(await page.locator('#reportToast').innerText(), 'Configuration « Situation des entreprises » enregistrée pour votre compte.');
    const savedCall = await page.evaluate(() => window.calls.find(([url, body]) => url === '/api/v1/reports/configurations' && body?.model_id));
    assert.equal(savedCall[1].filtres.region, 'zone-1');
    assert.equal(savedCall[1].filtres.status, 'ACTIF');
    await page.locator('#previewReport').click();
    assert.equal(await page.locator('#reportPreview').isVisible(), true);
    assert.equal(await page.locator('#paperTable').innerText().then((text) => text.includes('Entreprise Bêta')), false);
    assert.equal(await page.locator('#paperTable').innerText().then((text) => text.includes('HAUQE-ENT-2026-0001')), true);
    assert.equal(await page.locator('#paperTable').innerText().then((text) => text.includes('Entreprise Alpha')), false,
      'La rubrique Données détaillées décochée ne doit pas apparaître dans l’aperçu.');
    await page.locator('#closePreviewFooter').click();
    assert.equal(await page.locator('#reportPreview').isVisible(), false);
    await page.locator('#previewReport').click();
    assert.equal(await page.locator('#reportPreview').isVisible(), true,
      'L’aperçu d’un export doit pouvoir se rouvrir sans rechargement.');
    await page.locator('#closePreview').click();
    await page.locator('#reportStatus').selectOption('INACTIF');
    await page.locator('#savedReports').click();
    await page.locator('[data-load-report="companies"]').click();
    await page.waitForFunction(() => document.querySelector('#reportStatus').value === 'ACTIF');
    await page.locator('[data-report="certs"]').click();
    await page.locator('#reportPeriod').selectOption('custom');
    await page.locator('#reportStart').fill('2026-01-01');
    await page.locator('#reportEnd').fill('2026-12-31');
    await page.locator('#reportStandard').selectOption('norm-1');
    await page.locator('#previewReport').click();
    assert.equal(await page.locator('#paperTable').innerText().then((text) => text.includes('CERT-ISO22000-2026-001')), true);
    assert.equal(await page.locator('#paperTable').innerText().then((text) => text.includes('CERT-ISO9001-2026-001')), false);
    await page.locator('#closePreview').click();
    await page.locator('.format-options label').filter({ has: page.locator('[name="reportFormat"][value="csv"]') }).click();
    const exportDownload = page.waitForEvent('download');
    await page.locator('#generateReport').click();
    const exportFile = await exportDownload;
    const exportContents = fs.readFileSync(await exportFile.path(), 'utf8');
    assert.equal(exportContents.includes('CERT-ISO22000-2026-001'), true);
    assert.equal(exportContents.includes('CERT-ISO9001-2026-001'), false);
    await page.evaluate(() => { window.rejectConfigSave = true; });
    await page.locator('#saveReportConfig').click();
    assert.equal(await page.locator('#reportToast').innerText(), 'Enregistrement refusé',
      'Un échec du serveur ne doit jamais afficher une fausse confirmation de sauvegarde.');
    console.log('Bilans BNEC : sélection, aperçu, génération et boutons au premier clic à 100 % et 200 %.');
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
