import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const p = "C:/Users/hp/Downloads/Fiche de présence_Mission GFA_ISTE_7751340 (3).xlsx";
const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(p));
const s = wb.worksheets.getItem("Fiche de présence");
for (const cell of ["C20", "C21", "D20", "E20", "F20"]) {
  const r = s.getRange(cell);
  console.log(cell, JSON.stringify(r.dataValidation));
}
console.log((await wb.inspect({kind:"region", sheetId:"Listen", range:"A1:O30", maxChars:12000})).ndjson);
