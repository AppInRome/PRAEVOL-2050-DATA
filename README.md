# PRAEVOL 2050 — dati ufficiali

Repository **solo dati** per l'app Android PRAEVOL 2050. Codice Android, build APK e grafica sono gestiti separatamente. **Nessuna GitHub Action**.

## Dati disponibili (28 ottobre 2026)
- `manifest.json`: indice machine-readable e stato di disponibilità.
- `data/istat_italia_popolazione_sintesi.json`: 4 valori *arrotondati* ISTAT per Italia (2025, 2030, 2050, 2080), scenario mediano e base 1/1/2025.
- `data/istat_italia_popolazione_sintesi.csv`: stessi 4 valori per il controllo umano.

**IMPORTANTE:** NON è ancora il database nazionale annuale completo. La popolazione del 2025 è la base delle previsioni; i punti di anni futuri sono previsionali. I valori sono espressi in milioni arrotondati, non in singoli residenti. **Non interpolare** dati per gli anni intermedi come fossero osservazioni ISTAT.

Fonte ufficiale: https://www.istat.it/comunicato-stampa/previsioni-della-popolazione-residente-delle-famiglie-e-delle-forze-di-lavoro-base-1-1-2025/

## Prossimi archivi — non ancora importati
- ISTAT previsioni comunali/provinciali, 2025–2050, per sesso, età quinquennale, bilancio e indicatori: https://demo.istat.it/app/?i=PPC
- ISTAT previsioni regionali/nazionali 2025–2080: https://demo.istat.it/app/?i=PPR
- ISTAT famiglie per regione, 2025–2050: banca dati DEMO / IstatData.
- Roma Capitale: popolazione osservata al 31/12/2025 per Municipio, Zona Urbanistica e suddivisioni toponomastiche: https://www.comune.roma.it/web/it/informazione-di-servizio.page?contentId=IDS1579597

Per l'integrazione regionale/comunale serviranno prima file originali verificati, intestazioni, copertura, licenze e controlli di completezza. Roma Capitale NON pubblica previsioni ufficiali ISTAT per Municipio: non attribuire loro lo scenario ISTAT.

## Accesso da Android
Manifest: https://raw.githubusercontent.com/AppInRome/PRAEVOL-2050-DATA/main/manifest.json

App: leggere il manifest, verificare `status`, `complete_series` e precisione prima di visualizzare ciascun grafico. Se offline, usare il database locale validato. GitHub Raw è distribuzione di piccoli file, non una API statistica ufficiale con garanzia di servizio.

## Attribuzione
Fonte: ISTAT, Previsioni popolazione residente, famiglie e forze di lavoro — base 1° gennaio 2025. Riprodurre fonte, anno base, scenario, unità e arrotondamento nell'app.
