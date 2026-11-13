const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('app/static/js/rapports.js','utf8');
test('fresh preview close button responds repeatedly, including icon clicks',()=>{
  const overlay={hidden:false};
  const original={attributes:[{name:'id',value:'closePreview'}],innerHTML:'<i></i>',replaceWith(button){this.replacement=button;}};
  const context={$:(s)=>s==='#reportPreview'?overlay:original,document:{createElement:()=>({setAttribute(){},addEventListener(type,fn){this.click=fn;}})}};
  vm.createContext(context);
  vm.runInContext(source.slice(source.indexOf('  function bindPreviewAction'),source.indexOf('  $("#reportPeriod").onchange')),context);
  context.bindPreviewAction('#closePreview',context.closeReportPreview);
  assert.equal(original.replacement.type,'button');
  for(let i=0;i<3;i++){
    overlay.hidden=false;
    original.replacement.click({preventDefault(){},stopPropagation(){},target:{tagName:'svg'}});
    assert.equal(overlay.hidden,true);
  }
});
test('both close controls use direct binding and hidden wins over display styles',()=>{
  assert.match(source,/mountPreviewCloseButton\(\);/);
  assert.match(source,/bindPreviewAction\("#closePreviewFooter", closeReportPreview\)/);
  const css=fs.readFileSync('app/static/css/rapports.css','utf8');
  assert.match(css,/\.report-preview-overlay\[hidden\]\{display:none!important\}/);
});
test('X is mounted fresh on every opening with its own click listener',()=>{
  const overlay={hidden:false}, slot={replaceChildren(button){this.button=button;}};
  const context={$:s=>s==='#reportPreview'?overlay:slot,document:{createElement:()=>({setAttribute(){},addEventListener(type,fn){this.click=fn;}})}};
  vm.createContext(context);
  vm.runInContext(source.slice(source.indexOf('  function closeReportPreview'),source.indexOf('  $("#reportPeriod").onchange')),context);
  let previous;
  for(let i=0;i<3;i++){
    overlay.hidden=false;
    context.mountPreviewCloseButton();
    assert.notEqual(slot.button,previous);
    slot.button.click({preventDefault(){},stopPropagation(){}});
    assert.equal(overlay.hidden,true);
    previous=slot.button;
  }
});
