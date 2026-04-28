-- Verification queries — run at any migration stage to inspect current state.
-- Usage:
--   mysql -h 127.0.0.1 -P 3307 -uroot -p'YourStrong!Passw0rd' imdb < verify.sql

SELECT '=== ROW COUNTS ===' AS section;
SELECT 'title_basics'     AS tbl, COUNT(*) AS rows FROM title_basics
UNION ALL
SELECT 'title_ratings',   COUNT(*) FROM title_ratings
UNION ALL
SELECT 'name_basics',     COUNT(*) FROM name_basics
UNION ALL
SELECT 'title_principals',COUNT(*) FROM title_principals
UNION ALL
SELECT 'title_crew',      COUNT(*) FROM title_crew;

SELECT '=== STORAGE ENGINES ===' AS section;
SELECT TABLE_NAME, ENGINE, TABLE_ROWS
FROM   information_schema.TABLES
WHERE  TABLE_SCHEMA = 'imdb'
ORDER  BY TABLE_NAME;

SELECT '=== TOP 10 MOVIES BY RATING ===' AS section;
SELECT   b.primaryTitle,
         b.startYear,
         r.averageRating,
         FORMAT(r.numVotes, 0) AS numVotes,
         b.genres
FROM     title_basics   b
JOIN     title_ratings  r ON r.tconst = b.tconst
ORDER BY r.averageRating DESC, r.numVotes DESC
LIMIT    10;

SELECT '=== DIRECTORS WITH MOST FILMS IN DATASET ===' AS section;
SELECT   n.primaryName,
         COUNT(*)          AS films_directed,
         GROUP_CONCAT(b.primaryTitle ORDER BY b.startYear SEPARATOR ' | ') AS titles
FROM     title_principals  tp
JOIN     name_basics        n  ON n.nconst  = tp.nconst
JOIN     title_basics       b  ON b.tconst  = tp.tconst
WHERE    tp.category = 'director'
GROUP BY n.nconst, n.primaryName
HAVING   films_directed > 1
ORDER BY films_directed DESC;

-- ── V2+ checks ──────────────────────────────────────────────
SELECT '=== GENRE DISTRIBUTION (available after V2) ===' AS section;
SELECT   genre,
         COUNT(*) AS movies
FROM     movie_genres
GROUP BY genre
ORDER BY movies DESC;

-- ── V3+ checks ──────────────────────────────────────────────
SELECT '=== FOREIGN KEY CONSTRAINTS (available after V3) ===' AS section;
SELECT   rc.CONSTRAINT_NAME,
         rc.TABLE_NAME,
         rc.REFERENCED_TABLE_NAME,
         kcu.COLUMN_NAME,
         kcu.REFERENCED_COLUMN_NAME
FROM     information_schema.REFERENTIAL_CONSTRAINTS rc
JOIN     information_schema.KEY_COLUMN_USAGE kcu
           ON kcu.CONSTRAINT_NAME   = rc.CONSTRAINT_NAME
          AND kcu.CONSTRAINT_SCHEMA = rc.CONSTRAINT_SCHEMA
WHERE    rc.CONSTRAINT_SCHEMA = 'imdb'
ORDER BY rc.TABLE_NAME;

SELECT '=== FULLTEXT INDEXES (available after V3) ===' AS section;
SELECT   TABLE_NAME, INDEX_NAME, INDEX_TYPE, COLUMN_NAME
FROM     information_schema.STATISTICS
WHERE    TABLE_SCHEMA = 'imdb'
  AND    INDEX_TYPE   = 'FULLTEXT'
ORDER BY TABLE_NAME, INDEX_NAME;
