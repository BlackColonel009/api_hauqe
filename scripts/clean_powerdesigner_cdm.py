from __future__ import annotations

import copy
import re
from pathlib import Path

from lxml import etree

from generate_mpd_mcd_matrix import CLASSIFICATION, ROOT


SOURCE = ROOT / "output" / "Livrable v01" / "MCD_HAUQE_CERTIF_BRUT_V01.cdm"
DETAIL = ROOT / "output" / "Livrable v01" / "MCD_HAUQE_CERTIF_DETAILLE_V01.cdm"
CONTRACT = ROOT / "output" / "Livrable v01" / "MCD_HAUQE_CERTIF_CONTRACTE_V01.cdm"

NS = {"a": "attribute", "c": "collection", "o": "object"}
TECH_ATTRIBUTES = {"created_at", "updated_at"}
REMOVE_DETAIL = {
    name for name, (kind, _, _) in CLASSIFICATION.items()
    if kind in {"TECHNIQUE", "FUSION"}
}
CONTRACT_ENTITIES = {
    "entreprises", "sites_entreprise", "offres_entreprise", "organismes", "normes",
    "accreditations", "certifications", "audits_certification",
    "renouvellements_certification", "documents", "campagnes", "missions_collecte",
    "fiches_collecte", "dossiers_verification", "controles_fuccs", "validations",
    "integrations_bnec", "classifications_entreprise", "resultats_infc",
    "classements_sncc", "alertes", "dossiers_veille",
}

ASSOCIATIVE_NAMES = {
    "utilisateur_role": "Attribution de rôle",
    "role_permission": "Autorisation de permission",
    "couvertures_certification": "Couverture de certification",
    "affectations_mission": "Affectation à une mission",
    "affectations_verification": "Affectation à une vérification",
    "notes_criteres": "Évaluation d’un critère",
    "ponderations_scoring": "Pondération de scoring",
}

PAIR_VERBS = {
    frozenset(("entreprises", "certifications")): "Détenir",
    frozenset(("entreprises", "contacts_entreprise")): "Avoir pour contact",
    frozenset(("entreprises", "sites_entreprise")): "Exploiter",
    frozenset(("entreprises", "offres_entreprise")): "Proposer",
    frozenset(("organismes", "accreditations")): "Détenir",
    frozenset(("organismes", "certifications")): "Délivrer",
    frozenset(("normes", "certifications")): "Encadrer",
    frozenset(("certifications", "audits_certification")): "Faire l’objet de",
    frozenset(("certifications", "renouvellements_certification")): "Être renouvelée par",
    frozenset(("campagnes", "missions_collecte")): "Organiser",
    frozenset(("missions_collecte", "fiches_collecte")): "Produire",
    frozenset(("fiches_collecte", "dossiers_verification")): "Ouvrir",
    frozenset(("dossiers_verification", "controles_fuccs")): "Être contrôlé par",
    frozenset(("fiches_collecte", "validations")): "Recevoir",
    frozenset(("validations", "integrations_bnec")): "Autoriser",
    frozenset(("certifications", "resultats_infc")): "Recevoir",
    frozenset(("certifications", "classements_sncc")): "Être classée",
    frozenset(("certifications", "dossiers_veille")): "Être suivie par",
}


def first_text(element, xpath: str) -> str:
    node = element.find(xpath, namespaces=NS)
    return node.text if node is not None and node.text else ""


def set_text(element, xpath: str, value: str) -> None:
    node = element.find(xpath, namespaces=NS)
    if node is not None:
        node.text = value


def humanize(value: str) -> str:
    replacements = {
        "id": "Identifiant",
        "mfa": "MFA",
        "bnec": "BNEC",
        "fuccs": "FUCCS",
        "infc": "INFC",
        "sncc": "SNCC",
        "rccm": "RCCM",
        "nif": "NIF",
        "ifu": "IFU",
    }
    words = [replacements.get(part, part) for part in value.split("_")]
    label = " ".join(words)
    return label[:1].upper() + label[1:]


def collect_entities(root):
    entities = root.xpath(".//o:Entity[@Id]", namespaces=NS)
    by_id = {entity.get("Id"): entity for entity in entities}
    by_code = {first_text(entity, "a:Code"): entity for entity in entities}
    return entities, by_id, by_code


def clean_attributes(root, kept_entity_ids: set[str]) -> None:
    data_items = {
        item.get("Id"): item
        for item in root.xpath(".//o:DataItem[@Id]", namespaces=NS)
    }
    used_data_items: set[str] = set()
    for entity in root.xpath(".//o:Entity[@Id]", namespaces=NS):
        if entity.get("Id") not in kept_entity_ids:
            continue
        code = first_text(entity, "a:Code")
        for attr in list(entity.xpath("./c:Attributes/o:EntityAttribute", namespaces=NS)):
            ref_node = attr.find("c:DataItem/o:DataItem", namespaces=NS)
            ref = ref_node.get("Ref") if ref_node is not None else None
            item = data_items.get(ref)
            item_code = first_text(item, "a:Code") if item is not None else ""
            if item_code in TECH_ATTRIBUTES:
                attr.getparent().remove(attr)
                continue
            if ref:
                used_data_items.add(ref)
            if item is not None:
                name = first_text(item, "a:Name")
                if item_code == "id":
                    set_text(item, "a:Name", f"Identifiant {humanize(code).lower()}")
                elif name:
                    set_text(item, "a:Name", humanize(name))
                for tag in ("a:DataType", "a:Length", "a:Precision", "a:DefaultValue"):
                    node = item.find(tag, namespaces=NS)
                    if node is not None:
                        item.remove(node)

    for item in list(root.xpath(".//o:DataItem[@Id]", namespaces=NS)):
        if item.get("Id") not in used_data_items:
            parent = item.getparent()
            if parent is not None:
                parent.remove(item)


def remove_entities_and_links(root, remove_codes: set[str]) -> None:
    entities, by_id, by_code = collect_entities(root)
    remove_ids = {by_code[code].get("Id") for code in remove_codes if code in by_code}

    relationship_ids = set()
    for rel in list(root.xpath(".//o:Relationship[@Id]", namespaces=NS)):
        refs = {node.get("Ref") for node in rel.xpath(".//o:Entity[@Ref]", namespaces=NS)}
        if refs & remove_ids:
            relationship_ids.add(rel.get("Id"))
            rel.getparent().remove(rel)

    for symbol in list(root.xpath(".//o:RelationshipSymbol[@Id]", namespaces=NS)):
        refs = {node.get("Ref") for node in symbol.xpath(".//o:Relationship[@Ref]", namespaces=NS)}
        if refs & relationship_ids:
            symbol.getparent().remove(symbol)

    for symbol in list(root.xpath(".//o:EntitySymbol[@Id]", namespaces=NS)):
        refs = {node.get("Ref") for node in symbol.xpath(".//o:Entity[@Ref]", namespaces=NS)}
        if refs & remove_ids:
            symbol.getparent().remove(symbol)

    for entity in list(root.xpath(".//o:Entity[@Id]", namespaces=NS)):
        if entity.get("Id") in remove_ids:
            entity.getparent().remove(entity)


def rename_entities(root) -> None:
    for entity in root.xpath(".//o:Entity[@Id]", namespaces=NS):
        code = first_text(entity, "a:Code")
        if code in ASSOCIATIVE_NAMES:
            name = ASSOCIATIVE_NAMES[code]
            stereotype = entity.find("a:Stereotype", namespaces=NS)
            if stereotype is None:
                code_node = entity.find("a:Code", namespaces=NS)
                stereotype = etree.Element("{attribute}Stereotype")
                code_node.addnext(stereotype)
            stereotype.text = "Association métier"
        elif code in CLASSIFICATION:
            name = CLASSIFICATION[code][1]
            if name == "—":
                continue
        else:
            name = humanize(code)
        set_text(entity, "a:Name", name)


def rename_relationships(root) -> None:
    _, by_id, _ = collect_entities(root)
    for rel in root.xpath(".//o:Relationship[@Id]", namespaces=NS):
        refs = [node.get("Ref") for node in rel.xpath("./c:Object1/o:Entity|./c:Object2/o:Entity", namespaces=NS)]
        codes = [first_text(by_id[ref], "a:Code") for ref in refs if ref in by_id]
        if len(codes) != 2:
            continue
        verb = PAIR_VERBS.get(frozenset(codes), "Associer")
        set_text(rel, "a:Name", verb)
        set_text(rel, "a:Code", f"rel_{codes[0]}_{codes[1]}"[:60])


def update_model_identity(root, name: str) -> None:
    model = root.find(".//o:Model", namespaces=NS)
    if model is not None:
        set_text(model, "a:Name", name)
        set_text(model, "a:Code", name)


def write_tree(tree, path: Path, model_name: str) -> None:
    root = tree.getroot()
    update_model_identity(root, model_name)
    sibling = root.getprevious()
    while sibling is not None:
        if isinstance(sibling, etree._ProcessingInstruction) and sibling.target == "PowerDesigner":
            sibling.text = re.sub(r'Name="[^"]*"', f'Name="{model_name}.cdm"', sibling.text)
            break
        sibling = sibling.getprevious()
    tree.write(
        str(path),
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True,
        standalone=None,
    )


def transform(tree, remove_codes: set[str], output: Path, model_name: str) -> None:
    root = tree.getroot()
    remove_entities_and_links(root, remove_codes)
    _, by_id, _ = collect_entities(root)
    clean_attributes(root, set(by_id))
    rename_entities(root)
    rename_relationships(root)
    write_tree(tree, output, model_name)


def build() -> None:
    parser = etree.XMLParser(remove_blank_text=False, remove_comments=False)
    source_tree = etree.parse(str(SOURCE), parser)

    detail_tree = copy.deepcopy(source_tree)
    transform(
        detail_tree,
        REMOVE_DETAIL,
        DETAIL,
        "MCD_HAUQE_CERTIF_DETAILLE_V01",
    )

    all_codes = set(CLASSIFICATION)
    contract_tree = copy.deepcopy(source_tree)
    transform(
        contract_tree,
        all_codes - CONTRACT_ENTITIES,
        CONTRACT,
        "MCD_HAUQE_CERTIF_CONTRACTE_V01",
    )

    for label, path in (("detail", DETAIL), ("contract", CONTRACT)):
        text = path.read_text(encoding="utf-8")
        print(
            label,
            "entities=", len(re.findall(r'<o:Entity Id="', text)),
            "attributes=", len(re.findall(r'<o:EntityAttribute Id="', text)),
            "relationships=", len(re.findall(r'<o:Relationship Id="', text)),
            path,
        )


if __name__ == "__main__":
    build()
