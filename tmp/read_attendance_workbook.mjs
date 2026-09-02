import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "C:/Users/hp/Downloads/Fiche de présence_Mission GFA_ISTE_7751340 (3).xlsx";
const outDir = "tmp/attendance_review";
await fs.mkdir(outDir, { recursive: true });

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
const overview = await workbook.inspect({
  kind: "workbook,sheet,table,definedName,drawing",
  maxChars: 12000,
  tableMaxRows: 12,
  tableMaxCols: 20,
  tableMaxCellChars: 160,
});
await fs.writeFile(`${outDir}/overview.ndjson`, overview.ndjson, "utf8");

const sheets = await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 8000 });
await fs.writeFile(`${outDir}/sheets.ndjson`, sheets.ndjson, "utf8");

const summary = [];
for (const sheet of workbook.worksheets.items) {
  const used = sheet.getUsedRange();
  const address = used?.address ?? null;
  const values = used?.values ?? [];
  summary.push({ name: sheet.name, address, values });
  const preview = await workbook.render({ sheetName: sheet.name, autoCrop: "all", scale: 1.4, format: "png" });
  const safe = sheet.name.replace(/[\\/:*?"<>|]/g, "_");
  await fs.writeFile(`${outDir}/${safe}.png`, new Uint8Array(await preview.arrayBuffer()));
}
await fs.writeFile(`${outDir}/used-ranges.json`, JSON.stringify(summary, null, 2), "utf8");
