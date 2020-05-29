###CODED BY OSCAR SALGADO ORTIZ - OSCSALGA AT CISCO.COM###

import Base as db
import datetime
import random
import sys
import time
import os

#global equipo

device1 = {
    "ip": "" 
}
all_devices = [device1] 

for a_device in all_devices:

    for i in range(6):
        try:
            esperar = random.randint(200, 400)
            print("ESPERANDO: " + str(esperar))
            time.sleep(esperar)
            conexion = db.Drops(a_device['ip'])
        except:
            continue 
        else:
            break
    else:
        sys.exit(1)

    serviceapps = conexion.ejecutarComando("show ipv4 int brief | in ServiceApp | u cut -d ' ' -f1")
    serviceapps = serviceapps.split()[5:]
    contador = len(serviceapps)

    conexion.cleanFiles()
    hostname = conexion.findHostname()

    for sa in serviceapps:
        cgn = conexion.ejecutarComando("show run formal interface {} | in service | u cut -d ' ' -f5".format(sa))
        cgn = cgn.split()[5:]
        NAT44 = conexion.ejecutarComando(
            "show run formal service cgn {} | in service-type | u head -n1 | u cut -d ' ' -f6".format(
                ''.join(cgn)))
        NAT44 = NAT44.split()[5:]
        NAT44 = ''.join(NAT44)

        print(hostname)
        print(sa)
        CGN = conexion.ejecutarComando('show run int {} | i "service cgn" |  u cut -d " " -f4'.format(sa)).split()[5:]

        for cgn in CGN:
            print(cgn)
            lc = conexion.ejecutarComando(
                "show run service cgn {} | in service-location preferred-active | u cut  -d ' ' -f4".format(cgn)).split()[5:]
            lc = ''.join(lc)
            
            vrf = conexion.ejecutarComando("show run service cgn {} | i inside-vrf | u head -n1 |  u cut  -d ' ' -f4".format(cgn)).split()[5:]
            vrf = ''.join(vrf)
            

            EntryDrops = conexion.valores("show cgn nat44 {} statistics  | in No translation entry drops"
                                          .format(NAT44), ": ", "")
            OutputDrops = conexion.valores("show int {} | in total output drops".format(sa),
                                           "bytes, ",
                                           "total output drops") 
            fragment = conexion.valores("show cgn nat44 {} inside-vrf all counters | in Fragment out to in drops"
                                        .format(NAT44), ": ", "") 

            conexion.variables(hostname, sa, OutputDrops[2], EntryDrops[2], fragment[2], cgn, lc,
                               NAT44,
                               vrf)

            conexion.dropAmbos(int(EntryDrops[2]), int(OutputDrops[2]))
           

            print("Fecha: " + str(datetime.datetime.now()))
            print("VRF: " + vrf)
            print("ServiceApp Restantes: {}".format(contador - 1))
            print("ServiceApp: {}".format(sa))
            print("CGN: {}".format(cgn))
            print("LineCard: {}".format(lc))
            print("NAT44: {}".format(NAT44))
            print("NoEntryTranslationsDrops: Valor1: {} Valor2: {} Total: {}".format(EntryDrops[0],
                                                                                     EntryDrops[1], EntryDrops[2]))
            print("TotalOutputDrops: Valor1 {} Valor2: {} Total: {}".format(OutputDrops[0],
                                                                            OutputDrops[1], OutputDrops[2]))
            print("Fragment: Valor1: {} Valor2: {} Total: {}".format(fragment[0], fragment[1], fragment[2]))
            print("*" * 100)
        contador = contador - 1

    conexion.desconectar()
