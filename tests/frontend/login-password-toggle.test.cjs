const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
test('fresh password control toggles on every click and preserves input value',()=>{
  const source=fs.readFileSync('app/static/js/connexion.js','utf8');
  const code=source.slice(source.indexOf('  function mountPasswordToggle()'),source.indexOf('  loginForm.addEventListener'));
  const input={type:'password',value:'unchanged',disabled:false};
  const slash={style:{}};
  let mounted,handler,created=0;
  const slot={replaceChildren(button){mounted=button}};
  const button={setAttribute(k,v){this[k]=v},querySelector(){return slash},addEventListener(k,h){handler=h}};
  vm.runInNewContext(code,{$:()=>slot,passwordInput:input,document:{createElement(){created++;return button}}});
  assert.equal(created,1);
  assert.equal(mounted['data-no-action-loader'],'true');
  for(let i=0;i<20;i++){
    handler({preventDefault(){},stopPropagation(){}});
    assert.equal(input.type,i%2===0?'text':'password');
    assert.equal(mounted['aria-pressed'],String(i%2===0));
    assert.equal(input.value,'unchanged');
  }
  input.disabled=true;
  handler({preventDefault(){},stopPropagation(){}});
  assert.equal(input.type,'password');
  assert.equal(created,1);
});
