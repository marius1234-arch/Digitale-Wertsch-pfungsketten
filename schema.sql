-- =====================================================================
-- Datenbank-Schema für Newsvendor-Pipeline (Roh-Daten only)
-- Gruppe 6 — Stochastische Bestandsoptimierung im E-Commerce
--
-- Designprinzip:
--   Die Datenbank enthält ausschließlich ROH-DATEN (Produkt-Stammdaten,
--   historische Verkäufe, Kostenparameter). Alle Berechnungen, also die
--   Nachfrageschätzung per relativer Häufigkeit (SAA) und das Newsvendor-
--   Quantil, passieren in Python und werden NICHT zurück in die DB
--   geschrieben. Dadurch ist die DB austauschbar:
--   man kann mehrere DBs (z. B. pro Produktkategorie oder pro Lager)
--   gegen dieselbe Python-Pipeline laufen lassen.
--
-- Verwendung:
--   1. SQLite Browser öffnen → "Neue Datenbank" → Datei "HistorischeVerkaufsdatenAmazon.db" anlegen
--   2. Tab "SQL ausführen" → Inhalt dieser Datei einfügen → Play-Button
--   3. Schreibvorgänge committen (Diskette-Symbol)
-- =====================================================================

-- Sauber starten (Reihenfolge wegen Foreign Keys wichtig)
DROP TABLE IF EXISTS cost_parameters;
DROP TABLE IF EXISTS sales_history;
DROP TABLE IF EXISTS products;

-- Foreign-Key-Checks aktivieren (in SQLite standardmäßig aus)
PRAGMA foreign_keys = ON;


-- =====================================================================
-- 1) products — Stammdaten der saisonalen Produkte
-- =====================================================================
CREATE TABLE products (
    product_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,
    category        TEXT    NOT NULL,
    season_type     TEXT    NOT NULL CHECK (season_type IN ('summer','winter','spring_summer','all_year')),
    description     TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);


-- =====================================================================
-- 2) sales_history — historische Verkaufsdaten (fiktiv generiert)
--    Granularität: ein Datensatz pro (Produkt, Jahr, Monat)
--    Datenbasis: 5 Jahre × 12 Monate = 60 Datenpunkte je Produkt, also
--    5 Beobachtungen je Kalendermonat für die relative Häufigkeit (SAA).
-- =====================================================================
CREATE TABLE sales_history (
    sale_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL,
    year            INTEGER NOT NULL,
    month           INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    sales_quantity  INTEGER NOT NULL CHECK (sales_quantity >= 0),
    UNIQUE (product_id, year, month),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_sales_product_year_month
    ON sales_history (product_id, year, month);


-- =====================================================================
-- 3) cost_parameters — Newsvendor-Inputs Cu und Co je Produkt
--
--    Cu = Cost of Underage (entgangene Marge je nicht verkaufter Einheit)
--       = selling_price_eur − purchase_cost_eur
--
--    Co = Cost of Overage (Verlust je übrig gebliebener Einheit)
--       = (1 − Restwertquote) × purchase_cost_eur + storage_cost_eur
--
--    Annahme: Restwertquote = 60 %. Übrig gebliebene Saisonware kann in
--    der Folgesaison nur noch zum Discount (60 % vom Einkauf) abgesetzt
--    werden — der Verlust pro Überschusseinheit beträgt also 40 % vom
--    Einkaufspreis plus eine Periode FBA-Lagergebühr.
--
--    Die fertigen Cu- und Co-Werte werden gespeichert (nicht zur Laufzeit
--    berechnet), damit später Amazon-spezifische Effekte (Buy-Box-Verlust
--    im Cu, Long-Term-Storage-Fees im Co) ohne Schemaänderung ergänzt
--    werden können.
-- =====================================================================
CREATE TABLE cost_parameters (
    product_id              INTEGER PRIMARY KEY,
    purchase_cost_eur       REAL NOT NULL CHECK (purchase_cost_eur >= 0),
    selling_price_eur       REAL NOT NULL CHECK (selling_price_eur >= 0),
    storage_cost_eur        REAL NOT NULL CHECK (storage_cost_eur >= 0),  -- FBA-Lagergebühr / Einheit / Periode
    cost_underage_eur       REAL NOT NULL,   -- Cu = selling_price − purchase_cost
    cost_overage_eur        REAL NOT NULL,   -- Co = 0.4 × purchase_cost + storage_cost
    FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE CASCADE
);


-- =====================================================================
-- PROJEKTDATEN: 3 fiktive saisonale Produkte mit unterschiedlichem Profil.
-- Diese Werte sind identisch zum eingebauten Fallback (lade_baked_daten) in
-- app.py. Für eine andere Produktwelt einfach eine zweite DB mit gleichem
-- Schema anlegen, die die Pipeline parallel verarbeiten kann.
-- =====================================================================

INSERT INTO products (name, category, season_type, description) VALUES
  ('Pool-Zubehör',    'Garten',  'summer',        'Reinigungsset für Pools, Peak Mai–August'),
  ('Heizdecke',       'Wohnen',  'winter',        'Elektrische Heizdecke, Peak November–Februar'),
  ('Gartenleuchten',  'Garten',  'spring_summer', 'Solar-Gartenleuchten, Peak März–September');

-- Kostenparameter (frei gewählte plausible Werte, später anpassen)
-- Cu = selling_price − purchase_cost
-- Co = 0.4 × purchase_cost + storage_cost   (60 % Restwertannahme)
INSERT INTO cost_parameters
    (product_id, purchase_cost_eur, selling_price_eur, storage_cost_eur, cost_underage_eur, cost_overage_eur)
VALUES
  (1, 12.00, 29.99, 1.20, 17.99, 6.00),   -- Pool-Zubehör:    Cu=17.99, Co=4.80+1.20=6.00
  (2, 18.00, 49.90, 2.50, 31.90, 9.70),   -- Heizdecke:       Cu=31.90, Co=7.20+2.50=9.70
  (3,  9.00, 22.50, 0.80, 13.50, 4.40);   -- Gartenleuchten:  Cu=13.50, Co=3.60+0.80=4.40

-- Historische Verkäufe — 5 Jahre (2021–2025) × 12 Monate je Produkt
-- Wachstum ~6-7% p.a.; 2021/2022 rückwärts extrapoliert

-- Pool-Zubehör (Sommer-Peak)
INSERT INTO sales_history (product_id, year, month, sales_quantity) VALUES
  (1,2021, 1, 26),(1,2021, 2, 31),(1,2021, 3, 52),(1,2021, 4,121),
  (1,2021, 5,278),(1,2021, 6,417),(1,2021, 7,452),(1,2021, 8,348),
  (1,2021, 9,157),(1,2021,10, 70),(1,2021,11, 34),(1,2021,12, 26),
  (1,2022, 1, 28),(1,2022, 2, 33),(1,2022, 3, 56),(1,2022, 4,130),
  (1,2022, 5,298),(1,2022, 6,447),(1,2022, 7,485),(1,2022, 8,373),
  (1,2022, 9,168),(1,2022,10, 75),(1,2022,11, 37),(1,2022,12, 28),
  (1,2023, 1, 30),(1,2023, 2, 35),(1,2023, 3, 60),(1,2023, 4,140),
  (1,2023, 5,320),(1,2023, 6,480),(1,2023, 7,520),(1,2023, 8,400),
  (1,2023, 9,180),(1,2023,10, 80),(1,2023,11, 40),(1,2023,12, 30),
  (1,2024, 1, 35),(1,2024, 2, 38),(1,2024, 3, 70),(1,2024, 4,150),
  (1,2024, 5,340),(1,2024, 6,510),(1,2024, 7,560),(1,2024, 8,420),
  (1,2024, 9,190),(1,2024,10, 85),(1,2024,11, 42),(1,2024,12, 32),
  (1,2025, 1, 38),(1,2025, 2, 40),(1,2025, 3, 75),(1,2025, 4,160),
  (1,2025, 5,360),(1,2025, 6,540),(1,2025, 7,590),(1,2025, 8,440),
  (1,2025, 9,200),(1,2025,10, 90),(1,2025,11, 45),(1,2025,12, 35);

-- Heizdecke (Winter-Peak)
INSERT INTO sales_history (product_id, year, month, sales_quantity) VALUES
  (2,2021, 1,370),(2,2021, 2,317),(2,2021, 3,159),(2,2021, 4, 80),
  (2,2021, 5, 44),(2,2021, 6, 31),(2,2021, 7, 26),(2,2021, 8, 31),
  (2,2021, 9, 70),(2,2021,10,177),(2,2021,11,353),(2,2021,12,458),
  (2,2022, 1,394),(2,2022, 2,338),(2,2022, 3,169),(2,2022, 4, 85),
  (2,2022, 5, 47),(2,2022, 6, 33),(2,2022, 7, 28),(2,2022, 8, 33),
  (2,2022, 9, 75),(2,2022,10,188),(2,2022,11,376),(2,2022,12,488),
  (2,2023, 1,420),(2,2023, 2,360),(2,2023, 3,180),(2,2023, 4, 90),
  (2,2023, 5, 50),(2,2023, 6, 35),(2,2023, 7, 30),(2,2023, 8, 35),
  (2,2023, 9, 80),(2,2023,10,200),(2,2023,11,400),(2,2023,12,520),
  (2,2024, 1,440),(2,2024, 2,380),(2,2024, 3,190),(2,2024, 4, 95),
  (2,2024, 5, 55),(2,2024, 6, 38),(2,2024, 7, 32),(2,2024, 8, 38),
  (2,2024, 9, 85),(2,2024,10,210),(2,2024,11,420),(2,2024,12,560),
  (2,2025, 1,470),(2,2025, 2,400),(2,2025, 3,200),(2,2025, 4,100),
  (2,2025, 5, 60),(2,2025, 6, 40),(2,2025, 7, 35),(2,2025, 8, 40),
  (2,2025, 9, 90),(2,2025,10,220),(2,2025,11,450),(2,2025,12,600);

-- Gartenleuchten (Frühjahr-Sommer-Peak)
INSERT INTO sales_history (product_id, year, month, sales_quantity) VALUES
  (3,2021, 1, 44),(3,2021, 2, 54),(3,2021, 3,160),(3,2021, 4,231),
  (3,2021, 5,285),(3,2021, 6,275),(3,2021, 7,249),(3,2021, 8,213),
  (3,2021, 9,178),(3,2021,10,107),(3,2021,11, 62),(3,2021,12, 49),
  (3,2022, 1, 47),(3,2022, 2, 57),(3,2022, 3,170),(3,2022, 4,245),
  (3,2022, 5,302),(3,2022, 6,292),(3,2022, 7,264),(3,2022, 8,226),
  (3,2022, 9,189),(3,2022,10,113),(3,2022,11, 66),(3,2022,12, 52),
  (3,2023, 1, 50),(3,2023, 2, 60),(3,2023, 3,180),(3,2023, 4,260),
  (3,2023, 5,320),(3,2023, 6,310),(3,2023, 7,280),(3,2023, 8,240),
  (3,2023, 9,200),(3,2023,10,120),(3,2023,11, 70),(3,2023,12, 55),
  (3,2024, 1, 55),(3,2024, 2, 65),(3,2024, 3,190),(3,2024, 4,275),
  (3,2024, 5,340),(3,2024, 6,330),(3,2024, 7,300),(3,2024, 8,255),
  (3,2024, 9,210),(3,2024,10,125),(3,2024,11, 75),(3,2024,12, 58),
  (3,2025, 1, 60),(3,2025, 2, 70),(3,2025, 3,200),(3,2025, 4,290),
  (3,2025, 5,360),(3,2025, 6,350),(3,2025, 7,320),(3,2025, 8,270),
  (3,2025, 9,220),(3,2025,10,130),(3,2025,11, 78),(3,2025,12, 60);


-- =====================================================================
-- Nützliche Read-Only-Queries für das Python-Programm
-- (in Python via sqlite3 oder pandas.read_sql_query auslesen)
-- =====================================================================

-- A) Alle Produkte mit Kostenparametern für die Pipeline
-- SELECT p.product_id, p.name, p.season_type,
--        c.cost_underage_eur, c.cost_overage_eur
-- FROM products p
-- JOIN cost_parameters c ON c.product_id = p.product_id;

-- B) Komplette Verkaufshistorie eines Produkts als Zeitreihe
-- SELECT year, month, sales_quantity
-- FROM sales_history
-- WHERE product_id = ?
-- ORDER BY year, month;

-- C) Sanity-Check: Anzahl Datenpunkte pro Produkt
-- SELECT product_id, COUNT(*) AS datenpunkte
-- FROM sales_history
-- GROUP BY product_id;

-- =====================================================================
-- ENDE
-- =====================================================================
