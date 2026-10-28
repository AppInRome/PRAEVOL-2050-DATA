# PRAEVOL 2050 — Stato dell'importazione (28 ottobre 2026)

## Disponibile e verificato
- Sintesi nazionale ISTAT della popolazione residente, scenario mediano base 1 gennaio 2025: **2025 = 58,9 milioni; 2030 = 58,7 milioni; 2050 = 55,0 milioni; 2080 = 45,8 milioni**, valori arrotondati.
- Archivio dati `data/istat_italia_popolazione_sintesi.json` e CSV.
- `manifest.json` segnala espressamente i dataset ancora non importati.

## Non disponibile in questo archivio
- CSV/ZIP completi previsioni popolazione per Comune/Provincia 2025–2050
- CSV/ZIP previsioni regionali popolazione 2025–2080
- Previsioni famiglie per Regione 2025–2050
- Tavole anagrafiche per Municipio e Zona Urbanistica di Roma Capitale al 31/12/2025

L'accesso automatico da questo ambiente a demo.istat.it è fallito per blocco di rete (DNS). Questo documento non equivale ad una consegna del database nazionale completo.

## Fonti
- https://demo.istat.it/app/?i=PPC — comuni e province (Comuni pubblici: capoluoghi e >5.000 abitanti, non tutti i 7.896 comuni singoli)
- https://demo.istat.it/app/?i=PPR — previsioni regionali fino al 2080
- https://demo.istat.it/app/?i=PRF — previsioni regionali delle famiglie
- https://www.comune.roma.it/web/it/informazione-di-servizio.page?contentId=IDS1579597 — anagrafe Roma 2025
- https://www.istat.it/notizia/dati-per-sezioni-di-censimento/ — osservazioni subcomunali nazionali 2023

## Regola scientifica
Una previsione comunale ISTAT non è automaticamente una previsione per Municipio. Le eventuali proiezioni subcomunali PRAEVOL saranno elaborate con modello separato, calibrato alla previsione comunale, intervalli d'incertezza e validazione retrospettiva. Non inventare valori intermedi o dati mancanti.

## Infrastruttura
Il repository contiene **solo dati e documentazione**; codice Android e compilazioni restano offline nel progetto locale. Nessuna GitHub Action è necessaria.
