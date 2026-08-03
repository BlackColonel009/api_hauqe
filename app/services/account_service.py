"""
Service métier — profil, préférences, sessions et verrouillage de reprise.

RÈGLES IMPORTANTES
------------------
- l'utilisateur peut modifier ses coordonnées personnelles limitées ;
- l'email professionnel, la fonction, les rôles et permissions ne sont pas
  modifiables depuis `/me/profile` ;
- les sessions listées appartiennent toujours au compte courant ;
- une session étrangère ne peut pas être révoquée ;
- le code privé est vérifié côté FastAPI ;
- après 5 codes privés erronés, la session courante est révoquée ;
- le verrouillage de reprise est distinct du blocage de compte login.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.repositories.account_repository import AccountRepository
from app.schemas.account import (
    MyProfileResponse,
    MyProfileUpdateRequest,
    MySessionResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdateRequest,
    SecurityLockStateResponse,
    SecurityLockUpdateRequest,
    SessionRevokeResponse,
    SessionsRevokeOthersResponse,
    UnlockSessionRequest,
    UnlockSessionResponse,
)
from app.services.auth_service import AuthContext
from app.utils.account_security import hash_secret, token_hash, verify_secret


_password_hasher = PasswordHasher()


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def current_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization", "").strip()
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session Bearer absente.",
        )
    raw = authorization[7:].strip()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session Bearer absente.",
        )
    return raw


class AccountService:

    # ========================================================
    # PROFIL
    # ========================================================

    @staticmethod
    async def profile(
        db: AsyncSession,
        actor: AuthContext,
    ) -> MyProfileResponse:
        user = await AccountRepository.get_user(db, actor.user.id)
        if user is None:
            raise HTTPException(404, "Utilisateur introuvable.")

        prefs = await AccountRepository.get_or_create_preferences(
            db,
            user.id,
        )
        roles, permissions = await AccountRepository.roles_and_permissions(
            db,
            user.id,
        )
        region_name = await AccountRepository.get_region_name(
            db,
            user.region_affectation_id,
        )

        return MyProfileResponse(
            id=user.id,
            email=user.email,
            prenoms=user.prenoms,
            nom=user.nom,
            telephone=user.telephone,
            fonction=user.fonction,
            region_affectation_id=user.region_affectation_id,
            region_affectation_nom=region_name,
            statut=user.statut,
            mfa_active=bool(user.mfa_active),
            derniere_connexion_at=user.derniere_connexion_at,
            created_at=user.created_at,
            langue=prefs.langue,
            fuseau_horaire=prefs.fuseau_horaire,
            avatar_document_id=prefs.avatar_document_id,
            roles=roles,
            permissions=permissions,
        )

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        *,
        payload: MyProfileUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> MyProfileResponse:
        user = await AccountRepository.get_user(db, actor.user.id)
        if user is None:
            raise HTTPException(404, "Utilisateur introuvable.")

        prefs = await AccountRepository.get_or_create_preferences(
            db,
            user.id,
        )

        changes = payload.model_dump(exclude_unset=True)

        # Champs d'identité personnelle que l'utilisateur peut corriger.
        for field in ("prenoms", "nom", "telephone"):
            if field in changes:
                value = changes[field]
                setattr(
                    user,
                    field,
                    value.strip() if isinstance(value, str) and value.strip() else None,
                )

        if "langue" in changes and changes["langue"] is not None:
            prefs.langue = changes["langue"]

        if "fuseau_horaire" in changes and changes["fuseau_horaire"]:
            prefs.fuseau_horaire = changes["fuseau_horaire"].strip()

        if "avatar_document_id" in changes:
            avatar_id = changes["avatar_document_id"]
            if avatar_id is not None:
                document = await AccountRepository.active_avatar_document(
                    db,
                    avatar_id,
                )
                if document is None:
                    raise HTTPException(
                        404,
                        "Document d'avatar introuvable ou inactif.",
                    )
                if (document.format or "").strip().upper() not in {
                    "PNG",
                    "JPG",
                    "JPEG",
                }:
                    raise HTTPException(
                        422,
                        "L'avatar doit être une image PNG ou JPEG.",
                    )
            prefs.avatar_document_id = avatar_id

        await write_audit_event(
            db,
            action="ACCOUNT_PROFILE_UPDATE",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=user.id,
            ressource_type="utilisateur",
            ressource_id=user.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "prenoms": user.prenoms,
                "nom": user.nom,
                "telephone": user.telephone,
                "langue": prefs.langue,
                "fuseau_horaire": prefs.fuseau_horaire,
                "avatar_document_id": (
                    str(prefs.avatar_document_id)
                    if prefs.avatar_document_id else None
                ),
            },
        )

        await db.commit()
        return await AccountService.profile(db, actor)

    # ========================================================
    # PRÉFÉRENCES DE NOTIFICATION
    # ========================================================

    @staticmethod
    async def notification_preferences(
        db: AsyncSession,
        actor: AuthContext,
    ) -> NotificationPreferencesResponse:
        prefs = await AccountRepository.get_or_create_preferences(
            db,
            actor.user.id,
        )
        return NotificationPreferencesResponse(
            alertes_critiques=prefs.notifications_alertes_critiques,
            affectations=prefs.notifications_affectations,
            corrections=prefs.notifications_corrections,
            rapports_planifies=prefs.notifications_rapports_planifies,
            resume_hebdomadaire=prefs.notifications_resume_hebdomadaire,
            actualisation_automatique_active=(
                prefs.actualisation_automatique_active
            ),
            actualisation_intervalle_secondes=(
                prefs.actualisation_intervalle_secondes
            ),
            actualisation_au_retour=prefs.actualisation_au_retour,
        )

    @staticmethod
    async def update_notification_preferences(
        db: AsyncSession,
        *,
        payload: NotificationPreferencesUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> NotificationPreferencesResponse:
        prefs = await AccountRepository.get_or_create_preferences(
            db,
            actor.user.id,
        )

        mapping = {
            "alertes_critiques": "notifications_alertes_critiques",
            "affectations": "notifications_affectations",
            "corrections": "notifications_corrections",
            "rapports_planifies": "notifications_rapports_planifies",
            "resume_hebdomadaire": "notifications_resume_hebdomadaire",
            "actualisation_automatique_active": (
                "actualisation_automatique_active"
            ),
            "actualisation_intervalle_secondes": (
                "actualisation_intervalle_secondes"
            ),
            "actualisation_au_retour": "actualisation_au_retour",
        }

        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(prefs, mapping[key], value)

        await write_audit_event(
            db,
            action="ACCOUNT_NOTIFICATION_PREFERENCES_UPDATE",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="preference_utilisateur",
            ressource_id=prefs.id,
            adresse_ip=client_ip(request),
        )

        await db.commit()
        return await AccountService.notification_preferences(db, actor)

    # ========================================================
    # SESSIONS
    # ========================================================

    @staticmethod
    async def resolve_current_session(
        db: AsyncSession,
        *,
        request: Request,
        actor: AuthContext,
    ):
        raw = current_bearer_token(request)
        session = await AccountRepository.get_session_by_token_hash(
            db,
            token_hash(raw),
        )
        if session is None or session.utilisateur_id != actor.user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session courante introuvable.",
            )
        return session

    @staticmethod
    async def list_sessions(
        db: AsyncSession,
        *,
        request: Request,
        actor: AuthContext,
    ) -> list[MySessionResponse]:
        current = await AccountService.resolve_current_session(
            db,
            request=request,
            actor=actor,
        )
        sessions = await AccountRepository.list_user_sessions(
            db,
            actor.user.id,
        )
        lock_map = await AccountRepository.lock_rows_for_sessions(
            db,
            [s.id for s in sessions],
        )

        items = []
        for session in sessions:
            lock = lock_map.get(session.id)
            locked = bool(
                lock
                and lock.verrouillee_at is not None
                and (
                    lock.deverrouillee_at is None
                    or lock.deverrouillee_at < lock.verrouillee_at
                )
            )
            items.append(
                MySessionResponse(
                    id=session.id,
                    current=session.id == current.id,
                    adresse_ip=session.adresse_ip,
                    user_agent=session.user_agent,
                    debut_at=session.debut_at,
                    derniere_activite_at=session.derniere_activite_at,
                    expiration_at=session.expiration_at,
                    revoquee_at=session.revoquee_at,
                    locked=locked,
                    locked_at=lock.verrouillee_at if locked else None,
                )
            )
        return items

    @staticmethod
    async def revoke_session(
        db: AsyncSession,
        *,
        session_id: UUID,
        actor: AuthContext,
        request: Request,
    ) -> SessionRevokeResponse:
        session = await AccountRepository.get_session(db, session_id)
        if session is None or session.utilisateur_id != actor.user.id:
            raise HTTPException(404, "Session introuvable.")

        if session.revoquee_at is None:
            session.revoquee_at = datetime.now(timezone.utc)
            await write_audit_event(
                db,
                action="ACCOUNT_SESSION_REVOKE",
                categorie="SECURITE",
                resultat="SUCCES",
                utilisateur_id=actor.user.id,
                ressource_type="session_utilisateur",
                ressource_id=session.id,
                adresse_ip=client_ip(request),
            )
            await db.commit()

        return SessionRevokeResponse(
            session_id=session.id,
            revoked=True,
        )

    @staticmethod
    async def revoke_other_sessions(
        db: AsyncSession,
        *,
        actor: AuthContext,
        request: Request,
    ) -> SessionsRevokeOthersResponse:
        current = await AccountService.resolve_current_session(
            db,
            request=request,
            actor=actor,
        )
        sessions = await AccountRepository.active_user_sessions(
            db,
            actor.user.id,
        )
        now = datetime.now(timezone.utc)
        count = 0
        for session in sessions:
            if session.id == current.id:
                continue
            session.revoquee_at = now
            count += 1

        if count:
            await write_audit_event(
                db,
                action="ACCOUNT_SESSION_REVOKE_OTHERS",
                categorie="SECURITE",
                resultat="SUCCES",
                utilisateur_id=actor.user.id,
                ressource_type="session_utilisateur",
                ressource_id=current.id,
                adresse_ip=client_ip(request),
                valeurs_apres={"revoked_count": count},
            )
            await db.commit()

        return SessionsRevokeOthersResponse(revoked_count=count)

    # ========================================================
    # VERROUILLAGE DE REPRISE
    # ========================================================

    @staticmethod
    async def security_lock_state(
        db: AsyncSession,
        *,
        actor: AuthContext,
        request: Request,
    ) -> SecurityLockStateResponse:
        security = await AccountRepository.get_or_create_security(
            db,
            actor.user.id,
        )
        session = await AccountService.resolve_current_session(
            db,
            request=request,
            actor=actor,
        )
        lock = await AccountRepository.get_or_create_session_lock(
            db,
            session.id,
        )

        locked = bool(
            lock.verrouillee_at
            and (
                lock.deverrouillee_at is None
                or lock.deverrouillee_at < lock.verrouillee_at
            )
        )

        return SecurityLockStateResponse(
            enabled=security.verrouillage_auto_active,
            timeout_minutes=security.delai_verrouillage_minutes,
            code_configured=bool(security.code_prive_hash),
            current_session_locked=locked,
            current_session_locked_at=(
                lock.verrouillee_at if locked else None
            ),
            attempts_remaining=max(
                0,
                5 - int(lock.tentatives_code_prive or 0),
            ),
        )

    @staticmethod
    async def update_security_lock(
        db: AsyncSession,
        *,
        payload: SecurityLockUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> SecurityLockStateResponse:
        user = await AccountRepository.get_user(db, actor.user.id)
        if user is None:
            raise HTTPException(404, "Utilisateur introuvable.")

        security = await AccountRepository.get_or_create_security(
            db,
            user.id,
        )

        changing_code = payload.new_code is not None
        enabling_without_code = (
            payload.enabled
            and not security.code_prive_hash
            and not changing_code
        )

        if enabling_without_code:
            raise HTTPException(
                422,
                "Un code privé doit être configuré avant activation.",
            )

        if changing_code:
            if not payload.current_password:
                raise HTTPException(
                    422,
                    "Le mot de passe actuel est requis pour changer le code privé.",
                )
            try:
                _password_hasher.verify(
                    user.mot_de_passe_hash or "",
                    payload.current_password,
                )
            except VerifyMismatchError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Mot de passe actuel incorrect.",
                )

            if payload.new_code != payload.confirm_code:
                raise HTTPException(
                    422,
                    "Les deux codes privés ne correspondent pas.",
                )

            if len(payload.new_code) < 5:
                raise HTTPException(
                    422,
                    "Le code privé doit contenir au moins 5 caractères.",
                )

            security.code_prive_hash = hash_secret(payload.new_code)
            security.code_prive_configure_at = datetime.now(timezone.utc)

        security.verrouillage_auto_active = payload.enabled
        security.delai_verrouillage_minutes = payload.timeout_minutes

        await write_audit_event(
            db,
            action="ACCOUNT_SECURITY_LOCK_SETTINGS_UPDATE",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=user.id,
            ressource_type="securite_compte_utilisateur",
            ressource_id=security.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "enabled": security.verrouillage_auto_active,
                "timeout_minutes": security.delai_verrouillage_minutes,
                "code_configured": bool(security.code_prive_hash),
            },
        )

        await db.commit()
        return await AccountService.security_lock_state(
            db,
            actor=actor,
            request=request,
        )

    @staticmethod
    async def lock_current_session(
        db: AsyncSession,
        *,
        reason: str,
        actor: AuthContext,
        request: Request,
    ) -> SecurityLockStateResponse:
        security = await AccountRepository.get_or_create_security(
            db,
            actor.user.id,
        )
        if not security.verrouillage_auto_active:
            raise HTTPException(
                409,
                "Le verrouillage automatique n'est pas activé.",
            )
        if not security.code_prive_hash:
            raise HTTPException(
                409,
                "Aucun code privé n'est configuré.",
            )

        session = await AccountService.resolve_current_session(
            db,
            request=request,
            actor=actor,
        )
        lock = await AccountRepository.get_or_create_session_lock(
            db,
            session.id,
        )

        lock.verrouillee_at = datetime.now(timezone.utc)
        lock.deverrouillee_at = None
        lock.tentatives_code_prive = 0
        lock.derniere_tentative_at = None
        lock.motif = reason

        await write_audit_event(
            db,
            action="ACCOUNT_SESSION_LOCK",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="session_utilisateur",
            ressource_id=session.id,
            adresse_ip=client_ip(request),
            contexte={"reason": reason},
        )

        await db.commit()
        return await AccountService.security_lock_state(
            db,
            actor=actor,
            request=request,
        )

    @staticmethod
    async def unlock_current_session(
        db: AsyncSession,
        *,
        payload: UnlockSessionRequest,
        actor: AuthContext,
        request: Request,
    ) -> UnlockSessionResponse:
        security = await AccountRepository.get_or_create_security(
            db,
            actor.user.id,
        )
        session = await AccountService.resolve_current_session(
            db,
            request=request,
            actor=actor,
        )
        lock = await AccountRepository.get_or_create_session_lock(
            db,
            session.id,
        )

        locked = bool(
            lock.verrouillee_at
            and (
                lock.deverrouillee_at is None
                or lock.deverrouillee_at < lock.verrouillee_at
            )
        )
        if not locked:
            return UnlockSessionResponse(
                unlocked=True,
                attempts_remaining=5,
                session_revoked=False,
            )

        if verify_secret(security.code_prive_hash, payload.code):
            lock.deverrouillee_at = datetime.now(timezone.utc)
            lock.tentatives_code_prive = 0
            lock.derniere_tentative_at = lock.deverrouillee_at

            await write_audit_event(
                db,
                action="ACCOUNT_SESSION_UNLOCK",
                categorie="SECURITE",
                resultat="SUCCES",
                utilisateur_id=actor.user.id,
                ressource_type="session_utilisateur",
                ressource_id=session.id,
                adresse_ip=client_ip(request),
            )
            await db.commit()

            return UnlockSessionResponse(
                unlocked=True,
                attempts_remaining=5,
                session_revoked=False,
            )

        lock.tentatives_code_prive = int(
            lock.tentatives_code_prive or 0
        ) + 1
        lock.derniere_tentative_at = datetime.now(timezone.utc)

        remaining = max(0, 5 - lock.tentatives_code_prive)

        await write_audit_event(
            db,
            action="ACCOUNT_SESSION_UNLOCK_FAILED",
            categorie="SECURITE",
            resultat="ECHEC",
            utilisateur_id=actor.user.id,
            ressource_type="session_utilisateur",
            ressource_id=session.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "attempts": lock.tentatives_code_prive,
                "remaining": remaining,
            },
        )

        if lock.tentatives_code_prive >= 5:
            session.revoquee_at = datetime.now(timezone.utc)
            await write_audit_event(
                db,
                action="ACCOUNT_SESSION_REVOKED_AFTER_PIN_FAILURES",
                categorie="SECURITE",
                resultat="SUCCES",
                utilisateur_id=actor.user.id,
                ressource_type="session_utilisateur",
                ressource_id=session.id,
                adresse_ip=client_ip(request),
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Nombre maximal de codes privés erronés atteint. "
                    "La session a été révoquée."
                ),
            )

        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Code privé incorrect.",
                "attempts_remaining": remaining,
            },
        )
