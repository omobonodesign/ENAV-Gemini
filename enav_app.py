import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os # Importa il modulo os
import re

# --- Configurazione Pagina ---
st.set_page_config(
    page_title="Analisi Dividendi ENAV",
    page_icon="✈️",
    layout="wide", # Utilizza l'intera larghezza della pagina
    initial_sidebar_state="collapsed"
)

# Funzione per migliorare l'aspetto visivo (simile a FDJ)
def set_page_style():
    st.markdown("""
    <style>
    .main {
        background-color: #F5F7F9; /* Leggermente grigio */
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #e1eafc; /* Blu chiaro per tab inattive */
        border-radius: 4px;
        padding: 10px 15px;
        font-weight: 500;
        color: #0d47a1; /* Blu scuro per testo tab inattive */
    }
    .stTabs [aria-selected="true"] {
        background-color: #0d47a1; /* Blu scuro per tab attiva */
        color: white;
    }
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #0d47a1; /* Bordo blu a sinistra */
    }
    h1, h2, h3 {
        color: #0d47a1; /* Blu scuro per i titoli */
    }
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }
    /* Custom styling for metrics */
     div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        border-left: 7px solid #0d47a1; /* Blu ENAV */
    }
    div[data-testid="stMetric"] > label {
        font-weight: bold;
        color: #0d47a1; /* Blu ENAV */
    }
    div[data-testid="stMetric"] > div:nth-of-type(1) { /* Target the value */
        font-size: 1.5em;
        font-weight: bold;
    }

    </style>
    """, unsafe_allow_html=True)

set_page_style()

# --- Dati Chiave Estratti (da Testo e PDF) ---
TICKER = "ENAV.MI" # Assumendo Borsa Italiana
NOME_SOCIETA = "ENAV S.p.A."
ULTIMO_DPS_PAGATO_VAL = 0.2300 # Relativo all'esercizio 2023
ANNO_ULTIMO_DPS = 2023
DPS_PROPOSTO_VAL = 0.2700 # Per esercizio 2024, pagato nel 2025
ANNO_DPS_PROPOSTO = 2024
YIELD_APPROX_PROPOSTO = 7.0 # Basato sul DPS proposto di 0.27
POLITICA_PAYOUT = ">= 80% FCF Normalizzato" #
LEVA_FINE_2024 = 0.8 # Debt/EBITDA
FCF_2024 = 199 # Milioni di Euro

# Dati storici Dividendo Per Azione (DPS) - Fonte: Analisi_ENAV_C.md
# Esercizio -> Pagamento -> Valore
dps_storico_data = {
    'Anno Esercizio': [2021, 2022, 2023],
    'DPS (€)': [0.1081, 0.1967, 0.2300],
    'Anno Pagamento': [2022, 2023, 2024]
}
df_dps = pd.DataFrame(dps_storico_data)

# Dati Proiezione Dividendi - Fonte: Analisi_ENAV_C.md
proj_dps_data = {
    'Anno Esercizio': [2024, 2025, 2026, 2027, 2028, 2029],
    'DPS Atteso (€)': [0.27, 0.28, 0.29, 0.30, 0.31, 0.32]
}
df_dps_proj = pd.DataFrame(proj_dps_data)

# Dati Finanziari Chiave (Estratti da PDF TIKR - 31/12 date)
# Selezioniamo gli ultimi 3 anni per chiarezza
fin_data = {
    'Metrica': [
        'Ricavi Totali (€M)',
        'Utile Netto (€M)',
        'EPS Diluito (€)',
        'EBITDA (€M)', # Dati EBITDA Adjusted dal PDF per coerenza
        'Free Cash Flow (FCF, €M)', # Dati FCF dal PDF
        'Debito Netto (€M)', # Dati Net Debt dal PDF
        'Leva Net Debt / EBITDA (calcolata da PDF)'
    ],
    '2021': [
        800.2,  # Revenues
        78.4,   # Net Income to Company
        0.14,   # Diluted EPS
        238.8,  # EBITDA (Adjusted)
        -242.8, # FCF (Nota: valore negativo anomalo nel PDF per il 2021)
        436.4,  # Net Debt
        1.83    # 436.4 / 238.8
    ],
    '2022': [
        907.4,  # Revenues
        105.0,  # Net Income to Company
        0.19,   # Diluted EPS
        284.4,  # EBITDA (Adjusted)
        139.1,  # FCF
        329.0,  # Net Debt
        1.16    # 329.0 / 284.4
    ],
    '2023': [
        964.0,  # Revenues
        112.9,  # Net Income to Company
        0.21,   # Diluted EPS
        313.2,  # EBITDA (Adjusted)
        100.1,  # FCF
        298.3,  # Net Debt
        0.95    # 298.3 / 313.2
    ],
     '2024 (Dati Analisi)': [
        "1037 (Piano Ind.)", #
        "126 (Piano Ind.)", #
        "N/A",
        "311 (Piano Ind.)", #
        FCF_2024,           #
        "258 (Piano Ind.)", #
        LEVA_FINE_2024      #
     ]
}
df_fin = pd.DataFrame(fin_data)

# Dati per copertura FCF/Dividendo (stimati dove necessario)
# Dividendo totale = DPS * numero azioni (approx 541.5M dal PDF)
num_azioni_approx = 541.5
fcf_coverage_data = {
    'Anno': [2021, 2022, 2023, 2024],
    'FCF (€M)': [-242.8, 139.1, 100.1, FCF_2024], # Dati PDF e Analisi
    'DPS (€)': [0.1081, 0.1967, 0.2300, DPS_PROPOSTO_VAL], # Dati Analisi
    'Dividendo Totale Stimato (€M)': [
        0.1081 * num_azioni_approx,
        0.1967 * num_azioni_approx,
        0.2300 * num_azioni_approx,
        DPS_PROPOSTO_VAL * num_azioni_approx
    ]
}
df_fcf_coverage = pd.DataFrame(fcf_coverage_data)
# Calcolo Copertura
df_fcf_coverage['Copertura FCF/Dividendo (x)'] = df_fcf_coverage['FCF (€M)'] / df_fcf_coverage['Dividendo Totale Stimato (€M)']
# Sostituisci inf con NaN per plotting
df_fcf_coverage.replace([np.inf, -np.inf], np.nan, inplace=True)

# --- Titolo e Header ---
st.title(f"✈️ Analisi Dividendi: {NOME_SOCIETA} ({TICKER})")
st.caption(f"Analisi basata sui dati del Piano Industriale 2025-2029, dati finanziari storici fino al 31/12/2023 e file di analisi.")
st.markdown("---")

# --- Metriche Chiave Dividendo ---
st.subheader("📊 Indicatori Chiave del Dividendo")
cols_metrics = st.columns(4)
with cols_metrics[0]:
    st.metric(
        label=f"Ultimo DPS Pagato (Esercizio {ANNO_ULTIMO_DPS})",
        value=f"€ {ULTIMO_DPS_PAGATO_VAL:.4f}",
        help="Dividendo pagato nel 2024 relativo all'esercizio 2023."
    )
with cols_metrics[1]:
    st.metric(
        label=f"DPS Proposto (Esercizio {ANNO_DPS_PROPOSTO})",
        value=f"€ {DPS_PROPOSTO_VAL:.4f}",
        help="Dividendo proposto per l'esercizio 2024 (pagamento nel 2025), come da Piano Industriale."
    )
with cols_metrics[2]:
    st.metric(
        label=f"Dividend Yield (Stimato su DPS {DPS_PROPOSTO_VAL:.2f}€)",
        value=f"~ {YIELD_APPROX_PROPOSTO:.1f}%",
        help=f"Rendimento stimato basato sul dividendo proposto per l'esercizio 2024. Il rendimento effettivo dipenderà dal prezzo dell'azione al momento dello stacco."
    )
with cols_metrics[3]:
    st.metric(
        label="Politica di Payout",
        value=POLITICA_PAYOUT,
        help="Politica dichiarata dalla società per la distribuzione del Free Cash Flow normalizzato."
    )
st.markdown("---")

# --- Tab per organizzare i grafici ---
tabs = st.tabs([
    "Dividendi: Storico e Proiezioni",
    "Sostenibilità del Dividendo",
    "Dati Finanziari Chiave",
    "Analisi Completa (Testo)",
    "Rischi Principali"
])

# TAB 1: Dividendi Storici e Proiezioni
with tabs[0]:
    st.header("Dividendi: Storico e Proiezioni Future")
    col1, col2 = st.columns(2)

    with col1:
        # --- Grafico Storico DPS ---
        st.subheader("📈 Crescita Storica del Dividendo per Azione")
        fig_dps_storico = px.line(
            df_dps,
            x='Anno Esercizio',
            y='DPS (€)',
            title="Andamento DPS Storico ENAV (Esercizi 2021-2023)",
            markers=True,
            text='DPS (€)'
        )
        fig_dps_storico.update_traces(textposition="top center", line=dict(width=3, color='#0d47a1'), texttemplate='%{text:.4f}')
        fig_dps_storico.update_layout(
            xaxis_title="Anno Esercizio Fiscale",
            yaxis_title="Dividendo per Azione (€)",
            yaxis_tickformat=".4f",
            hovermode="x unified",
            height=400
        )
        # Aggiungere barra per confronto visivo crescita
        fig_dps_bar = px.bar(
             df_dps,
             x='Anno Esercizio',
             y='DPS (€)',
             title="Crescita DPS Storico ENAV (Barre)",
             text='DPS (€)'
        )
        fig_dps_bar.update_traces(marker_color='#64b5f6', texttemplate='%{text:.4f}', textposition='outside')
        fig_dps_bar.update_layout(
            xaxis_title="Anno Esercizio Fiscale",
            yaxis_title="Dividendo per Azione (€)",
            yaxis_tickformat=".4f",
            height=400
        )

        st.plotly_chart(fig_dps_storico, use_container_width=True)
        st.plotly_chart(fig_dps_bar, use_container_width=True)
        st.caption("Fonte: Dati estratti da Analisi_ENAV_C.md. Si nota la ripresa e crescita del dividendo post-pandemia.")

    with col2:
        # --- Grafico Proiezioni DPS ---
        st.subheader("🔮 Proiezione Dividendi (Piano Industriale 2025-2029)")

        # Uniamo storico e proiezioni per un grafico completo
        df_dps_completo = pd.concat([
            df_dps[['Anno Esercizio', 'DPS (€)']].assign(Tipo='Storico'),
            df_dps_proj.rename(columns={'DPS Atteso (€)': 'DPS (€)'}).assign(Tipo='Proiezione Piano Ind.')
        ]).reset_index(drop=True)

        fig_dps_proj = px.line(
            df_dps_completo,
            x='Anno Esercizio',
            y='DPS (€)',
            title="Dividendo per Azione: Storico (2021-23) e Proiezioni Piano (2024-29)",
            markers=True,
            text='DPS (€)',
            color='Tipo',
            color_discrete_map={'Storico': '#0d47a1', 'Proiezione Piano Ind.': '#ffa726'}
        )
        fig_dps_proj.update_traces(textposition="top center", line=dict(width=3), texttemplate='%{text:.2f}')
        fig_dps_proj.update_layout(
            xaxis_title="Anno Esercizio Fiscale",
            yaxis_title="Dividendo per Azione (€)",
            yaxis_tickformat=".2f",
            hovermode="x unified",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        # Calcolo CAGR Proiettato 2024-2029
        dps_2024 = df_dps_proj[df_dps_proj['Anno Esercizio'] == 2024]['DPS Atteso (€)'].iloc[0]
        dps_2029 = df_dps_proj[df_dps_proj['Anno Esercizio'] == 2029]['DPS Atteso (€)'].iloc[0]
        anni_cagr = 2029 - 2024
        cagr_proj = ((dps_2029 / dps_2024)**(1 / anni_cagr) - 1) * 100

        fig_dps_proj.add_annotation(
            x=2026.5, y=(dps_2024 + dps_2029)/2 , # Posizione approssimativa
            text=f"CAGR Proiettato<br>2024-2029: ~{cagr_proj:.1f}%",
            showarrow=False,
            font=dict(size=12, color="orange"),
            bgcolor="rgba(255,255,255,0.7)"
        )

        st.plotly_chart(fig_dps_proj, use_container_width=True)
        st.caption(f"Fonte: Dati estratti da Analisi_ENAV_C.md. Il piano industriale prevede una crescita annua composta (CAGR) di circa il {cagr_proj:.1f}% per il dividendo nel periodo 2024-2029.")

# TAB 2: Sostenibilità del Dividendo
with tabs[1]:
    st.header("Sostenibilità del Dividendo")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💰 Copertura FCF vs Dividendo Totale")
        fig_fcf_cov = make_subplots(specs=[[{"secondary_y": True}]])

        # Barre per FCF e Dividendo Totale
        fig_fcf_cov.add_trace(
            go.Bar(
                x=df_fcf_coverage['Anno'],
                y=df_fcf_coverage['FCF (€M)'],
                name='Free Cash Flow (€M)',
                marker_color='#64b5f6', # Blu chiaro
                opacity=0.8
            ),
            secondary_y=False,
        )
        fig_fcf_cov.add_trace(
            go.Bar(
                x=df_fcf_coverage['Anno'],
                y=df_fcf_coverage['Dividendo Totale Stimato (€M)'],
                name='Dividendo Totale Stimato (€M)',
                marker_color='#0d47a1', # Blu scuro
                 opacity=0.8
            ),
            secondary_y=False,
        )

        # Linea per rapporto di copertura
        fig_fcf_cov.add_trace(
            go.Scatter(
                x=df_fcf_coverage['Anno'],
                y=df_fcf_coverage['Copertura FCF/Dividendo (x)'],
                name='Copertura FCF/Dividendo (x)',
                mode='lines+markers+text',
                line=dict(color='#ffa726', width=3), # Arancione
                marker=dict(size=8),
                text=df_fcf_coverage['Copertura FCF/Dividendo (x)'],
                texttemplate='%{text:.2f}x',
                textposition='top center'

            ),
            secondary_y=True,
        )

        fig_fcf_cov.update_layout(
            title='Free Cash Flow vs Dividendo Totale Stimato (2021-2024)',
            barmode='group',
            xaxis_title='Anno',
            yaxis_title='€ Milioni',
            yaxis2_title='Rapporto di Copertura (x)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=450,
            yaxis=dict(range=[min(0, df_fcf_coverage['FCF (€M)'].min()*1.1 if pd.notna(df_fcf_coverage['FCF (€M)'].min()) else 0) , max(df_fcf_coverage['FCF (€M)'].max(), df_fcf_coverage['Dividendo Totale Stimato (€M)'].max())*1.1]),
            yaxis2=dict(range=[0, max(2, df_fcf_coverage['Copertura FCF/Dividendo (x)'].max()*1.1 if pd.notna(df_fcf_coverage['Copertura FCF/Dividendo (x)'].max()) else 2)]) # Range y2 da 0 a max copertura o 2
        )
        fig_fcf_cov.update_yaxes(secondary_y=True, tickformat=".1f")
        # Aggiungere linea orizzontale a 1x sulla copertura
        fig_fcf_cov.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Copertura 1x", annotation_position="bottom right", secondary_y=True)

        st.plotly_chart(fig_fcf_cov, use_container_width=True)
        st.caption("Fonte: FCF da PDF TIKR e Analisi, Dividendo Totale calcolato (DPS * 541.5M azioni). Il FCF 2021 riportato nel PDF è anomalo. Nel 2024, il FCF (€199M) copre ampiamente il dividendo proposto (€0.27 * 541.5M ≈ €146M), con un rapporto di copertura > 1.3x.")
        st.warning("Nota: I dati FCF storici dal PDF TIKR presentano anomalie, in particolare per il 2021. La sostenibilità si basa maggiormente sui dati 2023 e sulle proiezioni del piano 2024-2029.")

    with col2:
        st.subheader("⚖️ Payout Ratio e Leva Finanziaria")
        # Payout = Dividendo Totale / Utile Netto
        # Necessitiamo Utile Netto (dal df_fin)
        utile_netto = df_fin[df_fin['Metrica'] == 'Utile Netto (€M)'].iloc[0]

        payout_data = {
            'Anno': [2021, 2022, 2023],
            'Utile Netto (€M)': [utile_netto['2021'], utile_netto['2022'], utile_netto['2023']],
            'Dividendo Totale (€M)': [df_fcf_coverage.loc[0, 'Dividendo Totale Stimato (€M)'],
                                        df_fcf_coverage.loc[1, 'Dividendo Totale Stimato (€M)'],
                                        df_fcf_coverage.loc[2, 'Dividendo Totale Stimato (€M)']]
        }
        df_payout = pd.DataFrame(payout_data)
        df_payout['Payout Ratio su Utile Netto (%)'] = (df_payout['Dividendo Totale (€M)'] / df_payout['Utile Netto (€M)']) * 100

        # Leva finanziaria
        leva_data = {
            'Anno': [2021, 2022, 2023, 2024],
             'Leva Net Debt/EBITDA': [
                 df_fin[df_fin['Metrica'] == 'Leva Net Debt / EBITDA (calcolata da PDF)'].iloc[0]['2021'],
                 df_fin[df_fin['Metrica'] == 'Leva Net Debt / EBITDA (calcolata da PDF)'].iloc[0]['2022'],
                 df_fin[df_fin['Metrica'] == 'Leva Net Debt / EBITDA (calcolata da PDF)'].iloc[0]['2023'],
                 LEVA_FINE_2024 # Dato da analisi
             ]
        }
        df_leva = pd.DataFrame(leva_data)

        # Grafico Combinato Payout e Leva
        fig_pay_lev = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                    subplot_titles=("Payout Ratio su Utile Netto (%)", "Leva Finanziaria (Net Debt / EBITDA)"))

        fig_pay_lev.add_trace(
            go.Bar(
                x=df_payout['Anno'],
                y=df_payout['Payout Ratio su Utile Netto (%)'],
                name='Payout Ratio (%)',
                marker_color='#64b5f6',
                text=df_payout['Payout Ratio su Utile Netto (%)'],
                texttemplate='%{text:.1f}%',
                textposition='outside'
            ), row=1, col=1
        )
        fig_pay_lev.add_trace(
            go.Scatter(
                x=df_leva['Anno'],
                y=df_leva['Leva Net Debt/EBITDA'],
                name='Leva (x)',
                mode='lines+markers+text',
                line=dict(color='#0d47a1', width=3),
                marker=dict(size=8),
                 text=df_leva['Leva Net Debt/EBITDA'],
                texttemplate='%{text:.2f}x',
                textposition='top center'
            ), row=2, col=1
        )

        # Aggiungere linea target politica payout (80% FCF, non Utile Netto)
        # Non mettiamo la linea target payout qui perchè si basa su Utile Netto e la politica è su FCF.
        # Aggiungere linea target leva (se rilevante, es. sotto 1.5x)
        fig_pay_lev.add_hline(y=1.0, line_dash="dot", line_color="grey", row=2, col=1)

        fig_pay_lev.update_layout(
            height=500,
            showlegend=False,
            xaxis_title='Anno',
            yaxis1_title='Payout Ratio (%)',
            yaxis2_title='Leva (x)',
            yaxis1_range=[0, max(100, df_payout['Payout Ratio su Utile Netto (%)'].max() * 1.1 if pd.notna(df_payout['Payout Ratio su Utile Netto (%)'].max()) else 100)],
            yaxis2_range=[0, max(2, df_leva['Leva Net Debt/EBITDA'].max() * 1.1 if pd.notna(df_leva['Leva Net Debt/EBITDA'].max()) else 2)]
        )
        fig_pay_lev.update_yaxes(tickformat=".1f", row=1, col=1)
        fig_pay_lev.update_yaxes(tickformat=".2f", row=2, col=1)

        st.plotly_chart(fig_pay_lev, use_container_width=True)
        st.caption("Payout Ratio calcolato su Utile Netto (Fonte PDF). Leva Finanziaria da PDF e Analisi. Si nota il payout su utile netto superiore al 100% nel 2023, indicando che il dividendo è guidato più dal FCF (come da politica) che dall'utile contabile. La leva è in miglioramento e si prevede scenda ulteriormente.")


# TAB 3: Dati Finanziari Chiave
with tabs[2]:
    st.header("Dati Finanziari Chiave")
    st.subheader("📈 Trend Finanziari Storici (2021-2023)")

    # Estrarre dati per grafico trend
    metrics_to_plot = ['Ricavi Totali (€M)', 'EBITDA (€M)', 'Utile Netto (€M)', 'Free Cash Flow (FCF, €M)']
    df_fin_plot = df_fin[df_fin['Metrica'].isin(metrics_to_plot)].set_index('Metrica')[['2021', '2022', '2023']]
    df_fin_plot = df_fin_plot.apply(pd.to_numeric, errors='coerce') # Converti in numerico, ignora errori (per N/A)
    df_fin_plot = df_fin_plot.transpose() # Anni come righe
    df_fin_plot.index.name = 'Anno'
    df_fin_plot.reset_index(inplace=True)


    fig_trends = px.line(df_fin_plot, x='Anno', y=metrics_to_plot,
                         title="Andamento Ricavi, EBITDA, Utile Netto e FCF (2021-2023)",
                         markers=True)

    fig_trends.update_layout(
        yaxis_title='€ Milioni',
        xaxis_title='Anno',
        hovermode="x unified",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_trends, use_container_width=True)
    st.caption("Fonte: Dati PDF TIKR. Ricavi, EBITDA e Utile Netto mostrano un trend di crescita. FCF mostra volatilità, con un dato 2021 anomalo.")


    st.subheader("🔢 Tabella Finanziaria Riassuntiva (Ultimi Anni e Dati Piano 2024)")
    # Mostra la tabella con dati fino al 2024 (da piano)
    st.dataframe(df_fin.set_index('Metrica'), use_container_width=True)
    st.caption("Fonte: Dati 2021-2023 da PDF TIKR, Dati 2024 da Piano Industriale/Analisi. Leva 2021-23 calcolata da dati PDF, 2024 da Analisi. FCF 2021 anomalo.")


# TAB 4: Analisi Completa (Testo)
with tabs[3]:
    st.header("📝 Analisi Dettagliata ENAV (da file .md)")

    analysis_content = ""
    try:
        # Leggi il contenuto del file markdown
        # Assicurati che il file 'Analisi_ENAV_C.md' sia nella stessa directory dello script Python
        if os.path.exists('Analisi_ENAV_C.md'):
            with open('Analisi_ENAV_C.md', 'r', encoding='utf-8') as f:
                analysis_content = f.read()
                # Rimuove i tag [source: ...] o se presenti (non dovrebbero esserci nel file originale)
                analysis_content = re.sub(r'\s*\[(source|cite):\s*\d+.*?\]', '', analysis_content)

            # Suddivisione approssimativa basata sui titoli markdown (## o ###)
            sections = {}
            current_section = "Introduzione / Sommario" # Default per il testo iniziale
            sections[current_section] = ""

            # Regex per trovare i titoli principali (## Titolo o # Titolo) e i sottotitoli numerati (## N. Titolo)
            # Modificato per catturare anche ###
            title_pattern = re.compile(r"^(#+)\s*(\d*\.?\s*\*?.*?\*?)$", re.MULTILINE)

            last_index = 0
            for match in title_pattern.finditer(analysis_content):
                level = len(match.group(1)) # Numero di #
                title = match.group(2).strip().replace('*','').strip()
                start_index = match.start()

                # Aggiunge il testo precedente alla sezione corrente
                sections[current_section] += analysis_content[last_index:start_index].strip() + "\n\n"

                # Pulisce il titolo
                clean_title = re.sub(r"^\d+\.\s+", "", title) # Rimuove numeri iniziali
                current_section = clean_title
                sections[current_section] = "" # Inizia una nuova sezione
                last_index = match.end()

            # Aggiunge l'ultimo pezzo di testo all'ultima sezione
            sections[current_section] += analysis_content[last_index:].strip()

            # Visualizza le sezioni con expander
            st.markdown("Espandi le sezioni per leggere l'analisi completa fornita nel file `Analisi_ENAV_C.md`.")
            # Espandi le prime sezioni di default
            expanded_sections = ["Introduzione / Sommario", "Executive Summary", "1. Storico dei Dividendi e Rendimento"]

            for title, content in sections.items():
                if content.strip(): # Mostra solo sezioni con contenuto
                     # Pulisci ulteriormente il titolo per l'ID dell'expander
                    expander_title = title.replace(":", "").replace("?", "").replace("/", "-")
                    is_expanded = any(sub in expander_title for sub in expanded_sections)

                    with st.expander(f"**{title}**", expanded=is_expanded):
                        # Sostituisce le tabelle Markdown con HTML per st.markdown
                        # Questo è un tentativo base, tabelle complesse potrebbero non rendere perfettamente
                        content_html = content.replace('\n|', '\n| ') # Assicura spazi per split
                        lines = content_html.split('\n')
                        in_table = False
                        table_html = ""
                        processed_content = ""

                        for line in lines:
                            line_stripped = line.strip()
                            if line_stripped.startswith('|') and line_stripped.endswith('|'):
                                if not in_table:
                                    # Controlla se è la riga separatore prima di iniziare la tabella
                                    if '---' in line_stripped:
                                        processed_content += line + "\n" # Mantieni la riga markdown se non è una tabella valida
                                        continue # Salta questa riga se è solo separatore senza header

                                    in_table = True
                                    table_html = "<div style='overflow-x:auto;'><table style='width:100%; border-collapse: collapse; border: 1px solid #ddd;'>\n"
                                    # Gestione header
                                    headers = [h.strip() for h in line_stripped.strip('|').split('|')]
                                    table_html += "  <thead style='background-color: #f2f2f2;'>\n    <tr>\n"
                                    for header in headers:
                                        table_html += f"      <th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>{header}</th>\n"
                                    table_html += "    </tr>\n  </thead>\n  <tbody>\n"
                                # Ignora la linea separatore ' |---|---| '
                                elif '---' not in line_stripped:
                                    cells = [c.strip() for c in line_stripped.strip('|').split('|')]
                                    table_html += "    <tr>\n"
                                    for cell in cells:
                                         # Rimuovi eventuali ** markdown per il grassetto e applica stile
                                        cell_clean = cell.replace('**', '')
                                        style = " style='border: 1px solid #ddd; padding: 8px;'"
                                        if cell != cell_clean: # Era grassetto
                                             style = " style='border: 1px solid #ddd; padding: 8px; font-weight: bold;'"

                                        table_html += f"      <td{style}>{cell_clean}</td>\n"
                                    table_html += "    </tr>\n"
                            else:
                                if in_table:
                                    in_table = False
                                    table_html += "  </tbody>\n</table></div>\n"
                                    processed_content += table_html
                                    table_html = ""
                                processed_content += line + "\n"

                        if in_table: # Chiudi la tabella se il file finisce con essa
                             table_html += "  </tbody>\n</table></div>\n"
                             processed_content += table_html

                        # Sostituisci ### con h4 e ## con h3 per una migliore gerarchia HTML
                        processed_content = re.sub(r'^### (.*?)$', r'<h4>\1</h4>', processed_content, flags=re.MULTILINE)
                        processed_content = re.sub(r'^## (.*?)$', r'<h3>\1</h3>', processed_content, flags=re.MULTILINE)
                        # Converti liste markdown in HTML
                        processed_content = re.sub(r'^\* (.*?)$', r'<li>\1</li>', processed_content, flags=re.MULTILINE)
                        processed_content = re.sub(r'^\- (.*?)$', r'<li>\1</li>', processed_content, flags=re.MULTILINE)
                        processed_content = re.sub(r'(<li>.*?</li>\n?)+', r'<ul>\g</ul>', processed_content, flags=re.DOTALL)


                        st.markdown(processed_content, unsafe_allow_html=True)
        else:
             st.error("Errore: File 'Analisi_ENAV_C.md' non trovato nella directory dell'app.")
             analysis_content = "Contenuto dell'analisi non disponibile (file non trovato)."


    except FileNotFoundError:
        st.error("Errore: File 'Analisi_ENAV_C.md' non trovato nella directory dell'app.")
        analysis_content = "Contenuto dell'analisi non disponibile (file non trovato)."
    except Exception as e:
        st.error(f"Errore nella lettura o elaborazione del file 'Analisi_ENAV_C.md': {e}")
        analysis_content = "Errore nel caricamento del contenuto dell'analisi."

# TAB 5: Rischi Principali
with tabs[4]:
    st.header("🚨 Principali Rischi da Considerare")
    st.markdown("I seguenti rischi sono stati evidenziati nel documento di analisi:")

    st.warning("""
    * **Rischi Regolatori:**
        * Cambiamenti nei parametri regolatori (es. WACC, tariffe) potrebbero influenzare la redditività.
        * Il "reset regolatorio" (come quello per RP4, 2025-2029) causa una temporanea, ma fisiologica, flessione dei risultati all'inizio del periodo.
    * **Rischi di Traffico:**
        * Eventi straordinari (pandemie, crisi geopolitiche, disastri naturali) possono impattare significativamente i volumi di traffico aereo.
        * Esistono meccanismi di compensazione regolatori nel medio termine, ma shock acuti possono avere effetti immediati.
    * **Rischi Esecutivi:**
        * Rischio nell'esecuzione dei piani di crescita, specialmente nelle attività non regolamentate (espansione internazionale, droni, servizi digitali).
        * Rischi legati all'integrazione di eventuali acquisizioni (M&A) pianificate (€350M allocati nel piano).
    * **Altri Rischi:**
        * Rischi operativi (scioperi, guasti tecnologici).
        * Rischi legati alla sostenibilità e agli obiettivi ESG.
        * Aumento dei tassi d'interesse (impatto sul costo del debito futuro, anche se la leva è bassa).
    """, icon="⚠️")

    st.info("""
    **Contesto RP4 (Reset Regolatorio 2025):**
    L'analisi evidenzia un previsto calo dell'EBITDA nel 2025 (-28% vs 2024) dovuto al reset dei parametri regolatori. Questo è un effetto tecnico atteso e non dovrebbe compromettere la crescita del dividendo pianificata, grazie alla solida generazione di cassa e alla politica di payout basata sul FCF. L'EBITDA è previsto poi recuperare e crescere significativamente fino al 2029.
    """, icon="ℹ️")

# --- Conclusioni Specifiche per Investitore Dividend ---
st.markdown("---")
st.subheader("🎯 Conclusioni per l'Investitore Orientato ai Dividendi (Basate sull'Analisi)")
st.markdown(f"""
Basato sull'analisi fornita nel file `Analisi_ENAV_C.md`:

**Punti di Forza (Pro-Dividendo):**
* ✅ **Politica Dividendi Chiara e Generosa:** Payout target esplicito >= 80% del FCF normalizzato, con forte impegno del management alla remunerazione.
* ✅ **Yield Attraente:** Rendimento stimato sul dividendo proposto per il 2024 (~7%) competitivo nel panorama delle utility e del mercato italiano.
* ✅ **Crescita Prevista del Dividendo:** Il Piano Industriale 2025-2029 delinea una traiettoria di crescita annua costante del DPS (+4% CAGR circa).
* ✅ **Solidità del Business Regolato:** Il core business garantisce flussi di cassa stabili e prevedibili, protetti da meccanismi regolatori (es. inflazione, traffico, WACC più alto in RP4).
* ✅ **Forte Generazione di Cassa:** Previsto FCF cumulato di ~€1 miliardo nel 2025-2029, sufficiente a coprire dividendi (€813M) e investimenti, permettendo anche l'azzeramento del debito.
* ✅ **Bassa Leva Finanziaria:** Rapporto Net Debt/EBITDA basso (0.8x a fine 2024) e in ulteriore riduzione, garantendo flessibilità finanziaria.

**Rischi e Considerazioni (Contro-Dividendo):**
* ⚠️ **Reset Regolatorio 2025:** Impatto negativo sull'EBITDA nel primo anno del nuovo periodo (2025), sebbene non si preveda un impatto sulla crescita del dividendo.
* ⚠️ **Dipendenza dal Traffico Aereo:** Sensibilità a shock esterni che influenzano i volumi di volo, anche se mitigata da meccanismi regolatori.
* ⚠️ **Esecuzione Crescita Non Regolata:** Il successo nell'espansione dei business non regolati (che hanno margini potenzialmente diversi) è cruciale per la crescita futura oltre il perimetro regolato.
* ⚠️ **Execution Risk M&A:** L'eventuale utilizzo della capacità di debito per M&A introduce rischi di integrazione e valutazione.

**In Sintesi:** ENAV appare come un investimento "core" per chi cerca un dividendo elevato, crescente e sostenibile, supportato da un business regolato solido e da una gestione finanziaria prudente. I rischi principali sono legati a fattori macro/settoriali (traffico) e all'esecuzione della strategia di crescita, ma la visibilità sui dividendi futuri data dal piano industriale è un elemento distintivo positivo.
""", unsafe_allow_html=True)

# Footer con disclaimer
st.markdown("---")
with st.container():
    st.markdown("""
    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; font-size: 0.9em; border-left: 5px solid #0d47a1;">
        <h3 style="color: #d32f2f; margin-bottom: 10px;">⚠️ DISCLAIMER</h3>
        <p style="margin-bottom: 5px;">Le informazioni contenute in questa applicazione web sono generate automaticamente sulla base dei documenti forniti ('Analisi_ENAV_C.md', 'TIKR - ENAV - Financials (...).pdf') e sono presentate esclusivamente a scopo informativo generale e/o educativo. Non costituiscono e non devono essere interpretate come consulenza finanziaria, legale, fiscale o di investimento.</p>
        <p style="margin-bottom: 5px;">Investire nei mercati finanziari comporta rischi significativi, inclusa la possibilità di perdere l'intero capitale investito. Le performance passate non sono indicative né garanzia di risultati futuri. I dati finanziari storici (specialmente FCF) potrebbero presentare anomalie o richiedere reclassification/normalizzazione non effettuata in questa sede.</p>
        <p style="margin-bottom: 5px;">Si raccomanda vivamente di condurre la propria analisi approfondita (due diligence), verificare i dati da fonti ufficiali della società e consultare un consulente finanziario indipendente e qualificato prima di prendere qualsiasi decisione di investimento basata su queste informazioni.</p>
        <p style="text-align: right; margin-top: 10px; font-style: italic;">Applicazione generata da AI.</p>
    </div>
    """, unsafe_allow_html=True)
