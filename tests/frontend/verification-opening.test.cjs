const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
test('opening confirms mission priority and provides five ordered risks',()=>{
 const js=fs.readFileSync('app/static/js/core/verification-opening.js','utf8');
 assert.match(js,/form.elements.priority.value=mission.priorite/);
 assert.match(js,/Confirmez-vous cette priorité initiale du dossier/);
 for(let i=1;i<=5;i++)assert.match(js,new RegExp(`option value="R${i}"`));
 assert.match(js,/data-no-action-loader/);
 assert.match(js,/themed-business-dialog/);
});
