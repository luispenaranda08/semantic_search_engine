-- Consultas de solo lectura sobre la base operativa de competencias (PostgreSQL, esquema public).
-- Solo textos de catálogo y conteos agregados: ninguna columna de personas, correos ni usuarios.
-- Exportar cada resultado desde pgAdmin a data/competencias_suid/esquema_pg/<nombre>.csv
-- y luego correr: python3 pg/auditar_csv_pg.py

-- 1. roles_permisos.csv — conocimiento funcional (qué rol puede hacer qué)
SELECT 'rol' AS tipo, code, name AS nombre, description AS descripcion FROM roles WHERE is_active
UNION ALL
SELECT 'permiso', code, name, description FROM permissions WHERE is_active
UNION ALL
SELECT 'rol_evento', code, name, description FROM event_roles
UNION ALL
SELECT 'permiso_evento', code, resource || ':' || action, description FROM event_permissions
ORDER BY tipo, code;

-- 2. fases_eventos.csv — descripción de eventos y fases
SELECT 'evento' AS tipo, e.code::text AS code, e.name AS nombre, e.description AS descripcion,
       e.event_type, e.scope, e.status, e.phases_count, e.olympic_cycle_year,
       e.has_preregistration, e.requires_enrollment_documentation, e.categories::text AS categorias,
       NULL AS promotion_mode, NULL AS ranking_type, NULL AS quota_modality
FROM events e
UNION ALL
SELECT 'fase', p.code::text, p.name, p.description,
       NULL, NULL, p.status, p.sequence_number, NULL,
       p.has_medals, p.has_accreditation_process, NULL,
       p.promotion_mode, p.ranking_type, p.quota_modality
FROM phases p;

-- 3. pruebas_distintas.csv — combinaciones de prueba (corpus a escala)
SELECT sport_type_name, sport_name, discipline_name, sex_name, category_name,
       COUNT(*)                          AS n_configs,
       COUNT(DISTINCT event_code)        AS n_eventos,
       COUNT(DISTINCT phase_code)        AS n_fases,
       COUNT(DISTINCT organization_code) AS n_organizaciones
FROM result_configs
WHERE deleted_at IS NULL
GROUP BY 1,2,3,4,5
ORDER BY n_configs DESC;

-- 4. reglas_por_deporte.csv — cupos de participación agregados por deporte
WITH deportes AS (
  SELECT DISTINCT sport_code, sport_name FROM lite_event_disciplines
)
SELECT d.sport_name, r.sport_code,
       COUNT(*) AS n_reglas,
       MIN(r.max_groups) AS min_grupos, MAX(r.max_groups) AS max_grupos,
       percentile_disc(0.5) WITHIN GROUP (ORDER BY r.min_athletes_per_group) AS med_min_por_grupo,
       percentile_disc(0.5) WITHIN GROUP (ORDER BY r.max_athletes_per_group) AS med_max_por_grupo,
       percentile_disc(0.5) WITHIN GROUP (ORDER BY r.max_individual_athletes) AS med_max_individuales,
       percentile_disc(0.5) WITHIN GROUP (ORDER BY r.max_support_personnel) AS med_max_apoyo
FROM participation_rules r
LEFT JOIN deportes d USING (sport_code)
GROUP BY 1,2
ORDER BY n_reglas DESC;
