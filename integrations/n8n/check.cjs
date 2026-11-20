// Validate expressions with the exact installed n8n parser before importing a workflow.
const assert=require('node:assert/strict');
const workflow=require('./sec-company-review.json');
const {extendSyntax}=require('../../.tools/n8n/node_modules/n8n-workflow/dist/cjs/extensions/expression-extension.js');
let expressions=0;
function walk(value){
  if(typeof value==='string'&&value.startsWith('={{')){extendSyntax(value);expressions++;}
  else if(Array.isArray(value))value.forEach(walk);
  else if(value&&typeof value==='object')Object.values(value).forEach(walk);
}
walk(workflow);
assert.equal(workflow.settings.timezone,'UTC');
assert.equal(workflow.settings.saveDataErrorExecution,'none');
assert.equal(workflow.settings.saveDataSuccessExecution,'none');
assert(expressions>=3);
console.log('Workflow expressions and metadata checked with the pinned n8n parser.');
