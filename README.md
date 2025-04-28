# ENAV S.p.A. - Analisi Dividendi (Applicazione Streamlit)

Questa è un'applicazione web interattiva costruita con Streamlit che presenta un'analisi finanziaria focalizzata sui dividendi per la società ENAV S.p.A. (Ticker: ENAV).

## 🎯 Obiettivo

L'applicazione è pensata per un investitore di lungo periodo interessato principalmente al reddito da dividendo e fornisce:
* Metriche chiave del dividendo (DPS, Yield, Policy).
* Visualizzazione dello storico dei dividendi e della loro crescita.
* Analisi della sostenibilità del dividendo tramite Free Cash Flow.
* Proiezioni future basate sul piano industriale ENAV 2025-2029.
* Analisi dei rischi rilevanti per il dividendo.
* Una tabella riassuntiva con i principali dati finanziari.
* Accesso al testo completo dell'analisi fornita.

## 🛠️ Tecnologie Utilizzate

* Python
* Streamlit (per l'interfaccia web)
* Pandas (per la manipolazione dei dati)
* Plotly (per i grafici interattivi)

## 📊 Fonti Dati

L'analisi e i dati presentati si basano principalmente su:
* File `Analisi_ENAV.md` (analisi qualitativa, dettagli dividendi, piano industriale).
* File `TIKR - ENAV - Financials (31.12.13 - 31.12.23) - Copia.pdf` (dati finanziari storici aggregati). *Nota: L'estrazione dati da PDF può contenere imprecisioni; fare riferimento ai report ufficiali ENAV per dati definitivi.*

## 🚀 Esecuzione

**Online (Consigliato):**
L'applicazione è pensata per essere deployata su Streamlit Community Cloud. Segui le istruzioni fornite separatamente per il deploy tramite GitHub.

**Locale:**
1.  Clona il repository: `git clone <URL_DEL_TUO_REPOSITORY>`
2.  Naviga nella cartella: `cd <NOME_CARTELLA_REPOSITORY>`
3.  Crea un ambiente virtuale (consigliato): `python -m venv venv`
4.  Attiva l'ambiente virtuale:
    * Windows: `.\venv\Scripts\activate`
    * macOS/Linux: `source venv/bin/activate`
5.  Installa le dipendenze: `pip install -r requirements.txt`
6.  Avvia l'app Streamlit: `streamlit run enav_app.py` (o il nome che hai dato al tuo file .py)

## ⚠️ Disclaimer

Le informazioni in questa applicazione sono solo a scopo informativo/educativo e non costituiscono consulenza finanziaria. Verifica sempre le informazioni sui documenti ufficiali della società e consulta un professionista prima di prendere decisioni di investimento.
