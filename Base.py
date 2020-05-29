###CODED BY OSCAR SALGADO ORTIZ - OSCSALGA AT CISCO.COM###

from netmiko import ConnectHandler
import datetime
import time
import re
import subprocess
import smtplib
import os
import sys

class Drops:
    nameOfFile = "ShowTechBajaPortLimit"
    emails = ['']
    hostname = ""
    sa = ""
    outputDrops = ""
    entryDrops = ""
    fragment = ""
    cgn = ""
    lc = ""
    nat = ""
    vrf = ""
    textoCorreo = ""
    tituloCorreo = ""
    tiempoLimiteUNA = 30 
    tiempoLimiteAMBAS = 5
    now = datetime.datetime.now()
    horaActual = now.hour
    horaActualParaBulk = 21
    fecha = time.strftime("%d/%m/%Y")
    directorio = os.path.dirname(os.path.realpath(__file__)) + "/"


    def __init__(self, ip):
        try:
            self.net_connect = ConnectHandler(device_type='cisco_xr', ip=ip,
                                          username='', password="")
            self.ip = ip
        except Exception as e:
            self.fileError("ERROR_LOGS", ip, self.fecha, str(e))
            sys.exit()

    def variables(self, hostname, sa, outputDrops, entryDrops, fragment, cgn, lc, nat, vrf):
        self.hostname = hostname
        self.sa = sa
        self.outputDrops = outputDrops
        self.entryDrops = entryDrops
        self.fragment = fragment
        self.cgn = cgn
        self.lc = lc
        self.nat = nat
        self.vrf = vrf

    def findHostname(self):
        hostname = self.net_connect.find_prompt()
        time.sleep(5)
        hostname = hostname.split(':', 1)[-1].strip()
        hostname = hostname.replace("#", "")
        return hostname


    def createDirectory(self, directorio):
        try:
            os.makedirs(self.directorio + directorio, exist_ok=True)
        except Exception as e:
            print(str(e))

    def cleanFiles(self):
        try:
            cantidad = self.ejecutarComando("dir harddisk: | in {} | u wc -l".format(self.nameOfFile))
            cantidad = cantidad.splitlines()
            cantidad = self.findNumber(cantidad)
            print("Number of files: " + str(cantidad))

            if cantidad > 1:
                print("Cleaning")
                comando = self.ejecutarComando("dir harddisk: | in {} | u cut  list 57-".format(self.nameOfFile))
                comando = comando.splitlines()
                print(comando)
                ultimo = comando[-1]
                self.ejecutarComandoDelay("delete /noprompt harddisk:{}*".format(self.nameOfFile))
                self.ejecutarComando("run > /harddisk:/{}".format(ultimo))

        except Exception as e:
            print(str(e))

    def findNumber(self, list):
        for x in list:
            try:
                return int(x)
            except ValueError:
                pass


    def findCGNandLC(self, command):
        comando = self.ejecutarComando(command)
        comando = comando.splitlines()
        del comando[0:2]

        return comando[0].strip()

    def correo(self, personas):
        SUBJECT = self.tituloCorreo + self.hostname
        TEXT = self.textoCorreo + "\n    SA: {}\n    total output drops: {}\n    " \
                                  "No translation entry drops: {}\n    " \
                                  "Fragment out to in drops: {}\n    " \
                                  "CGN: {}\n    " \
                                  "LineCard: {}\n    " \
                                  "NAT44: {}\n    " \
                                  "VRF: {}".format(self.sa, self.outputDrops, self.entryDrops, self.fragment, self.cgn,
                                                   self.lc, self.nat, self.vrf)

       
        gmail_sender = ''
        gmail_passwd = ''

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_sender, gmail_passwd)
        try:

            for p in personas:
                receiver = p
                BODY = '\r'.join(['To: %s' % receiver,
                                  'From: %s' % gmail_sender,
                                  'Subject: %s' % SUBJECT,
                                  '', TEXT])
                server.sendmail(gmail_sender, [receiver], BODY)
                print('email sent')
        except:
            print('error sending mail')
        server.quit()

    def fileError(self, archivo, ip, fecha, mensaje):
        try:
            with open(self.directorio + str(archivo).replace('#', '').replace(" ", "") + ".txt", "a") as f:
                f.write("IP: {} FECHA: {} ERROR: {}\n".format(ip, fecha, mensaje))
        except Exception as e:
            print(str(e))
            pass

    def file(self, archivo, command, output):
        try:
            self.createDirectory(os.path.split(str(archivo))[0])
            with open(self.directorio + str(archivo).replace('#', '') + ".txt", "a") as f:
                f.write("IP: {}\nCOMMAND: {}\nOUTPUT: {}\n".format(self.ip, command, output))
        except Exception as e:
            print(str(e))
            pass

    def find_between_r(self, s, first, last):
        try:
            start = s.rindex(first) + len(first)
            end = s.rindex(last, start)
            return s[start:end]
        except ValueError:
            return ""

    def snmpWalk(self, ip, community, interface):
        getVersion = subprocess.Popen(
            "snmpwalk -v1 -c {} {} 1.3.6.1.4.1.9.9.276.1.1.1.1.11.{}".format(community, ip, interface), shell=True,
            stdout=subprocess.PIPE).stdout
        contadores = getVersion.read()

        contadores = (self.find_between_r(contadores.decode(), "32:", "")).strip()
        return contadores

    def valores(self, command, left, right):
        try:
            comando = self.ejecutarComando(command)
            valor1 = self.find_between_r(comando, left, right)
            valor1 = abs(int(valor1))

            time.sleep(5)
            comando = self.ejecutarComando(command)
            valor2 = self.find_between_r(comando, left, right)
            valor2 = abs(int(valor2))

            total = self.diferencia(valor2, valor1) 
            return [valor2, valor1, total]
        except:
            pass

    def ejecutarComando(self, command):
        try:
            comando = self.net_connect.send_command(command, delay_factor=2)
            return comando
        except Exception as e:
            self.fileError("ERROR_LOGS_COMANDO", self.ip, self.fecha, str(e))
            print(str(e))
            pass

    def ejecutarComandoDelay(self, command):
        try:
            comando = self.net_connect.send_command_timing(command)
            self.net_connect.send_command_timing("\n")
            return comando
        except Exception as e:
            self.fileError("ERROR_LOGS_COMANDO_DELAY", self.ip, self.fecha, str(e))
            print(str(e))
            pass

    def ejecutarComandoConfig(self, command):
        try:
            comando = self.net_connect.send_config_set(command)
            return comando
        except Exception as e:
            self.fileError("ERROR_LOGS_COMANDO_CONFIG", self.ip, self.fecha, str(e))
            print(str(e))
            pass

    def diferencia(self, x, y):
        try:
            total = int(x) - int(y)
            total = abs(total)

            return total
        except Exception as e:
            pass

    def restaDeTiempo(self):
        time1 = self.dateOfLastFile()
        time1 = datetime.datetime.strptime(time1, '%Y-%m-%d %H:%M:%S.%f')
        time2 = datetime.datetime.now()
        totalTime = time2 - time1
        datetime.timedelta(0, 8, 562000)
        minutos = divmod(totalTime.days * 86400 + totalTime.seconds, 60)[0]
        segundos = divmod(totalTime.days * 86400 + totalTime.seconds, 60)[1]
        return minutos, segundos

    def dropAmbos(self, x, y):
        restaDeTiempo = self.restaDeTiempo()
        minutos = restaDeTiempo[0]
        segundos = restaDeTiempo[1]

        if minutos == 0 and segundos == 0 or minutos < 0:
            tiempo = datetime.datetime.now()
            tiempo = str(tiempo).replace(" ", "")
            print("CREANDO ARCHIVO POR QUE NO HAY NADA")
            command = "run > /harddisk:/{}2020-01-0100:00:01.000000.txt".format(self.nameOfFile)
            self.ejecutarComando(command)
            restaDeTiempo = self.restaDeTiempo()
            minutos = restaDeTiempo[0]
            segundos = restaDeTiempo[1]

        print("Minutos: {} Segundos: {} Since last E-Mail".format(minutos, segundos))
        if (x > 20000 and x < 499000) and (y > 20000 and y < 499000):
            self.tituloCorreo = "[AMBAS] Baja de trafico en: "
            self.textoCorreo = "INCREMENTO DE DROPS EN AMBAS INTERFACES "
            if minutos > self.tiempoLimiteAMBAS: 
                print("AMBAS")
                self.correo(self.emails)
                self.showTech()

        elif x >= 350000 and y >= 350000:
                if minutos >= self.tiempoLimiteAMBAS:
                    self.tituloCorreo = "[AMBAS+BULK] Baja de trafico en: "
                    self.textoCorreo = "INCREMENTO DE DROPS EN AMBAS INTERFACES "
                    self.correo(self.emails)
                    self.showTech()
                    self.bulkPortAlloc(self.cgn, self.nat, self.vrf)

        

    def bulkPortAlloc(self, cgn, nat, vrf):
        poner = self.ejecutarComandoConfig(
            ["service cgn " + cgn, "service-type nat44 " + nat, "inside-vrf " + vrf, "bulk-port-alloc size 1024",
             "commit"])

        time.sleep(10)
        quitar = self.ejecutarComandoConfig(
            ["service cgn " + cgn, "service-type nat44 " + nat, "inside-vrf " + vrf, "no bulk-port-alloc size 1024",
             "commit"])
        self.tituloCorreo = "[BULKPORT] Config made: "
        self.textoCorreo = "Se ha configurado el bulk: \n" + str(poner) + "\n" + str(quitar)
        self.correo(self.emails)

    def dateOfLastFile(self):
        command = "dir harddisk: | in {} | utility tail -n 1".format(self.nameOfFile)
        comando = self.ejecutarComando(command)
        s1 = comando
        s2 = self.nameOfFile
        try:
            resultado = self.insert_char(s1[s1.index(s2):], len(s2) + 10).replace(".txt", "")
        except:
            resultado = datetime.datetime.now()

        return str(resultado)

    def insert_char(self, string, index):
        resultado = string[:index] + ' ' + string[index:]
        resultado = resultado.replace(self.nameOfFile, "")
        return resultado

    def showTech(self):
        tiempo = datetime.datetime.now()
        tiempo = str(tiempo).replace(" ", "")
        command = "run > /harddisk:/{}{}.txt".format(self.nameOfFile, tiempo)
        self.ejecutarComando(command)
        self.cleanFiles()

    def serviceApp(self, ifIndex):
        command = "show snmp int | in ServiceApp | in ifIndex : {}".format(ifIndex)
        serviceApp = self.ejecutarComando(command)
        serviceApp = serviceApp.splitlines()
        del serviceApp[0:2]
        serviceApp = self.find_between_r(serviceApp[0], "ifName : ", "ifIndex :").strip()
        return serviceApp

    def desconectar(self):
        self.net_connect.disconnect()

