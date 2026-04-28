# DB-MYSQL-light — Mini IMDB Schema

Self-contained, seed-only MySQL 8.0 environment (no downloads required).  
Port **3307** — runs alongside the full IMDB instance on 3306.

## Migration story

| Version | Script | What changes |
|---------|--------|--------------|
| **V1** | `migrations/V1__initial_schema.sql` | 5 flat tables, MyISAM engine, 50 iconic movies pre-seeded |
| **V2** | `migrations/V2__normalize_genres.sql` | New `movie_genres` junction table — splits the comma-separated `genres` column into rows |
| **V3** | `migrations/V3__innodb_and_fk.sql` | All tables converted MyISAM → InnoDB, foreign keys added, FULLTEXT index on title |

## Tables (V1 baseline)

### title_basics
| Column | Type | Notes |
|--------|------|-------|
| tconst | VARCHAR(20) PK | IMDB title ID |
| titleType | VARCHAR(50) | `movie` for all seed rows |
| primaryTitle | VARCHAR(500) | English title |
| originalTitle | VARCHAR(500) | Original language title |
| isAdult | TINYINT | 0 for all seed rows |
| startYear | SMALLINT | Release year |
| endYear | SMALLINT | NULL for movies |
| runtimeMinutes | INT | |
| genres | VARCHAR(255) | Comma-separated (normalised in V2) |

### title_ratings
| Column | Type |
|--------|------|
| tconst | VARCHAR(20) PK |
| averageRating | FLOAT |
| numVotes | INT |

### name_basics
| Column | Type |
|--------|------|
| nconst | VARCHAR(20) PK |
| primaryName | VARCHAR(255) |
| birthYear | SMALLINT |
| deathYear | SMALLINT |
| primaryProfession | VARCHAR(255) |
| knownForTitles | VARCHAR(500) |

### title_principals
| Column | Type |
|--------|------|
| tconst | VARCHAR(20) PK |
| ordering_num | INT PK |
| nconst | VARCHAR(20) |
| category | VARCHAR(100) |
| job | VARCHAR(500) |
| characters_txt | VARCHAR(500) |

### title_crew
| Column | Type |
|--------|------|
| tconst | VARCHAR(20) PK |
| directors | TEXT | Comma-separated nconsts |
| writers | TEXT | Comma-separated nconsts |

### movie_genres (added in V2)
| Column | Type |
|--------|------|
| tconst | VARCHAR(20) PK |
| genre | VARCHAR(50) PK |

## Quick start

```bat
build_me.bat       # build Docker image once
run_me.bat         # spin up container + load V1 seed
migrate_v2.bat     # apply genre normalization
migrate_v3.bat     # apply InnoDB conversion + foreign keys
```

Connect: `mysql -h 127.0.0.1 -P 3307 -uroot -p'YourStrong!Passw0rd' imdb`
