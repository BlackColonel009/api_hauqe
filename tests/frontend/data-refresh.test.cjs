const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function runtime() {
  const source = fs.readFileSync('app/static/js/core/app-shell.js', 'utf8');
  const code = source.slice(source.indexOf('const PAGE_REFRESH_STORAGE_KEY'),
    source.indexOf('function installPageRefreshButton'));
  const root = { isConnected: true, querySelector: () => null };
  const flags = { dialog: false, input: false, busy: false, reloads: 0 };
  const listeners = {};
  const context = {
    window: {}, location: { hash: '#/entreprises' }, console,
    hasAccessToken: () => true, getCurrentRoute: () => 'entreprises',
    refreshCurrentRoute: async () => { flags.reloads++; },
    document: {
      hidden: false, activeElement: null,
      querySelectorAll: () => [],
      addEventListener: (name, callback) => { listeners[name] = callback; },
      body: { classList: { contains: () => flags.busy } },
      querySelector: (selector) => selector === '#pageContent'
        ? { firstElementChild: root }
        : selector.startsWith('dialog') ? (flags.dialog ? {} : null) : null,
    },
    CustomEvent: class {}, Intl, Date,
  };
  context.window.dispatchEvent = () => {};
  context.window.addEventListener = (name, callback) => { listeners[name] = callback; };
  vm.createContext(context);
  vm.runInContext(code, context);
  vm.runInContext(source.slice(source.indexOf('document.addEventListener("input"'),
    source.indexOf('window.addEventListener("hauqe:refresh-preferences-updated"')), context);
  return { context, flags, root, listeners, run: (code) => vm.runInContext(code, context) };
}

test('automatic refresh loads data without navigation', async () => {
  const r = runtime(); let applied = 0;
  r.context.window.HAUQE_REGISTER_DATA_REFRESH(async ({ shouldApply }) => {
    if (shouldApply()) applied++;
  });
  await r.run('refreshCollaborativePage()');
  assert.equal(applied, 1);
  assert.equal(r.flags.reloads, 0);
});

test('open modal, dirty form, hidden tab and running action suspend refresh', async () => {
  const r = runtime(); let calls = 0;
  r.context.window.HAUQE_REGISTER_DATA_REFRESH(async () => calls++);
  r.flags.dialog = true; await r.run('refreshCollaborativePage()');
  r.flags.dialog = false;
  r.run('pageFormDirty = true'); await r.run('refreshCollaborativePage()');
  r.run('pageFormDirty = false');
  r.context.document.hidden = true; await r.run('refreshCollaborativePage()');
  r.context.document.hidden = false;
  r.flags.busy = true; await r.run('refreshCollaborativePage()');
  assert.equal(calls, 0);
});

test('response is discarded if modal opens or page changes during request', async () => {
  for (const mutate of [r => { r.flags.dialog = true; },
    r => { r.context.location.hash = '#/certifications'; },
    r => { r.root.isConnected = false; }]) {
    const r = runtime(); let applied = false;
    r.context.window.HAUQE_REGISTER_DATA_REFRESH(async ({ shouldApply }) => {
      mutate(r); applied = shouldApply();
    });
    await r.run('refreshCollaborativePage()');
    assert.equal(applied, false);
  }
});

test('unregistered screen is not reloaded and preferences disable refresh', async () => {
  const r = runtime();
  assert.equal(await r.run('refreshCollaborativePage()'), false);
  r.context.window.HAUQE_REGISTER_DATA_REFRESH(async () => {});
  r.run('pageRefreshPreferences.enabled = false');
  assert.equal(await r.run('refreshCollaborativePage()'), false);
  assert.equal(r.flags.reloads, 0);
});

test('closed managed native dialog with aria-modal does not block polling', async () => {
  const r = runtime(); let calls = 0;
  const originalQuery = r.context.document.querySelector;
  r.context.document.querySelector = selector => {
    // Model the companyActionDialog after normalizeDialog: aria-modal=true,
    // no hidden attribute, but no open attribute either.
    if (selector.includes("[aria-modal='true']:not([hidden])")) return {};
    return originalQuery(selector);
  };
  r.context.window.HAUQE_REGISTER_DATA_REFRESH(async () => calls++);
  await r.run('refreshCollaborativePage()');
  assert.equal(calls, 1);
  r.flags.dialog = true;
  await r.run('refreshCollaborativePage()');
  assert.equal(calls, 1);
  r.flags.dialog = false;
  await r.run('refreshCollaborativePage()');
  assert.equal(calls, 2);
});

test('custom aria-modal blocks only while visibly displayed', () => {
  const r = runtime(); let visible = false;
  r.context.document.querySelectorAll = () => [{getClientRects: () => visible ? [{}] : []}];
  r.context.window.getComputedStyle = () => ({visibility:'visible'});
  assert.equal(r.run('pageHasOpenDialog()'), false);
  visible = true;
  assert.equal(r.run('pageHasOpenDialog()'), true);
});

test('editing modal then closing resumes polling without clearing its draft', async () => {
  const r = runtime(); let calls = 0;
  const form = {closest: () => ({})};
  const target = {value:'brouillon conservé',closest: () => form,matches: () => false};
  r.context.window.HAUQE_REGISTER_DATA_REFRESH(async () => calls++);
  r.flags.dialog = true;
  r.listeners.input({target}); r.listeners.change({target});
  await r.run('refreshCollaborativePage()');
  assert.equal(calls, 0);
  r.flags.dialog = false;
  await r.run('refreshCollaborativePage()');
  assert.equal(calls, 1);
  assert.equal(target.value, 'brouillon conservé');
});

test('editing inline form still blocks refresh', async () => {
  const r = runtime(); let calls = 0;
  r.context.window.HAUQE_REGISTER_DATA_REFRESH(async () => calls++);
  r.listeners.input({target:{closest:()=>({closest:()=>null}),matches:()=>false}});
  await r.run('refreshCollaborativePage()');
  assert.equal(calls, 0);
});

test('stale page initialization cannot register a loader on the next page', async () => {
  const r = runtime(); let calls = 0;
  const register = r.context.window.HAUQE_CAPTURE_DATA_REFRESH();
  r.context.location.hash = '#/certifications';
  register(async () => calls++);
  await r.run('refreshCollaborativePage()');
  assert.equal(calls, 0);
});

test('refresh timestamp includes seconds and changes only on success', async () => {
  const r = runtime();
  const stamp = {dataset:{},textContent:'Actualisé à —'};
  r.root.querySelector = selector => selector === '#companiesSyncAt'
    || selector === '[data-data-refresh-time]' ? stamp : null;
  r.context.window.HAUQE_REGISTER_DATA_REFRESH(async () => {});
  await r.run('refreshCollaborativePage()');
  assert.match(stamp.textContent, /^Actualisé à \d{2}:\d{2}:\d{2}$/);
  const previous = stamp.textContent;
  r.context.console = {warn:()=>{}};
  r.context.window.HAUQE_REGISTER_DATA_REFRESH(async () => {throw new Error('SMTP unrelated: API unavailable');});
  await r.run('refreshCollaborativePage()');
  assert.equal(stamp.textContent, previous);
});

test('pointer interaction suspends data commits to preserve button clicks', async () => {
  const r = runtime(); let calls = 0;
  r.context.window.HAUQE_REGISTER_DATA_REFRESH(async () => calls++);
  r.listeners.pointerdown({target:{closest:()=>({})}});
  await r.run('refreshCollaborativePage()');
  assert.equal(calls, 0);
});

test('all sixteen connected pages capture their original page before loading', () => {
  for (const page of ['app','entreprises','certifications','collectes','verifications',
    'validations','integrations','alertes','echeances','organismes','campagnes-collecte',
    'controle','scoring','infc','classement-sncc','veille']) {
    const source = fs.readFileSync(`app/static/js/${page}.js`, 'utf8');
    assert.ok(source.includes('HAUQE_CAPTURE_DATA_REFRESH'), page);
    assert.ok(source.includes('registerDataRefresh?.('), page);
  }
});
