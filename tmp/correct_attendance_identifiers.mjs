import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const sourceDir = "output/fiches_presence";
const tempDir = "tmp/attendance_identifier_update";
await fs.mkdir(tempDir, { recursive: true });

const files = [
  "Fiche_presence_Roland_DJAGBA_Juin_2026.xlsx",
  "Fiche_presence_Roland_DJAGBA_Juillet_2026.xlsx",
  "Fiche_presence_Roland_DJAGBA_Aout_2026.xlsx",
  "Fiche_presence_Roland_DJAGBA_Septembre_2026.xlsx",
];

for (const file of files) {
  const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(sourceDir, file)));
  const sheet = workbook.worksheets.getItem("Fiche de présence");

  sheet.getRange("F3").values = [[null]];
  sheet.getRange("F5").values = [["PSD-TGO23GIZ0271"]];
  sheet.getRange("F9").values = [["7751340"]];

  const check = await workbook.inspect({
    kind: "table",
    sheetId: "Fiche de présence",
    range: "B1:H15",
    include: "values,formulas",
    tableMaxRows: 15,
    tableMaxCols: 7,
    maxChars: 5000,
  });
  await fs.writeFile(path.join(tempDir, `${file}.check.ndjson`), check.ndjson, "utf8");

  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    summary: "formula error scan",
  });
  await fs.writeFile(path.join(tempDir, `${file}.errors.ndjson`), errors.ndjson, "utf8");

  const preview = await workbook.render({
    sheetName: "Fiche de présence",
    range: "B1:H15",
    scale: 1.5,
    format: "png",
  });
  await fs.writeFile(path.join(tempDir, `${file}.png`), new Uint8Array(await preview.arrayBuffer()));

  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(path.join(tempDir, file));
}
