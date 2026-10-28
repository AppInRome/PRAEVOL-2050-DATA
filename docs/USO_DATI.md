# Politica dati PRAEVOL 2050

1. Ogni dataset deve dichiarare ente, URL, anno base, scenario, unità, periodo, livello territoriale, licenza, data di estrazione e SHA-256 dell'originale.
2. Esporre solo dataset con stato `available` nel manifest.
3. Non interpretare i valori arrotondati di sintesi come dati annui completi.
4. Per gli aggiornamenti pubblicare file statici versionati (SQLite/JSON compressi) e poi aggiornare il manifest: evitare GitHub Actions.
5. Nessun dato personale o chiave API nel repository pubblico.
6. Distinguere previsioni ISTAT, dati osservati di Roma Capitale, ed elaborazioni sperimentali.
7. L'APK Android e i sorgenti rimangono fuori da questo archivio.
