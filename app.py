import os
import sqlite3

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
MONATE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
          "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "Programm", "Datenbank", "HistorischeVerkaufsdatenAmazon.db",
)


# ---------------------------------------------------------------------------
# Exakte historische Verkaufsdaten der Projekt-DB (product_id, year, month, qty)
# Fest hinterlegt, damit der Fallback identische Werte wie die lokale DB erzeugt.
# ---------------------------------------------------------------------------
VERKAUFSDATEN = [
    # Pool-Zubehör (product_id 1)
    (1, 2021, 1, 26), (1, 2021, 2, 31), (1, 2021, 3, 52), (1, 2021, 4, 121),
    (1, 2021, 5, 278), (1, 2021, 6, 417), (1, 2021, 7, 452), (1, 2021, 8, 348),
    (1, 2021, 9, 157), (1, 2021, 10, 70), (1, 2021, 11, 34), (1, 2021, 12, 26),
    (1, 2022, 1, 28), (1, 2022, 2, 33), (1, 2022, 3, 56), (1, 2022, 4, 130),
    (1, 2022, 5, 298), (1, 2022, 6, 447), (1, 2022, 7, 485), (1, 2022, 8, 373),
    (1, 2022, 9, 168), (1, 2022, 10, 75), (1, 2022, 11, 37), (1, 2022, 12, 28),
    (1, 2023, 1, 30), (1, 2023, 2, 35), (1, 2023, 3, 60), (1, 2023, 4, 140),
    (1, 2023, 5, 320), (1, 2023, 6, 480), (1, 2023, 7, 520), (1, 2023, 8, 400),
    (1, 2023, 9, 180), (1, 2023, 10, 80), (1, 2023, 11, 40), (1, 2023, 12, 30),
    (1, 2024, 1, 35), (1, 2024, 2, 38), (1, 2024, 3, 70), (1, 2024, 4, 150),
    (1, 2024, 5, 340), (1, 2024, 6, 510), (1, 2024, 7, 560), (1, 2024, 8, 420),
    (1, 2024, 9, 190), (1, 2024, 10, 85), (1, 2024, 11, 42), (1, 2024, 12, 32),
    (1, 2025, 1, 38), (1, 2025, 2, 40), (1, 2025, 3, 75), (1, 2025, 4, 160),
    (1, 2025, 5, 360), (1, 2025, 6, 540), (1, 2025, 7, 590), (1, 2025, 8, 440),
    (1, 2025, 9, 200), (1, 2025, 10, 90), (1, 2025, 11, 45), (1, 2025, 12, 35),
    # Heizdecke (product_id 2)
    (2, 2021, 1, 370), (2, 2021, 2, 317), (2, 2021, 3, 159), (2, 2021, 4, 80),
    (2, 2021, 5, 44), (2, 2021, 6, 31), (2, 2021, 7, 26), (2, 2021, 8, 31),
    (2, 2021, 9, 70), (2, 2021, 10, 177), (2, 2021, 11, 353), (2, 2021, 12, 458),
    (2, 2022, 1, 394), (2, 2022, 2, 338), (2, 2022, 3, 169), (2, 2022, 4, 85),
    (2, 2022, 5, 47), (2, 2022, 6, 33), (2, 2022, 7, 28), (2, 2022, 8, 33),
    (2, 2022, 9, 75), (2, 2022, 10, 188), (2, 2022, 11, 376), (2, 2022, 12, 488),
    (2, 2023, 1, 420), (2, 2023, 2, 360), (2, 2023, 3, 180), (2, 2023, 4, 90),
    (2, 2023, 5, 50), (2, 2023, 6, 35), (2, 2023, 7, 30), (2, 2023, 8, 35),
    (2, 2023, 9, 80), (2, 2023, 10, 200), (2, 2023, 11, 400), (2, 2023, 12, 520),
    (2, 2024, 1, 440), (2, 2024, 2, 380), (2, 2024, 3, 190), (2, 2024, 4, 95),
    (2, 2024, 5, 55), (2, 2024, 6, 38), (2, 2024, 7, 32), (2, 2024, 8, 38),
    (2, 2024, 9, 85), (2, 2024, 10, 210), (2, 2024, 11, 420), (2, 2024, 12, 560),
    (2, 2025, 1, 470), (2, 2025, 2, 400), (2, 2025, 3, 200), (2, 2025, 4, 100),
    (2, 2025, 5, 60), (2, 2025, 6, 40), (2, 2025, 7, 35), (2, 2025, 8, 40),
    (2, 2025, 9, 90), (2, 2025, 10, 220), (2, 2025, 11, 450), (2, 2025, 12, 600),
    # Gartenleuchten (product_id 3)
    (3, 2021, 1, 44), (3, 2021, 2, 54), (3, 2021, 3, 160), (3, 2021, 4, 231),
    (3, 2021, 5, 285), (3, 2021, 6, 275), (3, 2021, 7, 249), (3, 2021, 8, 213),
    (3, 2021, 9, 178), (3, 2021, 10, 107), (3, 2021, 11, 62), (3, 2021, 12, 49),
    (3, 2022, 1, 47), (3, 2022, 2, 57), (3, 2022, 3, 170), (3, 2022, 4, 245),
    (3, 2022, 5, 302), (3, 2022, 6, 292), (3, 2022, 7, 264), (3, 2022, 8, 226),
    (3, 2022, 9, 189), (3, 2022, 10, 113), (3, 2022, 11, 66), (3, 2022, 12, 52),
    (3, 2023, 1, 50), (3, 2023, 2, 60), (3, 2023, 3, 180), (3, 2023, 4, 260),
    (3, 2023, 5, 320), (3, 2023, 6, 310), (3, 2023, 7, 280), (3, 2023, 8, 240),
    (3, 2023, 9, 200), (3, 2023, 10, 120), (3, 2023, 11, 70), (3, 2023, 12, 55),
    (3, 2024, 1, 55), (3, 2024, 2, 65), (3, 2024, 3, 190), (3, 2024, 4, 275),
    (3, 2024, 5, 340), (3, 2024, 6, 330), (3, 2024, 7, 300), (3, 2024, 8, 255),
    (3, 2024, 9, 210), (3, 2024, 10, 125), (3, 2024, 11, 75), (3, 2024, 12, 58),
    (3, 2025, 1, 60), (3, 2025, 2, 70), (3, 2025, 3, 200), (3, 2025, 4, 290),
    (3, 2025, 5, 360), (3, 2025, 6, 350), (3, 2025, 7, 320), (3, 2025, 8, 270),
    (3, 2025, 9, 220), (3, 2025, 10, 130), (3, 2025, 11, 78), (3, 2025, 12, 60),
]

# Produkt-Stammdaten + Kostenparameter (product_id, name, season_type, cu, co)
PRODUKTE_BAKED = [
    (1, "Pool-Zubehör",   "summer",        17.99, 6.00),
    (2, "Heizdecke",      "winter",        31.90, 9.70),
    (3, "Gartenleuchten", "spring_summer", 13.50, 4.40),
]


# ---------------------------------------------------------------------------
# Datenzugriff
# ---------------------------------------------------------------------------
@st.cache_data
def lade_daten(db_pfad: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    con = sqlite3.connect(db_pfad)
    produkte = pd.read_sql_query(
        """
        SELECT p.product_id, p.name, p.season_type,
               c.cost_underage_eur AS cu,
               c.cost_overage_eur  AS co
        FROM products p
        JOIN cost_parameters c ON c.product_id = p.product_id
        ORDER BY p.product_id
        """,
        con,
    )
    verkauf = pd.read_sql_query(
        """
        SELECT product_id, year, month, sales_quantity
        FROM sales_history
        ORDER BY product_id, year, month
        """,
        con,
    )
    con.close()
    return produkte, verkauf


def lade_baked_daten() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Liefert die eingebauten Projektdaten direkt im Speicher (ohne Datei).
    Wird als Fallback genutzt, wenn keine DB-Datei am Pfad liegt — die Werte
    sind identisch zur lokalen Projekt-Datenbank.
    """
    produkte = pd.DataFrame(
        PRODUKTE_BAKED, columns=["product_id", "name", "season_type", "cu", "co"]
    )
    verkauf = (
        pd.DataFrame(
            VERKAUFSDATEN, columns=["product_id", "year", "month", "sales_quantity"]
        )
        .sort_values(["product_id", "year", "month"])
        .reset_index(drop=True)
    )
    return produkte, verkauf


# ---------------------------------------------------------------------------
# Berechnung
# ---------------------------------------------------------------------------
def empirisches_q_star(werte, cr: float) -> int:
    """
    Empirisches Newsvendor-Quantil (Sample Average Approximation).
    Q* ist der kleinste beobachtete Wert, dessen kumulative relative
    Häufigkeit das kritische Fraktil CR erreicht oder überschreitet.
    Das entspricht der ceil(CR * n)-ten Ordnungsstatistik der aufsteigend
    sortierten Beobachtungen und ist die exakte SAA-Newsvendor-Lösung.
    """
    sortiert = np.sort(np.asarray(werte))
    n = len(sortiert)
    k = int(np.ceil(cr * n - 1e-9))
    k = min(max(k, 1), n)
    return int(sortiert[k - 1])


def berechne_ergebnisse(verkauf: pd.DataFrame, produkte: pd.DataFrame) -> pd.DataFrame:
    """
    Relative Häufigkeit: Jeder historische Monatswert bekommt gleiches Gewicht.
    Q* = empirisches Quantil bei CR — kein Normalverteilungs-Fitting.
    μ und σ werden nur zur Anzeige mitberechnet.
    """
    prod_info = produkte.set_index("product_id")[["name", "season_type", "cu", "co"]]

    rows = []
    for (pid, month), grp in verkauf.groupby(["product_id", "month"]):
        vals = grp["sales_quantity"].values
        prod = prod_info.loc[pid]
        cr   = prod["cu"] / (prod["cu"] + prod["co"])
        rows.append({
            "product_id":     pid,
            "month":          month,
            "name":           prod["name"],
            "season_type":    prod["season_type"],
            "cu":             prod["cu"],
            "co":             prod["co"],
            "critical_ratio": cr,
            "mu":      vals.mean(),
            "min_val": int(vals.min()),
            "max_val": int(vals.max()),
            "Q_star":  empirisches_q_star(vals, cr),
        })

    df = pd.DataFrame(rows)
    df["monat_name"] = df["month"].apply(lambda m: MONATE[m - 1])
    return df


# ---------------------------------------------------------------------------
# Hilfsfunktionen UI
# ---------------------------------------------------------------------------
SEASON_LABELS = {
    "summer":        "Sommer",
    "winter":        "Winter",
    "spring_summer": "Frühjahr/Sommer",
    "all_year":      "Ganzjährig",
}


def _reset_cu_co(pid: int, cu_default: float, co_default: float) -> None:
    """Setzt Cu/Co eines Produkts auf die Datenbank-Standardwerte zurück."""
    st.session_state[f"cu_{pid}"] = float(cu_default)
    st.session_state[f"co_{pid}"] = float(co_default)


def zeige_produkt(prod: pd.Series, df: pd.DataFrame,
                  cu_default: float, co_default: float) -> None:
    pid = int(prod["product_id"])
    season = SEASON_LABELS.get(prod["season_type"], prod["season_type"])

    head_l, head_r = st.columns([4, 1])
    with head_l:
        st.subheader(f"{prod['name']}")
        st.caption(f"Saisontyp: {season}")
    with head_r:
        st.button(
            "↺ Standardwerte",
            key=f"reset_{pid}",
            on_click=_reset_cu_co,
            args=(pid, cu_default, co_default),
            help=f"Cu/Co auf die DB-Werte zurücksetzen "
                 f"(Cu = {cu_default:.2f} €, Co = {co_default:.2f} €)",
        )

    # Interaktive Kostenparameter — Änderung aktualisiert Grafik, Tabelle und Heatmap
    i1, i2, i3 = st.columns(3)
    with i1:
        cu = st.number_input(
            "Cu — Unterbevorratung (€)",
            min_value=0.01,
            step=0.50,
            format="%.2f",
            key=f"cu_{pid}",
            help="Entgangener Gewinn pro nicht bedienter Nachfrageeinheit",
        )
    with i2:
        co = st.number_input(
            "Co — Überbevorratung (€)",
            min_value=0.01,
            step=0.50,
            format="%.2f",
            key=f"co_{pid}",
            help="Lager- und Restwertkosten pro überschüssiger Einheit",
        )
    with i3:
        cr = cu / (cu + co)
        st.metric("Kritisches Fraktil", f"{cr:.1%}", help="CR = Cu / (Cu + Co)")

    col_chart, col_table = st.columns([3, 2], gap="large")

    with col_chart:
        _zeige_chart(df)

    with col_table:
        _zeige_tabelle(df)


def _zeige_chart(df: pd.DataFrame) -> None:
    fig = go.Figure()

    # Min/Max-Band aus historischen Beobachtungen
    fig.add_trace(go.Scatter(
        x=df["monat_name"].tolist() + df["monat_name"].tolist()[::-1],
        y=df["max_val"].tolist() + df["min_val"].tolist()[::-1],
        fill="toself",
        fillcolor="rgba(99,110,250,0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Beobachteter Bereich (Min–Max)",
        hoverinfo="skip",
    ))

    # Durchschnittsnachfrage μ
    fig.add_trace(go.Scatter(
        x=df["monat_name"], y=df["mu"].round(1),
        mode="lines+markers",
        name="Ø Nachfrage (Durchschnitt)",
        line=dict(color="#636EFA", width=2, dash="dash"),
        marker=dict(size=5),
    ))

    # Optimale Bestellmenge Q*
    fig.add_trace(go.Scatter(
        x=df["monat_name"], y=df["Q_star"],
        mode="lines+markers",
        name="Opt. Bestellmenge Q*",
        line=dict(color="#EF553B", width=2.5),
        marker=dict(size=6),
    ))

    fig.update_layout(
        xaxis_title="Monat",
        yaxis_title="Menge (Einheiten)",
        legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5),
        height=430,
        margin=dict(l=10, r=10, t=20, b=110),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def _zeige_tabelle(df: pd.DataFrame) -> None:
    tbl = df[["monat_name", "mu", "Q_star"]].copy()
    tbl.columns = ["Monat", "Ø Nachfrage", "Bestellmenge Q*"]
    tbl["Ø Nachfrage"] = tbl["Ø Nachfrage"].round(1)
    st.dataframe(
        tbl,
        use_container_width=True,
        hide_index=True,
        height=458,
        column_config={
            "Ø Nachfrage": st.column_config.NumberColumn(
                "Ø Nachfrage",
                help="Durchschnittlicher Absatz in diesem Monat über alle historischen Jahre",
            ),
            "Bestellmenge Q*": st.column_config.NumberColumn(
                "Bestellmenge Q*",
                help="Optimale Bestellmenge laut Newsvendor-Modell",
            ),
        },
    )


# ---------------------------------------------------------------------------
# App-Layout
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Newsvendor-Analyse | Gruppe 6",
    page_icon="📦",
    layout="wide",
)

st.title("📦 Stochastische Bestandsoptimierung")
st.caption("Gruppe 6 · Digitale Wertschöpfungskette · Newsvendor-Modell mit relativer Häufigkeit")

# Sidebar
with st.sidebar:
    st.header("Einstellungen")
    db_pfad = st.text_input(
        "Datenbankpfad",
        value=DEFAULT_DB,
        help="Pfad zur SQLite-Datenbank. Mehrere Datenbanken möglich.",
    )
    st.caption("Die Berechnung erfolgt ausschließlich in Python — die Datenbank wird nur gelesen.")

# Daten laden. Liegt am Pfad eine DB-Datei, wird sie gelesen. Fehlt sie (z. B. auf
# Streamlit Cloud, wo die Datei nicht am erwarteten Pfad liegt), werden die
# eingebauten Projektdaten direkt im Speicher genutzt — identisch zur lokalen DB
# und ohne dass eine Datei geschrieben wird (so kann keine veraltete Datei stören).
if os.path.exists(db_pfad):
    try:
        produkte, verkauf = lade_daten(db_pfad)
    except Exception as e:
        st.error(f"Fehler beim Laden der Datenbank: {e}")
        st.stop()
elif db_pfad == DEFAULT_DB:
    produkte, verkauf = lade_baked_daten()
    st.info(
        "Keine Datenbankdatei gefunden — es werden die eingebauten Projektdaten "
        "verwendet (identisch zur lokalen Datenbank)."
    )
else:
    st.warning(f"Datenbankdatei nicht gefunden:\n`{db_pfad}`\n\nBitte Pfad in der Sidebar anpassen.")
    st.stop()

# Cu/Co interaktiv: Standardwerte aus der DB einmalig in session_state ablegen
for _, _p in produkte.iterrows():
    _pid = int(_p["product_id"])
    st.session_state.setdefault(f"cu_{_pid}", float(_p["cu"]))
    st.session_state.setdefault(f"co_{_pid}", float(_p["co"]))

# Effektive Produkttabelle mit den (ggf. angepassten) Cu/Co aus session_state.
# Die DB selbst wird nie verändert — Anpassungen leben nur in der Session.
produkte_eff = produkte.copy()
produkte_eff["cu"] = produkte_eff["product_id"].apply(
    lambda pid: float(st.session_state[f"cu_{int(pid)}"]))
produkte_eff["co"] = produkte_eff["product_id"].apply(
    lambda pid: float(st.session_state[f"co_{int(pid)}"]))

# Berechnung (auf Basis der effektiven Kostenparameter)
ergebnisse = berechne_ergebnisse(verkauf, produkte_eff)

tab_ergebnisse, tab_heatmap, tab_berechnung = st.tabs(
    ["Ergebnisse", "Übersicht (Heatmap)", "Berechnungsweg Nachfrageprognose"]
)

# ---------------------------------------------------------------------------
# Tab 1: Ergebnisse
# ---------------------------------------------------------------------------
with tab_ergebnisse:
    st.info(
        "Tipp: Passe **Cu** und **Co** je Produkt an — Grafik, Tabelle und "
        "Heatmap aktualisieren sich sofort.",
        icon="🎛️",
    )
    for _, prod in produkte_eff.iterrows():
        pid = prod["product_id"]
        df_prod = (
            ergebnisse[ergebnisse["product_id"] == pid]
            .sort_values("month")
            .reset_index(drop=True)
        )
        db_row = produkte[produkte["product_id"] == pid].iloc[0]
        zeige_produkt(prod, df_prod, float(db_row["cu"]), float(db_row["co"]))
        st.divider()

# ---------------------------------------------------------------------------
# Tab 2: Übersicht (Heatmap)
# ---------------------------------------------------------------------------
with tab_heatmap:
    st.markdown(
        """
        ### Übersicht aller optimalen Bestellmengen

        Die Heatmap zeigt alle **36 Q\\*-Werte** (3 Produkte × 12 Monate) auf einen Blick.
        Dunklere Felder entsprechen niedrigeren, hellere Felder höheren Bestellmengen.
        """
    )

    pivot = (
        ergebnisse
        .pivot(index="product_id", columns="month", values="Q_star")
        .reindex(index=produkte["product_id"].tolist(), columns=list(range(1, 13)))
    )
    z_werte     = pivot.values
    x_labels    = MONATE
    y_labels    = produkte["name"].tolist()

    fig_hm = go.Figure(data=go.Heatmap(
        z=z_werte,
        x=x_labels,
        y=y_labels,
        colorscale="Viridis",
        colorbar=dict(title="Q*"),
        texttemplate="%{z}",
        textfont=dict(size=13),
        hovertemplate="Produkt: %{y}<br>Monat: %{x}<br>Q* = %{z}<extra></extra>",
    ))
    fig_hm.update_layout(
        xaxis_title="Monat",
        yaxis_title="Produkt",
        yaxis=dict(autorange="reversed"),
        height=380,
        margin=dict(l=10, r=10, t=20, b=40),
    )
    st.plotly_chart(fig_hm, use_container_width=True)

    st.caption(
        "Saisonmuster gut erkennbar: Pool-Zubehör mit Peak im Sommer (Mai–Aug), "
        "Heizdecke mit Peak im Winter (Nov–Feb), Gartenleuchten über Frühjahr "
        "bis Frühherbst (Mär–Sep)."
    )


# ---------------------------------------------------------------------------
# Tab 3: Berechnungsweg Nachfrageprognose
# ---------------------------------------------------------------------------
with tab_berechnung:
    st.markdown(
        """
        ### Wie wird die Nachfrageprognose berechnet?

        **Methode: Relative Häufigkeit**

        Jeder historische Jahreswert bekommt das gleiche Gewicht (1 / Anzahl Jahre).
        Die Werte werden aufsteigend sortiert und die kumulative Häufigkeit aufgebaut.
        Q\\* ist der kleinste beobachtete Wert, bei dem die kumulative Häufigkeit das
        **kritische Fraktil** (CR = Cu / (Cu + Co)) erreicht oder überschreitet.
        """
    )
    st.divider()

    sel_col1, sel_col2 = st.columns(2)
    with sel_col1:
        produkt_name = st.selectbox(
            "Produkt",
            options=produkte_eff["name"].tolist(),
        )
    with sel_col2:
        monat_idx = st.selectbox(
            "Monat",
            options=list(range(1, 13)),
            format_func=lambda m: MONATE[m - 1],
        )

    # Produktzeile und Verkaufsdaten für Auswahl
    prod_row  = produkte_eff[produkte_eff["name"] == produkt_name].iloc[0]
    cr        = prod_row["cu"] / (prod_row["cu"] + prod_row["co"])
    hist_vals = (
        verkauf[
            (verkauf["product_id"] == prod_row["product_id"]) &
            (verkauf["month"] == monat_idx)
        ]
        .sort_values("sales_quantity")
        [["year", "sales_quantity"]]
        .reset_index(drop=True)
    )

    n = len(hist_vals)
    hist_vals["Rel. Häufigkeit"]  = 1 / n
    hist_vals["Kum. Häufigkeit"]  = hist_vals["Rel. Häufigkeit"].cumsum()
    q_star = empirisches_q_star(hist_vals["sales_quantity"].values, cr)
    hist_vals["→ Q*?"] = hist_vals["sales_quantity"].apply(
        lambda v: "✓ Q* hier" if v == q_star else ""
    )

    st.markdown(
        f"**{produkt_name} — {MONATE[monat_idx - 1]}** · "
        f"Cu = {prod_row['cu']:.2f} € · Co = {prod_row['co']:.2f} € · "
        f"**CR = {cr:.1%}** · **Q\\* = {q_star}**"
    )

    tbl_display = hist_vals.copy()
    tbl_display.columns = ["Jahr", "Verkäufe", "Rel. Häufigkeit", "Kum. Häufigkeit", "→ Q*?"]
    tbl_display["Rel. Häufigkeit"] = tbl_display["Rel. Häufigkeit"].apply(lambda x: f"{x:.1%}")
    tbl_display["Kum. Häufigkeit"] = tbl_display["Kum. Häufigkeit"].apply(lambda x: f"{x:.1%}")

    st.dataframe(tbl_display, use_container_width=False, hide_index=True)

    # Balkendiagramm mit CR-Linie
    fig2 = go.Figure()
    farben = ["#EF553B" if v == q_star else "#636EFA" for v in hist_vals["sales_quantity"]]
    fig2.add_trace(go.Bar(
        x=hist_vals["sales_quantity"].astype(str) + " (" + hist_vals["year"].astype(str) + ")",
        y=hist_vals["Kum. Häufigkeit"].round(3),
        marker_color=farben,
        name="Kum. Häufigkeit",
        text=[f"{v:.1%}" for v in hist_vals["Kum. Häufigkeit"]],
        textposition="outside",
    ))
    fig2.add_hline(
        y=cr,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"CR = {cr:.1%}",
        annotation_position="top right",
    )
    fig2.update_layout(
        xaxis_title="Verkäufe (Jahr)",
        yaxis_title="Kumulative Häufigkeit",
        yaxis=dict(tickformat=".0%", range=[0, 1.15]),
        height=350,
        margin=dict(l=10, r=10, t=30, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=False)
    st.caption(f"Rot markiert: Q* = {q_star} — erster Wert, bei dem die kumulative Häufigkeit ≥ CR ({cr:.1%})")
