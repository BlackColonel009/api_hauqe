const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
function setup(){
  const ctx={document:{querySelector:()=>null,createElement:()=>{throw Error('Unexpected display');}},console};
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync('app/static/js/core/draft-reminder.js','utf8').replaceAll('export ',''),ctx);
  return ctx;
}
test('no draft produces no reminder and duplicate initialization sends one request',async()=>{
  const ctx=setup();let calls=0;
  const get=async()=>{calls++;return {total:0};};
  await ctx.showDraftReminder(get);await ctx.showDraftReminder(get);
  assert.equal(calls,1);
});
test('logout invalidates an old response and next session is checked again',async()=>{
  const ctx=setup();let finish;
  const pending=ctx.showDraftReminder(()=>new Promise(resolve=>finish=resolve));
  ctx.clearDraftReminder();finish({total:1,items:[{}]});await pending;
  let calls=0;await ctx.showDraftReminder(async()=>{calls++;return {total:0};});
  assert.equal(calls,1);
});
test('bell schedules one or two strikes without blocking when autoplay is denied',async()=>{
  const ctx=setup();let strikes=0,resumes=0;
  ctx.AudioContext=class{
    state='suspended';currentTime=0;destination={};
    async resume(){this.state='running';resumes++;}
    createOscillator(){return {frequency:{},connect(){},start(){strikes++;},stop(){},disconnect(){}};}
    createGain(){return {gain:{setValueAtTime(){},exponentialRampToValueAtTime(){}},connect(){},disconnect(){}};}
    async close(){this.state='closed';}
  };
  await ctx.ringDraftBell(1);
  assert.equal(strikes,0);assert.equal(resumes,0);
  await ctx.ringDraftBell(2,true);
  assert.equal(strikes,6); // 3 partiels pour chacun des 2 coups.
  await ctx.ringDraftBell(1,true);
  assert.equal(strikes,9);
  ctx.clearDraftReminder();
});
