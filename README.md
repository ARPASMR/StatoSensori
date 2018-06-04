# StatoSensori
script per la verifica dello stato dei sensori per IRIS
Esegue una scansione della tabella dei dati in IRIS (realtime) e se non trova dati attesi verifica che siano presenti nel remws (tramite collegamento a **remwsgwyd**) e se non li trova verifica che siano nel sito FTP o nella cartella GPRS o in quella radio.

Restituisce alcune informazioni a video e una informazione più completa in un file.

A seconda della situazione che trova per ogni sensore codifica un errore di gravità crescente

# Requisiti
Python 3.x

File di configurazione delle credenziali _Config.sh_,
```
export PGSQL_USER=<pgsql user>
export PGSQL_PASSWORD=<pgsql password>
export PGSQL_IP=<pgsql ip host>
export PGSQL_DBNAME=<pgsql db name>
export FTP_USER=<ftp user>
export FTP_PASSWORD=<ftp password>
export FTP_SERVER=<ftp.server.address>

```

**NOTA**: Il file Config.sh va tenuto in gitignore

# Esecuzione nel container
```
docker run -it --rm -e "DEBUG=False" arpasmr/python_base ./launch.sh

```
la variabile di ambiente DEBUG controlla la prolissità dei messaggi. Con _False_ vengono minimizzate le scritture

# Risultato
Nella tabella _realtime.errori_sensori_ vengono memorizzati i valori dell'ultimo run dello script. Vengono mantenuti solo gli ultimi, i precedenti sono cancellati definitivamente.
