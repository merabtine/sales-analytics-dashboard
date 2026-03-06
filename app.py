import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Business Intelligence Dashboard", layout="wide", page_icon="")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
}
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] label { color: #94a3b8 !important; font-weight: 600; font-size: 0.82rem; letter-spacing: 0.03em; }
section[data-testid="stSidebar"] h2 { color: #f1f5f9 !important; }
section[data-testid="stSidebar"] .stMarkdown p { color: #cbd5e1 !important; }

[data-testid="metric-container"] {
    border-radius: 14px; padding: 18px 22px;
    border-left: 4px solid #6366f1;
    background: rgba(99,102,241,0.07);
    backdrop-filter: blur(8px);
}
[data-testid="metric-container"] label { font-size: 0.82rem !important; font-weight: 600 !important; letter-spacing: 0.04em; opacity: 0.75; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 1.55rem !important; font-weight: 800 !important; }

.section-header {
    font-size: 1.15rem; font-weight: 700;
    margin: 32px 0 14px 0; padding: 10px 16px;
    border-radius: 8px; border-left: 4px solid #6366f1;
    background: rgba(99,102,241,0.08); color: inherit;
}
.page-title {
    font-size: 2rem; font-weight: 800;
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #06b6d4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    margin-bottom: 2px;
}
.page-subtitle { font-size: 0.95rem; margin-bottom: 24px; opacity: 0.6; }
.tab-header {
    font-size: 1.45rem; font-weight: 800; padding: 8px 0 4px 0;
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.info-box {
    border-radius: 12px; padding: 14px 20px; margin: 12px 0;
    font-size: 0.92rem; font-weight: 500;
    border: 1px solid rgba(99,102,241,0.3); background: rgba(99,102,241,0.09);
}
.upload-box {
    border-radius: 12px; padding: 14px 18px; margin: 8px 0 16px 0;
    border: 1px solid rgba(99,102,241,0.35); background: rgba(99,102,241,0.07);
    font-size: 0.88rem; line-height: 1.6;
}
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-radius: 12px; padding: 6px; background: rgba(99,102,241,0.08); }
.stTabs [data-baseweb="tab"] { border-radius: 8px; font-weight: 600; font-size: 0.9rem; padding: 8px 22px; color: inherit; opacity: 0.65; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; opacity: 1 !important; }
hr { opacity: 0.15; margin: 24px 0; }
</style>
""", unsafe_allow_html=True)

# =============================================
# COLONNES OBLIGATOIRES
# =============================================
COLS_VENTES = ["Num_CMD","Date_CMD","Client","Adresse","Code_Produit",
               "Produit","Categorie_Produit","Qte","Montant_HT","Taxe","Montant_TTC"]
COLS_ACHATS = ["Num_CMD","Date_CMD","Fournisseur","Code_Produit",
               "Produit","Categorie_Produit","Qte","Montant_HT","Taxe","Montant_TTC"]

# =============================================
# PARSING
# =============================================
def parse_ventes(file):
    df = pd.read_csv(file)
    df["Date_CMD"] = pd.to_datetime(df["Date_CMD"])
    df["Annee"] = df["Date_CMD"].dt.year.astype(str)
    df["Mois"] = df["Date_CMD"].dt.month
    df["Wilaya"] = df["Adresse"].str.split(" - ").str[-1].str.strip()
    df["Forme_Juridique"] = df["Client"].str.split().str[0]
    df["Type_Vente"] = df["Num_CMD"].str[:4]
    return df

def parse_achats(file):
    df = pd.read_csv(file)
    df["Date_CMD"] = pd.to_datetime(df["Date_CMD"])
    df["Annee"] = df["Date_CMD"].dt.year.astype(str)
    df["Mois"] = df["Date_CMD"].dt.month
    df["Type_Achat"] = df["Num_CMD"].str[:3]
    return df

# =============================================
# CALCUL PMP CHRONOLOGIQUE
# =============================================
def compute_pmp_chronologique(ventes_raw, achats_raw):
    df_v = ventes_raw.copy()
    df_a = achats_raw.copy()
    df_a["Prix_Unit_Achat"] = df_a["Montant_HT"] / df_a["Qte"]

    tous_produits = df_v["Code_Produit"].unique()
    resultats = []

    for code in sorted(tous_produits):
        ventes_prod = df_v[df_v["Code_Produit"] == code].copy()
        achats_prod = df_a[df_a["Code_Produit"] == code].copy()

        stock_qte    = 0.0
        stock_valeur = 0.0
        pmp_courant  = 0.0

        mouvements_achats = achats_prod[["Date_CMD","Qte","Prix_Unit_Achat"]].copy()
        mouvements_achats = mouvements_achats.rename(columns={"Prix_Unit_Achat": "prix_unit"})
        mouvements_achats["ordre"] = 0

        mouvements_ventes = ventes_prod[["Date_CMD","Num_CMD","Qte","Montant_HT"]].copy()
        mouvements_ventes["prix_unit"] = mouvements_ventes["Montant_HT"] / mouvements_ventes["Qte"]
        mouvements_ventes["ordre"] = 1

        all_dates = pd.concat([
            mouvements_achats[["Date_CMD","ordre","Qte","prix_unit"]].assign(mvt="achat"),
            mouvements_ventes[["Date_CMD","ordre","Qte","prix_unit","Num_CMD","Montant_HT"]].assign(mvt="vente")
        ]).sort_values(["Date_CMD","ordre"]).reset_index(drop=True)

        for _, row in all_dates.iterrows():
            if row["mvt"] == "achat":
                stock_valeur  = stock_valeur + row["Qte"] * row["prix_unit"]
                stock_qte     = stock_qte + row["Qte"]
                pmp_courant   = stock_valeur / stock_qte if stock_qte > 0 else 0
            else:
                qte_vendue      = row["Qte"]
                prix_vente_unit = row["prix_unit"]
                marge_unit      = prix_vente_unit - pmp_courant
                marge_totale    = marge_unit * qte_vendue
                stock_qte       = max(0, stock_qte - qte_vendue)
                stock_valeur    = stock_qte * pmp_courant

                ligne_vente = ventes_prod[ventes_prod["Num_CMD"] == row["Num_CMD"]].iloc[0]
                resultats.append({
                    "Num_CMD":           row["Num_CMD"],
                    "Date_CMD":          row["Date_CMD"],
                    "Client":            ligne_vente["Client"],
                    "Adresse":           ligne_vente["Adresse"],
                    "Code_Produit":      code,
                    "Produit":           ligne_vente["Produit"],
                    "Categorie_Produit": ligne_vente["Categorie_Produit"],
                    "Qte":               qte_vendue,
                    "Montant_HT":        ligne_vente["Montant_HT"],
                    "Taxe":              ligne_vente["Taxe"],
                    "Montant_TTC":       ligne_vente["Montant_TTC"],
                    "Annee":             ligne_vente["Annee"],
                    "Mois":              ligne_vente["Mois"],
                    "Wilaya":            ligne_vente["Wilaya"],
                    "Forme_Juridique":   ligne_vente["Forme_Juridique"],
                    "Type_Vente":        ligne_vente["Type_Vente"],
                    "PMP":               round(pmp_courant, 4),
                    "Prix_Vente_Unit":   round(prix_vente_unit, 4),
                    "Marge_Unit":        round(marge_unit, 4),
                    "Marge_Totale":      round(marge_totale, 4),
                })

    return pd.DataFrame(resultats)

# =============================================
# PALETTES
# =============================================
PALETTE_ANNEES     = {"2024": "#3b82f6", "2025": "#f97316"}
PALETTE_TYPE_VENTE = {"SLSD": "#6366f1", "SLSG": "#10b981", "SLSR": "#f43f5e"}
PALETTE_TYPE_ACHAT = {"POL": "#8b5cf6", "POI": "#f59e0b"}
PALETTE_CAT    = {"Laptop": "#6366f1", "Printer": "#f97316", "Ink": "#10b981", "Scanner": "#f43f5e"}
PALETTE_WILAYA = {"Alger": "#6366f1", "Blida": "#06b6d4", "Oran": "#f97316", "Setif": "#10b981"}
PALETTE_FORME  = {"SARL": "#6366f1", "EURL": "#f97316", "SNC": "#10b981"}
PALETTE_FOURN  = {"SARL IMPORT COMPUTER": "#6366f1", "EURL ABM": "#f97316", "SNC Wiffak": "#10b981"}
SEQ_COLORS     = ["#6366f1","#f97316","#10b981","#f43f5e","#06b6d4","#8b5cf6","#eab308","#ec4899"]
MAP_INDICATEUR = {"CA": "#6366f1", "Cout": "#f43f5e", "Marge": "#10b981"}

def chart(fig, height=480):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", size=13),
        title_font=dict(size=16, family="Inter"),
        legend=dict(bgcolor="rgba(128,128,128,0.12)", bordercolor="rgba(128,128,128,0.2)", borderwidth=1, font=dict(size=12)),
        margin=dict(t=60, b=50, l=50, r=30), height=height,
        xaxis=dict(gridcolor="rgba(128,128,128,0.15)", linecolor="rgba(128,128,128,0.25)", tickfont=dict(size=12)),
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)", linecolor="rgba(128,128,128,0.25)", tickfont=dict(size=12)),
    )
    fig.update_traces(textfont_size=12)
    return fig

# =============================================
# HEADER
# =============================================
st.markdown('<div class="page-title">Business Intelligence Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Analyse des Ventes &nbsp;&bull;&nbsp; Achats &nbsp;&bull;&nbsp; Marges — 2024 / 2025</div>', unsafe_allow_html=True)
st.markdown("---")

# =============================================
# UPLOAD CSV (sidebar — en premier)
# =============================================
with st.sidebar:
    st.markdown("## 📂 Chargement des données")
    st.markdown(
        '<div class="upload-box">'
        'Importez vos deux fichiers CSV<br>pour alimenter le dashboard.<br>'
        '<small>Séparateur : virgule &nbsp;|&nbsp; Encodage : UTF-8</small>'
        '</div>',
        unsafe_allow_html=True
    )
    uploaded_ventes = st.file_uploader("📄 Fichier Ventes (ventes.csv)", type=["csv"], key="upload_v")
    uploaded_achats = st.file_uploader("📄 Fichier Achats (achats.csv)", type=["csv"], key="upload_a")

    with st.expander("ℹ️ Colonnes attendues"):
        st.markdown(f"**ventes.csv**\n\n`{'`, `'.join(COLS_VENTES)}`")
        st.markdown(f"**achats.csv**\n\n`{'`, `'.join(COLS_ACHATS)}`")

# Attente des fichiers
if uploaded_ventes is None or uploaded_achats is None:
    st.info("⬅️  Veuillez charger les fichiers **ventes.csv** et **achats.csv** dans la barre latérale pour afficher le dashboard.")
    st.stop()

# Lecture & validation
try:
    df_ventes = parse_ventes(uploaded_ventes)
except Exception as e:
    st.error(f"❌ Erreur lecture ventes.csv : {e}")
    st.stop()

try:
    df_achats = parse_achats(uploaded_achats)
except Exception as e:
    st.error(f"❌ Erreur lecture achats.csv : {e}")
    st.stop()

cols_v_manq = [c for c in COLS_VENTES if c not in df_ventes.columns]
cols_a_manq = [c for c in COLS_ACHATS if c not in df_achats.columns]
if cols_v_manq:
    st.error(f"❌ Colonnes manquantes dans ventes.csv : {cols_v_manq}")
    st.stop()
if cols_a_manq:
    st.error(f"❌ Colonnes manquantes dans achats.csv : {cols_a_manq}")
    st.stop()

df_marge = compute_pmp_chronologique(df_ventes, df_achats)

with st.sidebar:
    st.success(f"✅ Ventes : {len(df_ventes):,} lignes")
    st.success(f"✅ Achats : {len(df_achats):,} lignes")
    st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Partie 1 — Ventes", "Partie 2 — Achats", "Partie 3 — Marges"])

# ██████████████████████████████████████████████
#  PARTIE 1 — VENTES
# ██████████████████████████████████████████████
with tab1:
    st.markdown('<div class="tab-header">Analyse des Ventes</div>', unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("## Filtres — Ventes")
        f_produit_v = st.multiselect("Produit", sorted(df_ventes["Produit"].unique()), key="vp")
        f_cat_v     = st.multiselect("Categorie", sorted(df_ventes["Categorie_Produit"].unique()), key="vc")
        f_client_v  = st.multiselect("Client", sorted(df_ventes["Client"].unique()), key="vcl")
        f_forme_v   = st.multiselect("Forme Juridique", sorted(df_ventes["Forme_Juridique"].unique()), key="vf")
        f_type_v    = st.multiselect("Type Vente", sorted(df_ventes["Type_Vente"].unique()), key="vt")
        f_wilaya_v  = st.multiselect("Wilaya", sorted(df_ventes["Wilaya"].unique()), key="vw")
        f_mois_v    = st.multiselect("Mois", sorted(df_ventes["Mois"].unique()), key="vm")
        f_annee_v   = st.multiselect("Annee", sorted(df_ventes["Annee"].unique()), key="va")

    dv = df_ventes.copy()
    if f_produit_v: dv = dv[dv["Produit"].isin(f_produit_v)]
    if f_cat_v:     dv = dv[dv["Categorie_Produit"].isin(f_cat_v)]
    if f_client_v:  dv = dv[dv["Client"].isin(f_client_v)]
    if f_forme_v:   dv = dv[dv["Forme_Juridique"].isin(f_forme_v)]
    if f_type_v:    dv = dv[dv["Type_Vente"].isin(f_type_v)]
    if f_wilaya_v:  dv = dv[dv["Wilaya"].isin(f_wilaya_v)]
    if f_mois_v:    dv = dv[dv["Mois"].isin(f_mois_v)]
    if f_annee_v:   dv = dv[dv["Annee"].isin(f_annee_v)]

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("CA HT", f"{dv['Montant_HT'].sum():,.0f} DA")
    with c2: st.metric("Quantites vendues", f"{dv['Qte'].sum():,}")
    with c3: st.metric("Commandes", f"{dv['Num_CMD'].nunique()}")
    with c4: st.metric("Clients", f"{dv['Client'].nunique()}")
    st.markdown("---")

    st.markdown('<div class="section-header">Produits vendus apres le 01 Fevrier 2025</div>', unsafe_allow_html=True)
    df_post = df_ventes[df_ventes["Date_CMD"] > "2025-02-01"][
        ["Code_Produit","Produit","Categorie_Produit","Date_CMD","Client","Wilaya","Type_Vente"]
    ].drop_duplicates()
    df_post["Date_CMD"] = df_post["Date_CMD"].dt.strftime("%Y-%m-%d")
    st.dataframe(df_post.reset_index(drop=True), use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header">Classement Produits par CA — Type Vente et Annee</div>', unsafe_allow_html=True)
    ca_prod = dv.groupby(["Produit","Type_Vente","Annee"])["Montant_HT"].sum().reset_index().sort_values("Montant_HT", ascending=False)

    fig = px.bar(ca_prod, x="Produit", y="Montant_HT", color="Type_Vente", barmode="group",
                 title="CA par Produit et Type de Vente (SLSD / SLSG / SLSR)",
                 color_discrete_map=PALETTE_TYPE_VENTE, text_auto=".2s",
                 category_orders={"Type_Vente": ["SLSD","SLSG","SLSR"]})
    fig.update_layout(xaxis_tickangle=-25, bargap=0.18, bargroupgap=0.08)
    st.plotly_chart(chart(fig, 520), use_container_width=True)

    fig = px.bar(dv.groupby(["Produit","Annee"])["Montant_HT"].sum().reset_index(),
                 x="Produit", y="Montant_HT", color="Annee", barmode="group",
                 title="CA par Produit et Annee",
                 color_discrete_map=PALETTE_ANNEES, text_auto=".2s")
    fig.update_layout(xaxis_tickangle=-25, bargap=0.2, bargroupgap=0.1)
    st.plotly_chart(chart(fig, 500), use_container_width=True)

    fig = px.pie(ca_prod.groupby("Produit")["Montant_HT"].sum().reset_index(),
                 values="Montant_HT", names="Produit", title="Repartition du CA par Produit",
                 color_discrete_sequence=SEQ_COLORS, hole=0.42)
    fig.update_traces(textposition="outside", textinfo="percent+label", textfont_size=13)
    st.plotly_chart(chart(fig, 520), use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header">Classement Clients par CA — Wilaya et Forme Juridique</div>', unsafe_allow_html=True)
    ca_cl = dv.groupby(["Client","Wilaya","Forme_Juridique"])["Montant_HT"].sum().reset_index().sort_values("Montant_HT", ascending=False)

    fig = px.bar(ca_cl, x="Client", y="Montant_HT", color="Wilaya", barmode="group",
                 title="CA par Client et Wilaya", color_discrete_map=PALETTE_WILAYA, text_auto=".2s")
    fig.update_layout(xaxis_tickangle=-25)
    st.plotly_chart(chart(fig, 500), use_container_width=True)

    fig = px.bar(ca_cl, x="Client", y="Montant_HT", color="Forme_Juridique", barmode="group",
                 title="CA par Client et Forme Juridique", color_discrete_map=PALETTE_FORME, text_auto=".2s")
    fig.update_layout(xaxis_tickangle=-25)
    st.plotly_chart(chart(fig, 500), use_container_width=True)

    fig = px.treemap(ca_cl, path=["Forme_Juridique","Wilaya","Client"], values="Montant_HT",
                     title="Hierarchie Clients — Forme Juridique > Wilaya > Client",
                     color="Montant_HT", color_continuous_scale=["#6366f1","#8b5cf6","#a78bfa","#c4b5fd"])
    st.plotly_chart(chart(fig, 540), use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header">Ventes Quantitatives — Produit, Categorie, Type Vente, Mois et Annee</div>', unsafe_allow_html=True)
    fig = px.bar(dv.groupby(["Produit","Categorie_Produit"])["Qte"].sum().reset_index(),
                 x="Produit", y="Qte", color="Categorie_Produit",
                 title="Quantites Vendues par Produit et Categorie",
                 color_discrete_map=PALETTE_CAT, text_auto=True)
    fig.update_layout(xaxis_tickangle=-25)
    st.plotly_chart(chart(fig, 500), use_container_width=True)

    fig = px.bar(dv.groupby(["Type_Vente","Produit"])["Qte"].sum().reset_index(),
                 x="Produit", y="Qte", color="Type_Vente", barmode="group",
                 title="Quantites par Type de Vente (SLSD / SLSG / SLSR)",
                 color_discrete_map=PALETTE_TYPE_VENTE, text_auto=True,
                 category_orders={"Type_Vente": ["SLSD","SLSG","SLSR"]})
    fig.update_layout(xaxis_tickangle=-25, bargap=0.2, bargroupgap=0.1)
    st.plotly_chart(chart(fig, 500), use_container_width=True)

    fig = px.line(dv.groupby(["Mois","Annee"])["Qte"].sum().reset_index(),
                  x="Mois", y="Qte", color="Annee", title="Evolution Quantites par Mois et Annee",
                  color_discrete_map=PALETTE_ANNEES, markers=True, line_shape="spline")
    fig.update_traces(line_width=3, marker_size=9)
    fig.update_layout(xaxis=dict(tickmode="linear", tick0=1, dtick=1))
    st.plotly_chart(chart(fig, 480), use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header">Categorie de Produit la Plus Rentable</div>', unsafe_allow_html=True)
    ca_cat = dv.groupby("Categorie_Produit")["Montant_HT"].sum().reset_index().sort_values("Montant_HT", ascending=False)
    top = ca_cat.iloc[0]
    st.markdown(f'<div class="info-box">Categorie la plus rentable : <strong>{top["Categorie_Produit"]}</strong> — <strong>{top["Montant_HT"]:,.0f} DA</strong></div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        fig = px.bar(ca_cat, x="Categorie_Produit", y="Montant_HT", color="Categorie_Produit",
                     title="CA par Categorie", color_discrete_map=PALETTE_CAT, text_auto=".2s")
        st.plotly_chart(chart(fig, 440), use_container_width=True)
    with c2:
        fig = px.pie(ca_cat, values="Montant_HT", names="Categorie_Produit",
                     title="Repartition CA par Categorie", hole=0.45, color_discrete_map=PALETTE_CAT)
        fig.update_traces(textposition="outside", textinfo="percent+label", textfont_size=13)
        st.plotly_chart(chart(fig, 440), use_container_width=True)


# ██████████████████████████████████████████████
#  PARTIE 2 — ACHATS
# ██████████████████████████████████████████████
with tab2:
    st.markdown('<div class="tab-header">Analyse des Achats</div>', unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("---")
        st.markdown("## Filtres — Achats")
        f_produit_a = st.multiselect("Produit", sorted(df_achats["Produit"].unique()), key="ap")
        f_cat_a     = st.multiselect("Categorie", sorted(df_achats["Categorie_Produit"].unique()), key="ac")
        f_fourn_a   = st.multiselect("Fournisseur", sorted(df_achats["Fournisseur"].unique()), key="af")
        f_type_a    = st.multiselect("Type Achat (POL/POI)", sorted(df_achats["Type_Achat"].unique()), key="at")
        f_mois_a    = st.multiselect("Mois", sorted(df_achats["Mois"].unique()), key="am")
        f_annee_a   = st.multiselect("Annee", sorted(df_achats["Annee"].unique()), key="aa")

    da = df_achats.copy()
    if f_produit_a: da = da[da["Produit"].isin(f_produit_a)]
    if f_cat_a:     da = da[da["Categorie_Produit"].isin(f_cat_a)]
    if f_fourn_a:   da = da[da["Fournisseur"].isin(f_fourn_a)]
    if f_type_a:    da = da[da["Type_Achat"].isin(f_type_a)]
    if f_mois_a:    da = da[da["Mois"].isin(f_mois_a)]
    if f_annee_a:   da = da[da["Annee"].isin(f_annee_a)]

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Cout Achat HT", f"{da['Montant_HT'].sum():,.0f} DA")
    with c2: st.metric("Quantites achetees", f"{da['Qte'].sum():,}")
    with c3: st.metric("Commandes", f"{da['Num_CMD'].nunique()}")
    with c4: st.metric("Fournisseurs", f"{da['Fournisseur'].nunique()}")
    st.markdown("---")

    st.markdown('<div class="section-header">Produits achetes en 2024</div>', unsafe_allow_html=True)
    df_2024 = df_achats[df_achats["Annee"] == "2024"]
    prods_2024 = df_2024.groupby(["Code_Produit","Produit","Categorie_Produit","Fournisseur"]).agg(
        Qte_Total=("Qte","sum"), Montant_Total=("Montant_HT","sum")).reset_index()
    st.dataframe(prods_2024, use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header">Achats Quantitatifs — Produit, Type Achat, Mois et Annee</div>', unsafe_allow_html=True)
    fig = px.bar(da.groupby(["Produit","Type_Achat"])["Qte"].sum().reset_index(),
                 x="Produit", y="Qte", color="Type_Achat", barmode="group",
                 title="Quantites Achetees par Produit et Type (POL / POI)",
                 color_discrete_map=PALETTE_TYPE_ACHAT, text_auto=True)
    fig.update_layout(xaxis_tickangle=-25, bargap=0.2, bargroupgap=0.1)
    st.plotly_chart(chart(fig, 520), use_container_width=True)

    fig = px.bar(da.groupby(["Annee","Produit"])["Qte"].sum().reset_index(),
                 x="Produit", y="Qte", color="Annee", barmode="group",
                 title="Quantites Achetees par Produit et Annee",
                 color_discrete_map=PALETTE_ANNEES, text_auto=True)
    fig.update_layout(xaxis_tickangle=-25, bargap=0.2, bargroupgap=0.1)
    st.plotly_chart(chart(fig, 500), use_container_width=True)

    fig = px.line(da.groupby(["Mois","Annee"])["Qte"].sum().reset_index(),
                  x="Mois", y="Qte", color="Annee", title="Evolution des Achats par Mois et Annee",
                  color_discrete_map=PALETTE_ANNEES, markers=True, line_shape="spline")
    fig.update_traces(line_width=3, marker_size=9)
    fig.update_layout(xaxis=dict(tickmode="linear", tick0=1, dtick=1))
    st.plotly_chart(chart(fig, 460), use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header">Fournisseur Dominant par Categorie</div>', unsafe_allow_html=True)
    fourn_cat = da.groupby(["Fournisseur","Categorie_Produit"])["Montant_HT"].sum().reset_index().sort_values("Montant_HT", ascending=False)
    fig = px.bar(fourn_cat, x="Categorie_Produit", y="Montant_HT", color="Fournisseur", barmode="group",
                 title="Montant Achat par Categorie et Fournisseur",
                 color_discrete_map=PALETTE_FOURN, text_auto=".2s")
    st.plotly_chart(chart(fig, 520), use_container_width=True)

    qte_f = da.groupby(["Fournisseur","Categorie_Produit"])["Qte"].sum().reset_index()
    fig = px.bar(qte_f, x="Categorie_Produit", y="Qte", color="Fournisseur", barmode="group",
                 title="Quantites Achetees par Categorie et Fournisseur",
                 color_discrete_map=PALETTE_FOURN, text_auto=True)
    st.plotly_chart(chart(fig, 500), use_container_width=True)

    fig = px.sunburst(fourn_cat, path=["Categorie_Produit","Fournisseur"], values="Montant_HT",
                      title="Hierarchie Fournisseurs par Categorie",
                      color_discrete_sequence=SEQ_COLORS)
    st.plotly_chart(chart(fig, 540), use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header">Categorie de Produit la Plus Couteuse</div>', unsafe_allow_html=True)
    cout_cat = da.groupby("Categorie_Produit")["Montant_HT"].sum().reset_index().sort_values("Montant_HT", ascending=False)
    top_c = cout_cat.iloc[0]
    st.markdown(f'<div class="info-box">Categorie la plus couteuse : <strong>{top_c["Categorie_Produit"]}</strong> — <strong>{top_c["Montant_HT"]:,.0f} DA</strong></div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        fig = px.bar(cout_cat, x="Categorie_Produit", y="Montant_HT", color="Categorie_Produit",
                     title="Cout Achat par Categorie", color_discrete_map=PALETTE_CAT, text_auto=".2s")
        st.plotly_chart(chart(fig, 440), use_container_width=True)
    with c2:
        fig = px.pie(cout_cat, values="Montant_HT", names="Categorie_Produit",
                     title="Repartition Couts par Categorie", hole=0.45, color_discrete_map=PALETTE_CAT)
        fig.update_traces(textposition="outside", textinfo="percent+label", textfont_size=13)
        st.plotly_chart(chart(fig, 440), use_container_width=True)


# ██████████████████████████████████████████████
#  PARTIE 3 — MARGES  (PMP CHRONOLOGIQUE)
# ██████████████████████████████████████████████
with tab3:
    st.markdown('<div class="tab-header">Analyse des Marges — PMP Chronologique</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("---")
        st.markdown("## Filtres — Marges")
        f_produit_m = st.multiselect("Produit", sorted(df_marge["Produit"].unique()), key="mp")
        f_cat_m     = st.multiselect("Categorie", sorted(df_marge["Categorie_Produit"].unique()), key="mc")
        f_wilaya_m  = st.multiselect("Wilaya", sorted(df_marge["Wilaya"].unique()), key="mw")
        f_mois_m    = st.multiselect("Mois", sorted(df_marge["Mois"].unique()), key="mm2")
        f_annee_m   = st.multiselect("Annee", sorted(df_marge["Annee"].unique()), key="man")

    dm = df_marge.copy()
    if f_produit_m: dm = dm[dm["Produit"].isin(f_produit_m)]
    if f_cat_m:     dm = dm[dm["Categorie_Produit"].isin(f_cat_m)]
    if f_wilaya_m:  dm = dm[dm["Wilaya"].isin(f_wilaya_m)]
    if f_mois_m:    dm = dm[dm["Mois"].isin(f_mois_m)]
    if f_annee_m:   dm = dm[dm["Annee"].isin(f_annee_m)]

    ca_tot    = dm["Montant_HT"].sum()
    marge_tot = dm["Marge_Totale"].sum()
    taux      = (marge_tot / ca_tot * 100) if ca_tot > 0 else 0

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Marge Totale",      f"{marge_tot:,.0f} DA")
    with c2: st.metric("CA HT",             f"{ca_tot:,.0f} DA")
    with c3: st.metric("Taux de Marge",     f"{taux:.1f} %")
    with c4: st.metric("Produits analyses", f"{dm['Produit'].nunique()}")
    st.markdown("---")

    st.markdown('<div class="section-header">Tableau PMP — Prix Achat / Prix Vente / Marge par ligne de vente</div>', unsafe_allow_html=True)
    diag = dm[["Date_CMD","Num_CMD","Produit","Categorie_Produit","Wilaya","Annee","Mois",
                "Qte","Montant_HT","PMP","Prix_Vente_Unit","Marge_Unit","Marge_Totale"]].copy()
    diag["Taux_Marge_%"] = (diag["Marge_Totale"] / diag["Montant_HT"] * 100).round(2)
    diag["Date_CMD"]     = diag["Date_CMD"].dt.strftime("%Y-%m-%d")
    diag = diag.sort_values(["Produit","Date_CMD"]).reset_index(drop=True)
    st.dataframe(diag, use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header">Marge Totale par Produit</div>', unsafe_allow_html=True)
    mp = dm.groupby(["Produit","Categorie_Produit"]).agg(
        Marge_Totale=("Marge_Totale","sum"), CA=("Montant_HT","sum")).reset_index()
    mp["Taux_%"] = (mp["Marge_Totale"] / mp["CA"] * 100).round(2)
    mp = mp.sort_values("Marge_Totale", ascending=False)

    fig = px.bar(mp, x="Produit", y="Marge_Totale", color="Categorie_Produit",
                 title="Marge Totale par Produit et Categorie",
                 color_discrete_map=PALETTE_CAT, text_auto=".2s")
    fig.update_layout(xaxis_tickangle=-25)
    st.plotly_chart(chart(fig, 540), use_container_width=True)

    fig = px.bar(mp, x="Produit", y="Taux_%", color="Categorie_Produit",
                 title="Taux de Marge (%) par Produit",
                 color_discrete_map=PALETTE_CAT, text_auto=True)
    fig.update_layout(xaxis_tickangle=-25)
    st.plotly_chart(chart(fig, 520), use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header">Marge par Produit et Annee — taux variables selon PMP</div>', unsafe_allow_html=True)
    mp_annee = dm.groupby(["Produit","Annee"]).agg(
        Marge_Totale=("Marge_Totale","sum"), CA=("Montant_HT","sum")).reset_index()
    mp_annee["Taux_%"] = (mp_annee["Marge_Totale"] / mp_annee["CA"] * 100).round(2)

    fig = px.bar(mp_annee, x="Produit", y="Marge_Totale", color="Annee", barmode="group",
                 title="Marge Totale par Produit et Annee",
                 color_discrete_map=PALETTE_ANNEES, text_auto=".2s")
    fig.update_layout(xaxis_tickangle=-25, bargap=0.2, bargroupgap=0.1)
    st.plotly_chart(chart(fig, 520), use_container_width=True)

    fig = px.bar(mp_annee, x="Produit", y="Taux_%", color="Annee", barmode="group",
                 title="Taux de Marge (%) par Produit et Annee — PMP recalcule apres chaque entree stock",
                 color_discrete_map=PALETTE_ANNEES, text_auto=True)
    fig.update_layout(xaxis_tickangle=-25, bargap=0.2, bargroupgap=0.1)
    st.plotly_chart(chart(fig, 520), use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header">CA vs Cout Achat vs Marge par Produit</div>', unsafe_allow_html=True)
    comp = dm.groupby("Produit").agg(CA=("Montant_HT","sum"), Marge=("Marge_Totale","sum")).reset_index()
    comp["Cout"] = comp["CA"] - comp["Marge"]
    melt = comp.melt(id_vars="Produit", value_vars=["CA","Cout","Marge"],
                     var_name="Indicateur", value_name="Valeur")
    fig = px.bar(melt, x="Produit", y="Valeur", color="Indicateur", barmode="group",
                 title="Comparaison CA / Cout Achat / Marge Nette",
                 color_discrete_map=MAP_INDICATEUR, text_auto=".2s",
                 category_orders={"Indicateur": ["CA","Cout","Marge"]})
    fig.update_layout(xaxis_tickangle=-25, bargap=0.18, bargroupgap=0.08)
    st.plotly_chart(chart(fig, 560), use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header">Marge par Wilaya</div>', unsafe_allow_html=True)
    mw = dm.groupby("Wilaya")["Marge_Totale"].sum().reset_index().sort_values("Marge_Totale", ascending=False)
    c1,c2 = st.columns(2)
    with c1:
        fig = px.bar(mw, x="Wilaya", y="Marge_Totale", color="Wilaya",
                     title="Marge Totale par Wilaya", color_discrete_map=PALETTE_WILAYA, text_auto=".2s")
        st.plotly_chart(chart(fig, 440), use_container_width=True)
    with c2:
        fig = px.pie(mw, values="Marge_Totale", names="Wilaya",
                     title="Repartition Marge par Wilaya", hole=0.45, color_discrete_map=PALETTE_WILAYA)
        fig.update_traces(textposition="outside", textinfo="percent+label", textfont_size=13)
        st.plotly_chart(chart(fig, 440), use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header">Marge par Categorie de Produit</div>', unsafe_allow_html=True)
    mc = dm.groupby("Categorie_Produit")["Marge_Totale"].sum().reset_index().sort_values("Marge_Totale", ascending=False)
    top_m = mc.iloc[0]
    st.markdown(f'<div class="info-box">Categorie avec la plus grande marge : <strong>{top_m["Categorie_Produit"]}</strong> — <strong>{top_m["Marge_Totale"]:,.0f} DA</strong></div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        fig = px.bar(mc, x="Categorie_Produit", y="Marge_Totale", color="Categorie_Produit",
                     title="Marge par Categorie", color_discrete_map=PALETTE_CAT, text_auto=".2s")
        st.plotly_chart(chart(fig, 440), use_container_width=True)
    with c2:
        fig = px.pie(mc, values="Marge_Totale", names="Categorie_Produit",
                     title="Repartition Marges par Categorie", hole=0.45, color_discrete_map=PALETTE_CAT)
        fig.update_traces(textposition="outside", textinfo="percent+label", textfont_size=13)
        st.plotly_chart(chart(fig, 440), use_container_width=True)
    st.markdown("---")

    st.markdown('<div class="section-header">Evolution de la Marge par Mois et Annee</div>', unsafe_allow_html=True)
    mmois = dm.groupby(["Mois","Annee"])["Marge_Totale"].sum().reset_index()
    fig = px.line(mmois, x="Mois", y="Marge_Totale", color="Annee",
                  title="Marge Mensuelle — 2024 vs 2025",
                  color_discrete_map=PALETTE_ANNEES, markers=True, line_shape="spline")
    fig.update_traces(line_width=3, marker_size=10)
    fig.update_layout(xaxis=dict(tickmode="linear", tick0=1, dtick=1))
    st.plotly_chart(chart(fig, 500), use_container_width=True)

    st.markdown('<div class="section-header">Table Recapitulative des Marges</div>', unsafe_allow_html=True)
    recap = dm.groupby(["Produit","Categorie_Produit","Wilaya","Annee","Mois"]).agg(
        CA=("Montant_HT","sum"), Marge=("Marge_Totale","sum"), Qte=("Qte","sum")).reset_index()
    recap["Taux_Marge_%"] = (recap["Marge"] / recap["CA"] * 100).round(2)
    st.dataframe(recap.sort_values(["Produit","Annee","Mois"]), use_container_width=True)

st.markdown("---")

    unsafe_allow_html=True
)
