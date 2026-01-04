import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.express as px
from pathlib import Path

# ======================================
# CONFIG STREAMLIT
# ======================================
st.set_page_config(
    page_title="CoinAfrique Animal Data",
    layout="wide"
)

# ======================================
# CONSTANTES
# ======================================
DEFAULT_DATA_PATH = Path("data/data_animaux.csv")

# ======================================
# FONCTION DE SCRAPING
# ======================================
def scrape_coinafrique(categories, max_pages):
    df = pd.DataFrame()

    for categorie, infos in categories.items():
        pages = min(infos["pages"], max_pages)

        for page in range(1, pages + 1):
            url = f"{infos['url']}?page={page}"
            try:
                res = requests.get(url, timeout=10)
                res.raise_for_status()
            except Exception:
                continue

            soup = BeautifulSoup(res.content, "html.parser")
            containers = soup.select("div.col.s6.m4.l3")

            data = []
            for c in containers:
                try:
                    data.append({
                        "categorie": categorie,
                        "page": page,
                        "nom": c.select_one("p.ad__card-description a").text.strip(),
                        "prix": c.select_one("p.ad__card-price a").text.replace("CFA", "").strip(),
                        "adresse": c.select_one("p.ad__card-location span").text.strip(),
                        "image": c.select_one("img.ad__card-img")["src"]
                    })
                except Exception:
                    pass

            df = pd.concat([df, pd.DataFrame(data)], ignore_index=True)

    return df

# ======================================
# DONNÉES DE CONFIGURATION
# ======================================
categories = {
    "chiens": {"url": "https://sn.coinafrique.com/categorie/chiens", "pages": 11},
    "moutons": {"url": "https://sn.coinafrique.com/categorie/moutons", "pages": 16},
    "poules_lapins_pigeons": {
        "url": "https://sn.coinafrique.com/categorie/poules-lapins-et-pigeons",
        "pages": 10
    },
    "autres_animaux": {"url": "https://sn.coinafrique.com/categorie/autres-animaux", "pages": 6},
}

# ======================================
# SIDEBAR
# ======================================
st.sidebar.title("🐾 Animal Data")

nb_pages = st.sidebar.number_input(
    "Pages à récupérer",
    min_value=1,
    max_value=20,
    value=2,
    help="Après modification, cliquez sur 'Scrape data' pour actualiser."
)

option = st.sidebar.selectbox(
    "Menu",
    (
        "Scrape data using BeautifulSoup",
        "Upload external file",
        "Dashboard",
        "Evaluate the App"
    )
)

# ======================================
# SESSION STATE
# ======================================
if "data" not in st.session_state:
    st.session_state.data = None

if "source" not in st.session_state:
    st.session_state.source = None

# ======================================
# HEADER
# ======================================
st.markdown(
    "<h1 style='text-align:center;'>🐶🐔🐑 CoinAfrique – Animal Market Data 🐑🐔🐶</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align:center;'>Analyse des annonces d’animaux au Sénégal</p>",
    unsafe_allow_html=True
)

# ======================================
# OPTION 1 : SCRAPING
# ======================================
if option == "Scrape data using BeautifulSoup":

    st.info(
        "Après avoir changé le nombre de pages, cliquez sur **Scrape data** pour mettre à jour les données."
    )

    if st.button("🚀 Scrape data"):
        with st.spinner("Scraping en cours..."):
            st.session_state.data = scrape_coinafrique(categories, nb_pages)
            st.session_state.source = "Scraping"
        st.success("Scraping terminé")

    if st.session_state.data is not None:
        st.dataframe(st.session_state.data, use_container_width=True)

# ======================================
# OPTION 2 : UPLOAD FILE (AVEC FICHIER WEB SCRAPER)
# ======================================
elif option == "Upload external file":

    st.subheader("📂 Gestion des données")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Charger un fichier CSV ou Excel",
            type=["csv", "xlsx"]
        )

    with col2:
        use_default = st.button("🔄 Charger le fichier obtenu avec web scraper")

    # Charger fichier web scraper
    if use_default:
        if DEFAULT_DATA_PATH.exists():
            st.session_state.data = pd.read_csv(DEFAULT_DATA_PATH)
            st.session_state.source = "Fichier obtenu avec web scraper"
            st.success("Fichier web scraper chargé")
        else:
            st.error("Fichier web scraper introuvable")

    # Charger fichier utilisateur
    elif uploaded_file:
        try:
            df = (
                pd.read_csv(uploaded_file)
                if uploaded_file.name.endswith(".csv")
                else pd.read_excel(uploaded_file)
            )
            st.session_state.data = df
            st.session_state.source = "Fichier utilisateur"
            st.success("Fichier utilisateur chargé")
        except Exception as e:
            st.error(e)

    # Chargement automatique initial
    elif st.session_state.data is None and DEFAULT_DATA_PATH.exists():
        st.session_state.data = pd.read_csv(DEFAULT_DATA_PATH)
        st.session_state.source = "Fichier par défaut"

    if st.session_state.data is not None:
        st.caption(f"Source des données : {st.session_state.source}")
        st.dataframe(st.session_state.data, use_container_width=True)

# ======================================
# OPTION 3 : DASHBOARD
# ======================================
elif option == "Dashboard":

    if st.session_state.data is None or st.session_state.data.empty:
        st.warning("Aucune donnée disponible.")
    else:
        df = st.session_state.data.copy()

        if "prix" in df.columns:
            df["prix"] = pd.to_numeric(df["prix"], errors="coerce")

        st.markdown("<h2 style='text-align:center;'>📊 Dashboard Analytique</h2>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        fig1 = px.histogram(df, x="categorie", title="Nombre d'annonces")
        fig1.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        col1.plotly_chart(fig1, use_container_width=True)

        fig2 = px.box(df, x="categorie", y="prix", title="Distribution des prix")
        fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        col2.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)

        avg_price = df.groupby("categorie", as_index=False)["prix"].mean()
        fig3 = px.bar(avg_price, x="categorie", y="prix", title="Prix moyen")
        fig3.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        col3.plotly_chart(fig3, use_container_width=True)

        repartition = df["categorie"].value_counts().reset_index()
        repartition.columns = ["categorie", "count"]
        fig4 = px.pie(repartition, names="categorie", values="count", title="Répartition des annonces")
        fig4.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        col4.plotly_chart(fig4, use_container_width=True)

# ======================================
# OPTION 4 : EVALUATION
# ======================================
elif option == "Evaluate the App":
    st.subheader("Évaluation")
    st.markdown("Donnez votre avis sur l’application.")
    if st.button("Ouvrir le formulaire"):
        st.markdown("[Accéder au formulaire](https://ee.kobotoolbox.org/single/eDXBD6en)", unsafe_allow_html=True)
