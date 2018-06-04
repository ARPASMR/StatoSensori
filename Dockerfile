FROM arpasmr/python_base
WORKDIR /usr/src/myapp
COPY StatoSensori.py launch.sh Config.sh ./
CMD ["./launch.sh"]

