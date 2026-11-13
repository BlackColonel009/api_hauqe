const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app/static/js/rapports.js','utf8');
const context = {exportMeta:{companies:{date:'created_at',region:'zone_siege_id',status:'statut'}}};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('function normalizeAddress'),source.indexOf('  const frDate'))
  + source.slice(source.indexOf('  function filterExportRows'),source.indexOf('  async function loadFilteredExport')), context);
const rows = [
  {id:'a',created_at:'2026-10-01',adresse_siege:'KPALIME ADOLO',genre_promoteur:'FEMME'},
  {id:'b',created_at:'2026-10-02',adresse_siege:'Adolo quartier nord',genre_promoteur:'HOMME'},
  {id:'c',created_at:'2026-10-02',adresse_siege:'Lomé',genre_promoteur:null},
];
const run = (extra={}) => context.filterExportRows(rows,{id:'companies'},{start:'2026-10-01',end:'2026-10-31',...extra}).map(x=>x.id).join(',');
test('partial address includes every matching company, without choosing a suggestion',()=>assert.equal(run({adresse:'  adolo  '}),'a,b'));
test('address search ignores case and accents',()=>assert.equal(run({adresse:'LOME'}),'c'));
test('gender combines with partial address',()=>assert.equal(run({adresse:'ADOLO',genre:'FEMME'}),'a'));
test('unknown gender is selectable and never inferred from other fields',()=>assert.equal(run({genre:'NON_RENSEIGNE'}),'c'));
test('existing period filters remain effective',()=>assert.equal(run({start:'2026-10-02',adresse:'ADOLO'}),'b'));
test('all periods includes older and undated rows instead of silently emptying the register',()=>{
  const sample=[...rows,{id:'old',created_at:'2026-09-01'},{id:'undated'}];
  assert.equal(context.filterExportRows(sample,{id:'companies'},{start:null,end:null}).length,5);
  assert.equal(context.filterExportRows(sample,{id:'companies'},{start:null,end:null,genre:'FEMME'}).length,1);
});
test('business modal fields use the shared operational field theme',()=>{
  for (const [file,ids] of [['alertes',['alertResolution']],['veille',['watchReportType','watchReportStart','watchReportEnd']]]) {
    const html=fs.readFileSync(`app/templates/views/${file}.html`,'utf8');
    for (const id of ids) assert.match(html,new RegExp('<label class="operational-field"><span>[^<]*(?:<b>.*?</b>)?</span><(?:input|textarea) id="'+id+'"'));
  }
  const css=fs.readFileSync('app/static/css/business-dialogs.css','utf8');
  assert.match(css,/\[data-theme="dark"\] .themed-business-dialog .operational-field/);
  assert.match(css,/\.switch-line input/);
});
test('modal templates keep event IDs, common theme and scroll class',()=>{
  for(const [file,id,form] of [['alertes','resolveAlertDialog','resolveAlertForm'],['veille','watchReportDialog','watchReportForm']]){
    const html=fs.readFileSync(`app/templates/views/${file}.html`,'utf8');
    const start=html.indexOf('id="'+id+'"');
    assert.ok(start>=0);
    const modal=html.slice(html.lastIndexOf('<dialog',start),html.indexOf('</dialog>',start));
    for(const token of [form,'operational-form-dialog','operational-dialog-header','themed-business-body','operational-dialog-footer']) assert.ok(modal.includes(token),token);
  }
});
