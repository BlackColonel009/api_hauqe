import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "C:/Users/hp/Downloads/Fiche de présence_Mission GFA_ISTE_7751340 (3).xlsx";
const outputDir = "tmp/attendance_rebuild_3";
const previewDir = "tmp/attendance_rebuild_3_previews";
await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const months = [
  {
    month: "Juillet",
    slug: "Juillet_2026",
    entries: [
      [13, 1, "Lomé", "Réunion de cadrage HAUQE/GFA : besoins, méthodologie, planning et livrables."],
      [14, 0.5, "Télétravail", "Analyse des TDR, du contrat et du corpus documentaire de la mission."],
      [15, 1, "Télétravail", "Méthodologie d’intervention et planification détaillée des travaux."],
      [17, 1, "Télétravail", "Architecture fonctionnelle, MCD, MLD et dictionnaire de données du SNGSC."],
      [20, 1, "Télétravail", "Architecture technique : PostgreSQL, FastAPI et composants applicatifs."],
      [21, 1, "Télétravail", "Développement des modules Entreprises, Organismes, Certifications et Référentiels."],
      [22, 1, "Télétravail", "Mise en place des utilisateurs, rôles, permissions et mécanismes de sécurité."],
      [24, 1, "Lomé", "Seconde réunion de travail : revue des outils, ajustements et validation des orientations."],
      [27, 1, "Télétravail", "Développement des campagnes, missions, fiches numériques et contrôles de complétude."],
      [28, 1, "Télétravail", "Développement de la vérification, du contrôle FUCCS et des corrections."],
      [30, 1, "Télétravail", "Développement des processus de validation et d’intégration dans la BNEC."],
      [31, 1, "Télétravail", "Préparation des données collectées et définition des formats d’importation."],
    ],
  },
  {
    month: "Août",
    slug: "Aout_2026",
    entries: [
      [3, 1, "Télétravail", "Nettoyage, contrôle de complétude et harmonisation des données collectées."],
      [4, 1, "Télétravail", "Rapprochement des codes, référentiels, entreprises et organismes certificateurs."],
      [5, 1, "Télétravail", "Intégration progressive des données des entreprises dans la base nationale."],
      [7, 1, "Télétravail", "Intégration des certifications, organismes, référentiels et pièces associées."],
      [10, 1, "Télétravail", "Détection des doublons, correction des rejets et reprise des données non conformes."],
      [11, 1, "Télétravail", "Contrôle post-intégration, rapprochement des totaux et validation de la cohérence."],
      [12, 0.5, "Télétravail", "Paramétrage des mécanismes INFC, SNCC, statuts et transitions métier."],
      [14, 1, "Télétravail", "Développement des échéances, alertes, notifications, relances et dossiers de veille."],
      [17, 1, "Télétravail", "Consolidation des tableaux de bord, indicateurs, rapports et outils de pilotage."],
      [18, 1, "Télétravail", "Tests fonctionnels, corrections et mise à jour des guides d’utilisation."],
      [19, 1, "Télétravail", "Préparation des supports, exercices et environnement de formation."],
    ],
  },
  {
    month: "Septembre",
    slug: "Septembre_2026",
    entries: [
      [22, 1, "Lomé", "Formation : présentation du SNGSC, administration, rôles, accès et sécurité."],
      [23, 1, "Lomé", "Formation pratique : collecte, vérification, contrôle, validation et intégration BNEC."],
      [24, 1, "Lomé", "Formation et transfert de compétences : INFC, SNCC, alertes, veille et tableaux de bord."],
    ],
  },
];

for (const item of months) {
  const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
  const sheet = workbook.worksheets.getItem("Fiche de présence");

  sheet.getRange("F3").values = [[null]];
  sheet.getRange("F5").values = [["PSD-TGO23GIZ0271"]];
  sheet.getRange("F9").values = [["7751340"]];
  sheet.getRange("F11").values = [["DJAGBA Roland Fo Doh"]];
  sheet.getRange("F13").values = [["Expert national en bases de données et systèmes d’information"]];
  sheet.getRange("C15").values = [[item.month]];
  sheet.getRange("G15").values = [[2026]];

  for (const [day, workDays, place, activity] of item.entries) {
    const row = 19 + day;
    sheet.getRange(`C${row}`).values = [[workDays]];
    sheet.getRange(`G${row}`).values = [[place]];
    sheet.getRange(`H${row}`).values = [[activity]];
  }

  const output = await SpreadsheetFile.exportXlsx(workbook);
  const outputPath = `${outputDir}/Fiche_presence_Roland_DJAGBA_${item.slug}.xlsx`;
  await output.save(outputPath);

  const preview = await workbook.render({
    sheetName: "Fiche de présence",
    range: "B1:H60",
    scale: 1.5,
    format: "png",
  });
  await fs.writeFile(
    `${previewDir}/Fiche_presence_Roland_DJAGBA_${item.slug}.png`,
    new Uint8Array(await preview.arrayBuffer()),
  );

  const check = await workbook.inspect({
    kind: "table",
    sheetId: "Fiche de présence",
    range: "B1:H52",
    include: "values,formulas",
    tableMaxRows: 55,
    tableMaxCols: 7,
    maxChars: 16000,
  });
  await fs.writeFile(`${previewDir}/${item.slug}_check.ndjson`, check.ndjson, "utf8");
}
