-- HAUQE Certif — Correction consolidée 2.0
-- Situation déclarée d'une certification collectée sur le terrain.
ALTER TABLE certifications_declarees
    ADD COLUMN IF NOT EXISTS situation_declaree VARCHAR(255);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_certifications_declarees_situation'
    ) THEN
        ALTER TABLE certifications_declarees
        ADD CONSTRAINT ck_certifications_declarees_situation
        CHECK (
            situation_declaree IS NULL OR situation_declaree IN (
                'PRESENTE','ABSENTE','AUDIT_SURVEILLANCE_1',
                'AUDIT_SURVEILLANCE_2','AUDIT_SURVEILLANCE_3','RENOUVELLEMENT'
            )
        );
    END IF;
END $$;
