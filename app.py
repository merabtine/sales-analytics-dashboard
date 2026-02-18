import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# Chargement des données
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("ventes.csv")
    df["Date_CMD"] = pd.to_datetime(df["Date_CMD"])
    df["Mois"] = df["Date_CMD"].dt.month
    df["Annee"] = df["Date_CMD"].dt.year
    return df

df = load_data()

st.title("📊 Analyse des Ventes - Business Intelligence")

# -----------------------------
# Filtres dynamiques
# -----------------------------
st.sidebar.header("🔎 Filtres")

produits = st.sidebar.multiselect(
    "Produit",
    df["Produit"].unique(),
    default=df["Produit"].unique()
)

categories = st.sidebar.multiselect(
    "Catégorie",
    df["Categorie"].unique(),
    default=df["Categorie"].unique()
)

clients = st.sidebar.multiselect(
    "Client",
    df["Client"].unique(),
    default=df["Client"].unique()
)

annees = st.sidebar.multiselect(
    "Année",
    df["Annee"].unique(),
    default=df["Annee"].unique()
)

type_vente = st.sidebar.multiselect(
    "Type Vente",
    df["Type_Vente"].unique(),
    default=df["Type_Vente"].unique()
)

# -----------------------------
# Application des filtres
# -----------------------------
df_filtered = df[
    (df["Produit"].isin(produits)) &
    (df["Categorie"].isin(categories)) &
    (df["Client"].isin(clients)) &
    (df["Annee"].isin(annees)) &
    (df["Type_Vente"].isin(type_vente))
]

# -----------------------------
# Indicateurs globaux
# -----------------------------
st.subheader("📌 Indicateurs Globaux")

col1, col2 = st.columns(2)

with col1:
    st.metric("Chiffre d'Affaire Total (HT)", f"{df_filtered['Montant_HT'].sum():,.0f} DA")

with col2:
    st.metric("Quantité Totale Vendue", f"{df_filtered['Quantite'].sum():,.0f}")

# -----------------------------
# Graphique CA par Produit
# -----------------------------
st.subheader("📈 Chiffre d'Affaire par Produit")

ca_produit = df_filtered.groupby("Produit")["Montant_HT"].sum().reset_index()

fig1 = px.bar(
    ca_produit,
    x="Produit",
    y="Montant_HT",
    title="Classement des Produits par Chiffre d'Affaire",
)

st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
# Graphique Quantités par Mois
# -----------------------------
st.subheader("📊 Quantités Vendues par Mois")

qte_mois = df_filtered.groupby(["Annee", "Mois"])["Quantite"].sum().reset_index()

fig2 = px.line(
    qte_mois,
    x="Mois",
    y="Quantite",
    color="Annee",
    markers=True,
    title="Evolution des Quantités Vendues",
)

st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# Produits vendus après 01 Février 2025
# -----------------------------
st.subheader("🗂 Produits vendus après 01 Février 2025")

df_after = df[df["Date_CMD"] > "2025-02-01"]

st.dataframe(df_after[["Date_CMD", "Produit", "Client", "Montant_HT"]])

# -----------------------------
# Catégorie la plus rentable
# -----------------------------
st.subheader("🏆 Catégorie ayant généré le plus de CA")

cat_ca = df_filtered.groupby("Categorie")["Montant_HT"].sum().reset_index()
best_cat = cat_ca.sort_values("Montant_HT", ascending=False).iloc[0]

st.success(f"Catégorie gagnante : {best_cat['Categorie']} avec {best_cat['Montant_HT']:,.0f} DA")
