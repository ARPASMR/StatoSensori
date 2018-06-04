#!/bin/bash
# launcher per l'esecuzione in continuo dello script python
# (pensato per essere lanciato dall'interno del container)
# parte che contiene le variabili di ambiente
source Config.sh
# lancio di python
while [ 1 ]
do 
      python StatoSensori.py
      sleep 3300
done
