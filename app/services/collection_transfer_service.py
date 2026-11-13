from datetime import date
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func, or_

from app.models.fiche_collecte import FicheCollecte
from app.models.mission_collecte import MissionCollecte
from app.models.campagne import Campagne
from app.models.entreprise import Entreprise
from app.models.affectation_mission import AffectationMission
from app.audit.service import write_audit_event


def ensure_manager(actor):
    if not set(actor.roles).intersection({'ADMIN_HAUQE', 'POINT_FOCAL_BNEC'}):
        raise HTTPException(403, 'Action réservée au point focal et à l’administrateur HAUQE.')


async def list_dossiers(db, mission_id):
    rows = (await db.execute(select(FicheCollecte, Entreprise.raison_sociale)
        .outerjoin(Entreprise, Entreprise.id == FicheCollecte.entreprise_id)
        .where(FicheCollecte.mission_id == mission_id)
        .order_by(FicheCollecte.numero_revision.desc().nullslast(), FicheCollecte.created_at.desc()))).all()
    grouped = {}
    for fiche, name in rows:
        key = fiche.dossier_id or fiche.id
        if key not in grouped:
            grouped[key] = {'fiche_id': str(fiche.id), 'entreprise': name or 'Entreprise à renseigner',
                            'statut': fiche.statut, 'revisions': 0}
        grouped[key]['revisions'] += 1
    return {'items': list(grouped.values()), 'total_fiches': len(rows)}


async def transfer(db, source_id, payload, actor, request):
    ensure_manager(actor)
    if source_id == payload.destination_id:
        raise HTTPException(400, 'La mission destination doit être différente.')
    # Ordre stable pour empêcher deux transferts opposés de se bloquer.
    missions = (await db.execute(select(MissionCollecte)
        .where(MissionCollecte.id.in_([source_id, payload.destination_id]))
        .order_by(MissionCollecte.id).with_for_update())).scalars().all()
    by_id = {m.id: m for m in missions}
    if len(by_id) != 2:
        raise HTTPException(404, 'Mission introuvable.')
    destination = by_id[payload.destination_id]
    if (destination.statut or '').upper() in {'ARCHIVEE', 'ANNULEE'}:
        raise HTTPException(409, 'La mission destination est archivée ou annulée.')
    campaign = await db.get(Campagne, destination.campagne_id)
    if not campaign or (campaign.statut or '').upper() not in {'ACTIVE', 'ACTIF'}:
        raise HTTPException(409, 'La campagne destination doit être active.')
    rows = (await db.execute(select(FicheCollecte).where(FicheCollecte.mission_id == source_id)
                              .with_for_update())).scalars().all()
    selected = set(payload.fiche_ids)
    if not selected.issubset({f.id for f in rows}):
        raise HTTPException(409, 'Une collecte sélectionnée ne se trouve plus dans cette mission.')
    roots = {f.dossier_id or f.id for f in rows if f.id in selected}
    moved = [f for f in rows if (f.dossier_id or f.id) in roots]
    # Une entreprise peut avoir plusieurs dossiers ; ne jamais les fusionner.
    company_ids = {f.entreprise_id for f in moved if f.entreprise_id}
    conflict = (await db.execute(select(FicheCollecte.id).where(
        FicheCollecte.mission_id == destination.id,
        FicheCollecte.entreprise_id.in_(company_ids)).limit(1))).first() if company_ids else None
    if conflict:
        raise HTTPException(409, 'La destination contient déjà un dossier de cette entreprise. Aucun déplacement effectué.')
    responsible_ids = {f.responsable_id for f in moved}
    today = date.today()
    assignments = (await db.execute(select(AffectationMission.utilisateur_id).where(
        AffectationMission.mission_id == destination.id,
        func.upper(AffectationMission.statut) == 'ACTIF',
        or_(AffectationMission.date_debut.is_(None), AffectationMission.date_debut <= today),
        or_(AffectationMission.date_fin.is_(None), AffectationMission.date_fin >= today)
    ))).scalars().all()
    if responsible_ids - set(assignments):
        raise HTTPException(409, 'Affectez d’abord tous les responsables des dossiers à la mission destination. Aucun déplacement effectué.')
    for fiche in moved:
        fiche.mission_id = destination.id
    await write_audit_event(db, action='COLLECTE_DOSSIERS_DEPLACER', categorie='COLLECTE',
        resultat='SUCCES', utilisateur_id=actor.user.id, ressource_type='mission_collecte',
        ressource_id=source_id, adresse_ip=request.client.host if request.client else None,
        valeurs_avant={'mission_id': str(source_id), 'campagne_id': str(by_id[source_id].campagne_id)},
        valeurs_apres={'mission_id': str(destination.id), 'campagne_id': str(destination.campagne_id),
                      'fiches': [str(f.id) for f in moved], 'motif': payload.motif})
    await db.commit()
    return {'dossiers_deplaces': len(roots), 'revisions_deplacees': len(moved)}


async def archive(db, mission_id, motif, actor, request):
    ensure_manager(actor)
    mission = (await db.execute(select(MissionCollecte).where(MissionCollecte.id == mission_id)
                                .with_for_update())).scalar_one_or_none()
    if not mission:
        raise HTTPException(404, 'Mission introuvable.')
    if (await db.execute(select(FicheCollecte.id).where(FicheCollecte.mission_id == mission_id).limit(1))).first():
        raise HTTPException(409, 'Archivage impossible : cette mission contient encore des collectes ou révisions.')
    old = mission.statut
    if old == 'ARCHIVEE':
        return {'statut': 'ARCHIVEE'}
    mission.statut = 'ARCHIVEE'
    await write_audit_event(db, action='COLLECTE_MISSION_ARCHIVER', categorie='COLLECTE',
        resultat='SUCCES', utilisateur_id=actor.user.id, ressource_type='mission_collecte',
        ressource_id=mission_id, adresse_ip=request.client.host if request.client else None,
        valeurs_avant={'statut': old}, valeurs_apres={'statut': 'ARCHIVEE', 'motif': motif})
    await db.commit()
    return {'statut': 'ARCHIVEE'}


async def unarchive(db, mission_id, motif, actor, request):
    ensure_manager(actor)
    mission = (await db.execute(select(MissionCollecte).where(MissionCollecte.id == mission_id)
                                .with_for_update())).scalar_one_or_none()
    if not mission:
        raise HTTPException(404, 'Mission introuvable.')
    if (mission.statut or '').upper() != 'ARCHIVEE':
        raise HTTPException(409, 'Cette mission n’est pas archivée.')
    campaign = await db.get(Campagne, mission.campagne_id)
    if not campaign or (campaign.statut or '').upper() not in {'ACTIVE', 'ACTIF'}:
        raise HTTPException(409, 'Réactivez d’abord la campagne avant de désarchiver sa mission.')
    # L'ancien statut n'était pas stocké séparément ; reprise explicite planifiée.
    mission.statut = 'PLANIFIEE'
    await write_audit_event(db, action='COLLECTE_MISSION_DESARCHIVER', categorie='COLLECTE',
        resultat='SUCCES', utilisateur_id=actor.user.id, ressource_type='mission_collecte',
        ressource_id=mission_id, adresse_ip=request.client.host if request.client else None,
        valeurs_avant={'statut': 'ARCHIVEE'}, valeurs_apres={'statut': 'PLANIFIEE', 'motif': motif})
    await db.commit()
    return {'statut': 'PLANIFIEE'}
