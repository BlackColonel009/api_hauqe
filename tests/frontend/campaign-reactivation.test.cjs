const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('app/static/js/campagnes-collecte.js','utf8');
function setup(confirm=true,fail=false){
  const calls=[];
  const ctx={window:{confirm:()=>confirm},apiPatch:async(...args)=>{calls.push(args);if(fail)throw Error('Refus');},loadCampaigns:async()=>calls.push('reload'),showState:(...args)=>calls.push(args)};
  vm.createContext(ctx);
  vm.runInContext('let actionInProgress=false;'+source.slice(source.indexOf('  async function reactivateCampaign'),source.indexOf('  // Les lignes sont redessinées')),ctx);
  return {ctx,calls};
}
test('reactivation changes only status after confirmation',async()=>{
  const {ctx,calls}=setup();await ctx.reactivateCampaign({id:'c1',code:'CAMP-1'});
  assert.equal(calls[0][0],'/api/v1/campagnes/c1');
  assert.equal(JSON.stringify(calls[0][1]),'{"statut":"ACTIVE"}');
  assert.equal(calls[1],'reload');
});
test('cancel leaves campaign untouched',async()=>{
  const {ctx,calls}=setup(false);await ctx.reactivateCampaign({id:'c1'});assert.equal(calls.length,0);
});
test('failure releases action lock to allow retry',async()=>{
  const {ctx,calls}=setup(true,true);await ctx.reactivateCampaign({id:'c1'});await ctx.reactivateCampaign({id:'c1'});
  assert.equal(calls.filter(x=>Array.isArray(x)&&x[0]==='/api/v1/campagnes/c1').length,2);
});
