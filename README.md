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

# Esecuzione nel container
```
docker run -it --rm -v "$PWD":/usr/src/myapp -w /usr/src/myapp arpasmr/python_base python StatoSensori.py

```
# Branch
**master**
**env**

Il branch _env_ ha le variabili di accesso al dB e al FTP definite da apposite variabili di ambiente: è quindi utilizzabile come microservizio nel container passando le variabili corrette, al posto di averle scritte nel file _Config.py_

Per usarlo con arpasmr/python_base si può usare la sintassi
```
docker run -it --rm -e "PGSQL_USER=<nome utente>" -e "PGSQL_PASSWORD=<password utente>" -e "PGSQL_IP=<IP database>" -e "PGSQL_DBNAME=<nome database>" -e "FTP_USER=<utente ftp>" -e "FTP_PASSWORD=<password ftp>" -e "FTP_SERVER=<server ftp (es. arpalombardia>" -v "$PWD":/usr/src/myapp -w /usr/src/myapp arpasmr/python_base python StatoSensori.py

```
