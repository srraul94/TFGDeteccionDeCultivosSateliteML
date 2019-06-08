# -*- coding: utf-8 -*-
#Importación de las librerias necesarias.
from satsearch import Search
from satstac import Items
import pickle
import sys


#Definicion de los métodos utilizados.

def buscarResultadosSatelite(minLon,minLat,maxLon,maxLat,minDate,maxDate,maxCloudCover,satellite):
  search = Search.search(bbox=[minLon,minLat,maxLon,maxLat],
               datetime=minDate+'/'+maxDate,
               property=["eo:cloud_cover<"+str(maxCloudCover)],
               collection=satellite)
  items = search.items()
  return items


def descargarResultadosSatelite(items,directorio):
  filenameB5 = items.download('B5', path=directorio+'/${date}')
  print(filenameB5)
  filenameB4 = items.download('B4', path=directorio+'/${date}')
  print(filenameB4)


def leerParametrosBusquedaDescargas(ruta):
  diccionarioParametros = {}
  
  # Abre archivo en modo lectura
  with open(ruta,'r') as archivo:
    # inicia bucle infinito para leer línea a línea.
    while True: 
      linea = archivo.readline()  # lee línea.
      if not linea: 
          break  # Si no hay más se rompe bucle.
      linea = linea.rstrip() #Quita caracteres vacios y \n a la derecha.
      
      key, value = linea.strip().split('=') #dividimos la linea mediante el signo = . izquierda la clave y derecha valor
      key = key.strip() #quitamos espacios en blancos de la parte izquierda
      key = key.strip("'") #quitamos comillas simples de la parte izquierda
      
      value = value.strip() # #quitamos espacios en blancos de la parte derecha
      value = value.strip("'") # quitamos comillas simples de la parte derecha
      
      diccionarioParametros[key] = value
  archivo.close  # Cierra archivo
  
  return diccionarioParametros


def procesoBusquedayDescarga(parameters):  
  minLon = float(parameters['minLon']) 
  minLat = float(parameters['minLat'])
  maxLon = float(parameters['maxLon'])
  maxLat = float(parameters['maxLat'])
  minDate = parameters['minDate']
  maxDate = parameters['maxDate']
  clouds = int(parameters['clouds'])
  satellite = parameters['satellite']
  rutaDescarga = parameters['rutaDescarga']
  
  print("------- Buscando resultados... --------")  
  myItems = buscarResultadosSatelite(minLon,minLat,maxLon,maxLat,minDate,maxDate,clouds,satellite)
  print(myItems.summary(['date', 'id', 'eo:cloud_cover']))

  print("------- Descargando los resultados... --------") 
  descargarResultadosSatelite(myItems, rutaDescarga)
  listaFechas = myItems.dates()

  print("------- Guardando el fichero con las fechas de los resultados... --------")  
  with open('FechasDescargadasSatelite.txt', 'wb') as archivo:# Abre archivo binario para escribir   
     pickle.dump(listaFechas, archivo) # Escribe la lista en el fichero creado en forma de datos. 
  archivo.close
  print("------- Fin del proceso de Busqueda y Descarga de Resultados --------")  





#Programa principal donde usamos los métodos definidos.

if len(sys.argv) == 2: # Son 2 porque el primer parametros es el nombre del script py
        print(sys.argv[1]) #ruta del fichero de configuración
        parametros = leerParametrosBusquedaDescargas(sys.argv[1])
        procesoBusquedayDescarga(parametros)
else:
        print ("Este programa necesita que indiques la ruta del fichero con los parametros de busqueda")
