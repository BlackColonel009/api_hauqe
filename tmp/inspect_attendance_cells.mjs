import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "C:/Users/hp/Downloads/Fiche de présence_Mission GFA_ISTE_7751340 (3).xlsx";
const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
const sheet = wb.worksheets.getItem("Fiche de présence");
for (const rangeName of ["B1:H18", "B19:H52", "B53:H60"]) {
  const r = sheet.getRange(rangeName);
  console.log(JSON.stringify({ range: rangeName, values: r.values, formulas: r.formulas }, null, 2));
}
console.log((await wb.inspect({kind:"computedStyle", sheetId:"Fiche de présence", range:"B1:H55", maxChars:8000})).ndjson);
