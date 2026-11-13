const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
test('enhancer ignores its own mutations and reconnects after icon conversion',()=>{
  let observing=false, icons=0, handler, pending=true;
  const page={};
  const context={location:{hash:'#/entreprises/nouveau'},document:{readyState:'complete',querySelector:s=>s==='#pageContent'?page:s==='#pageContent i[data-lucide]'&&pending?{}:null},window:{addEventListener:(name,fn)=>handler=fn,lucide:{createIcons(){assert.equal(observing,false);pending=false;icons++;}}},MutationObserver:class{disconnect(){observing=false;}observe(){observing=true;}},clearTimeout(){},setTimeout(){}};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync('app/static/js/core/business-rules-ui.js','utf8'),context);
  handler();
  assert.equal(icons,1); assert.equal(observing,true);
  handler();
  assert.equal(icons,1); assert.equal(observing,true);
});
