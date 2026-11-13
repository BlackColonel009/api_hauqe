const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app/static/js/entreprise-form.js', 'utf8');
test('render never recaptures stale inputs after changing structured rows', () => {
  const render = source.slice(source.indexOf('  function renderStep()'), source.indexOf('  function validCurrentStep()'));
  assert.doesNotMatch(render, /captureCompanyFields\(/);
});
for (const kind of ['contacts', 'sites', 'offers']) {
  for (const editing of [false, true]) {
    test(`${kind}: consecutive removals preserve remaining identities (${editing ? 'edit' : 'create'})`, () => {
      let captures = 0, renders = 0;
      const context = {state: {[kind]: [{id: editing ? 'a' : null, nom:'A'}, {id:editing ? 'b' : null, nom:'B'}, {id:editing ? 'c' : null, nom:'C'}], removed:{[kind]:new Set()}}, captureCompanyFields:()=>captures++, renderStep:()=>renders++};
      vm.createContext(context);
      vm.runInContext(source.slice(source.indexOf('  function removeStructuredEntry'), source.indexOf('  function bindStructured')), context);
      context.removeStructuredEntry(kind, 1);
      assert.equal(context.state[kind].map(x=>x.nom).join(','), 'A,C');
      context.removeStructuredEntry(kind, 0);
      assert.equal(context.state[kind][0].nom, 'C');
      assert.equal(captures, 2);
      assert.equal(renders, 2);
      assert.equal([...context.state.removed[kind]].join(','), editing ? 'b,a' : '');
    });
  }
}
test('initial actions are fresh native buttons excluded from automatic busy handling', () => {
  const bind = source.slice(source.indexOf('  function recreateActionButton'), source.indexOf('  async function load()'));
  assert.match(bind, /document.createElement\('button'\)/);
  assert.match(bind, /data-no-action-loader/);
  assert.match(bind, /original.replaceWith\(button\)/);
  assert.doesNotMatch(bind, /cloneNode/);
});
