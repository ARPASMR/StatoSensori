#!bin/python
# coding=UTF8
# -----------------------------------------------------------------------------
# STATOSENSORI
# -----------------------------------------------------------------------------
# verifica della presenza dei dati nei vari punti del percorso di acquisizione
# i. nel database IRIS
# ii. nel REMWS
# iii. sul sito FTP (per i sensori CAE)
# le informazioni sulla presenza dei dati sono archiviati nella tabella errori_sensori
# il programma è pensato per funzionare in contunuo, eventualmente lanciato da
# un file shell dentro un container
# FASE 1
#inizializzazione
import os
import pandas as pd
from sqlalchemy import *
import datetime as dt
import json as js
import requests
from ftplib import FTP
# definizione funzione di ricerca nell'FTP della stazione idstazione nella directory
# la funzione richiede di conoscere la stazione e la directory dove cercare il dato
# ritorna il valore:
#  ora del pacchetto: ho trovato il dato e l'ultimo pacchetto è delle ore AAAA-MM-GG HH:MM:SS (che valore uso?
#                     numero di secondi da datainizio, se è negativo vuol dire che l'ultimo dato è precedente a datainizio)
#  -1: non ho trovato il dato
#  -2: la directory non esiste

def ricercaFTP(directory):
    #serve anche datainizio, le variabili d'ambiente, ecc.
    #occorre verificare quali siano le variabili lette dalla funzione nel main
    nfile=0
    elenco_file=[]
    try:
        elenco_file=ftp.nlst(directory)
    except:
       #print ("Nessuna directory")
        errore=-2
        nfile=0
    nfile=len(elenco_file)-1
    if (nfile>0):
        datafile=elenco_file[nfile].split("DATI")[1]
        anno=int(datafile[1:5])
        mese=int(datafile[5:7])
        giorno=int(datafile[7:9])
        ora=int(datafile[10:12])
        minuto=int(datafile[12:14])
        file_ora=dt.datetime(anno,mese,giorno,ora,minuto)
        #print("Ultimo dato della stazione",st,"alle ore",file_ora.strftime("%Y-%m-%d %H:%M"))
        delta=file_ora-datainizio
        if (delta.days<0):
            delta=datainizio-file_ora
            errore=-delta.seconds
        else:
            errore=delta.seconds
    else:
        #print ("Nessun dato per la stazione", st)
        errore=-1
    return errore

# inizializzazioni
datafine=dt.datetime.utcnow()+dt.timedelta(hours=1)
datainizio=datafine-dt.timedelta(hours=1)

#lettura credenziali da variabili ambiente

PGSQL_IP=os.environ['PGSQL_IP']
PGSQL_USER=os.environ['PGSQL_USER']
PGSQL_DBNAME=os.environ['PGSQL_DBNAME']
PGSQL_PASSWORD=os.environ['PGSQL_PASSWORD']
FTP_SERVER=os.environ['FTP_SERVER']
FTP_USER=os.environ['FTP_USER']
FTP_PASSWORD=os.environ['FTP_PASSWORD']
DEBUG=os.environ['DEBUG']
if (DEBUG):
    print("STATOSENSORI: DEBUG attivato")
# webservice remwsgwyd
url='http://10.10.0.15:9099'

# preparazione query
#selezione df_sensori
Query='Select *  from "dati_di_base"."anagraficasensori" where "anagraficasensori"."idrete" in (1,4) and "anagraficasensori"."datafine" is NULL;'
engine = create_engine('postgresql+pg8000://'+PGSQL_USER+':'+PGSQL_PASSWORD+'@'+PGSQL_IP+'/'+PGSQL_DBNAME)
#engine = create_engine('postgresql://'+PGSQL_USER+':'+PGSQL_PASSWORD+'@'+PGSQL_IP+'/'+PGSQL_DBNAME)
conn=engine.connect()
df_sensori=pd.read_sql(Query, conn)

#selezione df_dati
QueryJoin='Select "m_osservazioni_tr"."idsensore", "m_osservazioni_tr"."data_e_ora","m_osservazioni_tr"."misura" from "realtime"."m_osservazioni_tr" inner join "dati_di_base"."anagraficasensori" on ("m_osservazioni_tr"."idsensore"="anagraficasensori"."idsensore") where "anagraficasensori"."idrete" in (1,4) and "anagraficasensori"."datafine" is NULL and "m_osservazioni_tr"."data_e_ora" between \''+datainizio.strftime("%Y-%m-%d %H:%M")+'\' and \''+datafine.strftime("%Y-%m-%d %H:%M")+'\';'
engine = create_engine('postgresql+pg8000://'+PGSQL_USER+':'+PGSQL_PASSWORD+'@'+PGSQL_IP+'/'+PGSQL_DBNAME)
conn=engine.connect()
df_dati=pd.read_sql(QueryJoin, conn)

# main
manca=0
ce=0
nfile=0
errori=pd.DataFrame(columns=['idstazione','idsensore','codice','descrizione','data_e_ora'])
#cambio la tipologia della colonna descrizione in stringa
errori.descrizione.astype('str')
errori.data_e_ora.astype('datetime64[ns]')

# strutturo la richiesta
frame_dati={}
frame_dati["sensor_id"]=0
frame_dati["function_id"]=1
frame_dati["operator_id"]=4
frame_dati["granularity"]=1 # chiedo solo i 10 minuti
frame_dati["start"]=datainizio.strftime("%Y-%m-%d %H:%M")
frame_dati["finish"]=datafine.strftime("%Y-%m-%d %H:%M")

#prima del ciclo dovrei verificare che il remws gateway funzioni: altrimenti lo segnalo ed esco (sic?)

# ciclo sui sensori
N=-1
for id in df_sensori.idsensore:
    if (DEBUG):
        print ("Data di inizio",datainizio.strftime("%Y-%m-%d %H:%M"),"mancano ",manca, "e ci sono ", ce, "su ",manca+ce, "--->Errori gravi", errori[errori.codice==3].codice.count(),end="\r")
    operator_id=1 #resetto ad ogni giro per chiedere ill dato rilevato

    # se non ho dati nel dataframe del dB chiedo al REM
    if (df_dati[df_dati.idsensore==id][0:1].empty) :
        stazione=df_sensori[df_sensori.idsensore==id].idstazione.item()
        N+=1
        N=len(errori)
        errori.loc[N]=[stazione,id,1,'no IRIS',dt.datetime.now().strftime("%Y-%m-%d %H:%M")]
        frame_dati["sensor_id"]=id
        tipo=df_sensori[df_sensori.idsensore==id].nometipologia.item()
    # per pluviometri e nivometri l'operatore è la cumulata
        if(tipo=='PP' or tipo=='N'):
            operator_id=4

        richiesta={
        'header':{'id': 10},
        'data':{'sensors_list':[frame_dati]}
        }
        try:
            r=requests.post(url,data=js.dumps(richiesta))
        except:
            print("Errore: REMWS non raggiungibile", end="\r")
        if(js.loads(r.text)['data']['outcome']==0):
            #print ("dato per il sensore ",id, "di" ,tipo,"presente nel REM")
            ce+=1
        else:
            #print ("Attenzione: dato di ",tipo, "sensore ", id, "ASSENTE nel REM")

            manca+=1
            # devo cercarlo nell'FTP
            # qual è l stazione?
            st=df_sensori[df_sensori.idsensore==id].idstazione.item()
            rt=df_sensori[df_sensori.idsensore==id].idrete.item()
            errori.idstazione.loc[N]=st
            errori.descrizione.loc[N]=errori.descrizione.loc[N]+ "& no REMWS"
            errori.codice.loc[N]=2
            # connessione ftp

            if (rt == 4):
                #print("la stazione",st,"è nella rete CAE")
                directory="GPRS/SP"+str(st)+"/"+datainizio.strftime("%Y%m%d")
                directory_radio="Supervisore/SP"+str(st)+"/"+datainizio.strftime("%Y%m%d")
                ftp=FTP(host=FTP_SERVER,user=FTP_USER,passwd=FTP_PASSWORD)
                err=ricercaFTP(directory)
                if (err>0):
                    # ho trovato il pacchetto, tutto a posto
                    err_radio=0
                elif (err==-1):
                    # non ci sono dati in GPRS: prvo in Supervisore
                    errori.descrizione.loc[N]=errori.descrizione.loc[N]+ " & no GPRS"

                    # è necessario riconnettersi? credo di no
                    #ftp=FTP(host=FTP_SERVER,user=FTP_USER,passwd=FTP_PASSWORD)
                    err_radio=ricercaFTP(directory_radio)
                elif (err==-2):
                    # manca la cartella GPRS: errore medio
                    errori.descrizione.loc[N]=errori.descrizione.loc[N]+ " & no GPRS Folder"
                    err_radio=ricercaFTP(directory_radio)
                else:
                    #la cartella c'è ma il dato è antecedente a data inizio
                    datapacket=datainizio+dt.timedelta(seconds=err)
                    errori.descrizione.loc[N]=errori.descrizione.loc[N]+ " & GPRS "+datapacket.strftime("%H:%M")
                    errori.codice.loc[N]=1
                    #vado comunque a vedere la radio
                    err_radio=ricercaFTP(directory_radio)
                if (err_radio==-1):
                    #il dato non è neanche nella cartella radio
                    errori.descrizione.loc[N]=errori.descrizione.loc[N]+ " & no Radio"
                    errori.codice.loc[N]=3
                elif (err_radio==-2):
                    #non c'è la cartella: segnalo come grave errore
                    errori.descrizione.loc[N]=errori.descrizione.loc[N]+ " & no Radio Folder"
                    errori.codice.loc[N]=3
                elif (err_radio<0):
                    # è negativo ma non -1 e non -2
                    # la cartella c'è, ma l'ultimo dato è antecedente a data inizio, quindi segnalo anomalia
                    datapacket=datainizio+dt.timedelta(seconds=err_radio)
                    errori.descrizione.loc[N]=errori.descrizione.loc[N]+ " & Radio "+datapacket.strftime("%H:%M")
                    errori.codice.loc[N]=1
                else:
                    # tutto a posto, c'è almeno un pacchetto dopo datainizio
                    if(DEBUG):
                        print("===========___________===========_____________================____________",end="\b\r")
    else:

    #    print ("sensore ",id, "OK!")
        ce+=1
#print("..............+++++++++.............++++++++++++.............................++++++++......")
#print("Elaborazione terminata.")
print ("STATOSENSORI: Data di inizio",datainizio.strftime("%Y-%m-%d %H:%M"),"mancano ",manca, "e ci sono ", ce, "su ",manca+ce)
print ("STATOSENSORI: Errori gravi:", errori[errori.codice==3])
print("STATOSENSORI: Dati non presenti solo su IRIS ma disponibili su REMWS o in FTP:",errori[errori.codice==1].codice.count())
print("STATOSENSORI: Dati non presenti neanche nel REMWS ma disponibili su FTP:", errori[errori.codice==2].codice.count())
# scrittura nel db
statement='delete from realtime.errori_sensori'
engine.execute(statement)
for i in range(0,N):
    statement='INSERT into realtime.errori_sensori ("idstazione","idsensore","codice","descrizione","data_e_ora") VALUES ('+\
    str(errori.idstazione[i])+','+str(errori.idsensore[i])+','+str(errori.codice[i])+\
    ',\''+errori.descrizione[i]+'\',\''+errori.data_e_ora[i]+'\')'
    engine.execute(statement)
# fine esecuzione
