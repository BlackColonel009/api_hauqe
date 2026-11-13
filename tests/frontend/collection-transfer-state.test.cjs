const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('app/static/js/core/collection-transfer.js','utf8');
const ctx={};vm.createContext(ctx);
vm.runInContext(source.slice(0,source.indexOf('export function installCollectionTransfer')).replace('export ',''),ctx);
test('mission options explicitly distinguish archived and non archived status',()=>{
  assert.equal(ctx.missionStateLabel('ARCHIVEE'),'Archivée — désarchivage requis');
  assert.equal(ctx.missionStateLabel('PLANIFIEE'),'Non archivée — Planifiée');
  assert.equal(ctx.missionStateLabel('EN_COURS'),'Non archivée — En cours');
  assert.equal(ctx.missionStateLabel('ANNULEE'),'Annulée');
});
