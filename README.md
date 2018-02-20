# StatoSensori
script per la verifica dello stato dei sensori per IRIS
Esegue una scansione della tabella dei dati in IRIS (realtime) e se non trova dati attesi verifica che siano presenti nel remws (tramite collegamento a **remwsgwyd**) e se non li trova verifica che siano nel sito FTP o nella cartella GPRS o in quella radio.

Restituisce alcune informazioni a video e una informazione più completa in un file.

A seconda della situazione che trova per ogni sensore codifica un errore di gravità crescente

# Requisiti
Python 3.x

File di configurazione delle credenziali _Config_, come dizionario
```
Config=dict(PGSQL_USER=<_utente_>,PGSQL_PASSWORD=<_password_>,PGSQL_IP=<indirizzo server>,PGSQL_DBNAME=<nome del db>,FTP_USER=<utente ftp>,FTP_PASSWORD=<password>,FTP_SERVER=<server ftp>)
```

**NOTA**: Il file Config.py va tenuto in gitignore
