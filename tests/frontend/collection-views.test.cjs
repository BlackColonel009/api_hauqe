const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
test('collection views share action hydration and clear the inactive DOM',()=>{
 const js=fs.readFileSync('app/static/js/collectes.js','utf8');
 assert.match(js,/grid\.replaceChildren\(\)/);
 assert.match(js,/tbody\.replaceChildren\(\)/);
 assert.match(js,/hydrateCampaignTreeButtons\(campaignGroups\)/);
 assert.match(js,/registryView=mode/);
 assert.match(js,/if\(lastRegistryPayload\)renderRows\(lastRegistryPayload\)/);
 const css=fs.readFileSync('app/static/css/collectes.css','utf8');
 assert.match(css,/#collecteGridView\[hidden\]/);
 assert.match(css,/max-width:1000px/);
});
