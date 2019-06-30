# -*- coding: utf-8 -*-

from satsearch import Search
from satstac import Items
from osgeo import gdal
from matplotlib import pyplot as plt
import sys
import numpy as np
np.seterr(divide='ignore', invalid='ignore')
import glob
import utm
import rasterio
import os
import shutil
import pickle

from datetime import *
from rasterio.mask import mask

def calcularCaracteristicasBanda(directorio,fecha):
  
  in_dir = directorio+'/'+str(fecha)
  
  b4_file = glob.glob(in_dir + '/**B4.TIF') # red band
  
  #cargamos la banda como conjunto de datos para poder obtener sus propiedades.
  dataSetB4 = gdal.Open(b4_file[0],gdal.GA_ReadOnly)
 
  #Comprueba si se ha podido cargar la banda.
  if dataSetB4 is None:
    print("El archivo B4 es None")

  #Obtenemos la Rasterband de uno de los conjuntos de datos, por ejemplo dataSetB4
  banda = dataSetB4.GetRasterBand(1)

  #Consegumos el número de filas y columnas de la banda, que nos dará el tamaño de imagen.
  cols = dataSetB4.RasterXSize
  rows = dataSetB4.RasterYSize

  #usamos GetGeoTransform que nos da los datos de la banda.
  transform = dataSetB4.GetGeoTransform()

  xOrigin = transform[0] #proporciona el origen de coordenadas X
  yOrigin = transform[3] #proporciona el origen de coordenadas Y
  pixelWidth = transform[1] #proporciona el ancho de pixel
  pixelHeight = -transform[5] #proporciona el alto de pixel

  #Leemos la banda como un array desde el punto 0,0 y ponemos de tamaño el orignial de la banda.
  #Nos servirá para poder mostar el contenido de la celda [row][col]
  data = banda.ReadAsArray(0, 0, cols, rows)
  
  return xOrigin, yOrigin, data, pixelWidth, pixelHeight



def recortarGeometria (geoms,directorio,fecha):
  in_dir = directorio+'/'+str(fecha) #ruta completa con la fecha
  
  b4_file = glob.glob(in_dir + '/**B4.TIF') # red band
  b5_file = glob.glob(in_dir + '/**B5.TIF') # Near Infrared NIR band
  

  # carga la raster band, crea una mascara con el poligno y lo extrae.
  with rasterio.open(b4_file[0]) as src:
     out_image, out_transform = mask(src, geoms, crop=True, pad=False)
  out_meta = src.meta.copy()

  # establece los meta datos de la imagen resultado.
  out_meta.update({"driver": "GTiff",
     "height": out_image.shape[1],
     "width": out_image.shape[2],
     "transform": out_transform})

  #guarda la imagen resultado.
  with rasterio.open(in_dir +"/maskedb4.tif", "w", **out_meta) as dest:
      dest.write(out_image)
  
  with rasterio.open(b5_file[0]) as src:
      out_image, out_transform = mask(src, geoms, crop=True, pad=False)
  out_meta = src.meta.copy()

  out_meta.update({"driver": "GTiff",
      "height": out_image.shape[1],
      "width": out_image.shape[2],
      "transform": out_transform})

  with rasterio.open(in_dir +"/maskedb5.tif", "w", **out_meta) as dest:
      dest.write(out_image)



def calcularNDVI(directorio,fecha):
  
  in_dir = directorio+'/'+str(fecha) 
  
  #Abrimos las imagenes en forma de conjunto de datos.
  dataSetMaskedB4 = gdal.Open(in_dir +'/maskedb4.tif',gdal.GA_ReadOnly)
  dataSetMaskedB5 = gdal.Open(in_dir +'/maskedb5.tif',gdal.GA_ReadOnly)

  #obtenemos la raster band de la imagen (será 1 porque solo tinee una banda) y la leemos como array numpy de float 32
  RasterBandDataSetMaskedB4 = dataSetMaskedB4.GetRasterBand(1).ReadAsArray().astype(np.float32)
  RasterBandDataSetMaskedB5 = dataSetMaskedB5.GetRasterBand(1).ReadAsArray().astype(np.float32)

  #Ndvi es igual a  (banda RED - banda NIR) / (banda RED + banda NIR)
  ndvi = (RasterBandDataSetMaskedB5 - RasterBandDataSetMaskedB4)/(RasterBandDataSetMaskedB5 + RasterBandDataSetMaskedB4)
  return ndvi


def comprobadorPuntosGeometriaImagen(xOrigin,yOrigin,data,pixelWidth, pixelHeight, puntos,fecha):
  print("------- Comprobando la imagen", fecha, "... -------")
  print("El origen X es:",xOrigin)
  print("El origen y es:",yOrigin)
  print("Los puntos son:",puntos)
  print("Hay en total ",len(puntos)," puntos")

  
  for point in puntos:
      col = int((point[0] - xOrigin) / pixelWidth)
      row = int((yOrigin - point[1] ) / pixelHeight)
      
      try:
         val = data[row][col]
      except:
          print("Un punto esta fuera de la imagen :",point[0],",",point[1])
          return False 
  return True


def mostrarYGuardarImagen(directorioDescargas,ndvi,fecha,parcela,fIniSin,fFinSin,fIniSiem,fFinSiem,fIniCre,fFinCre):
  
  # Finalmente mostramos la imagen en la pantalla
  fig = plt.figure(figsize=(5, 5))
  fig.set_facecolor('white')
  plt.imshow(ndvi,'BrBG') #Podriamos usar otros filtros de color como:  #viridis #YlGn #BrBG

  plt.title('NDVI ' +str(fecha))
  plt.show()
    
  try: # comprueba si exista ya el directorio, sino lo crea.
    os.stat(directorioDescargas)
  except:
    os.mkdir(directorioDescargas)

 
  direDescargaParcela = directorioDescargas+'/'+parcela
  try: # comprueba si exista ya el directorio, sino lo crea.
    os.stat(direDescargaParcela)
  except:
    os.mkdir(direDescargaParcela)
              
  
  fechaReplace = fecha.replace(year=2013) #Convertimos la fecha para que todas esten el mismo año para compararse.
  
  
  if fechaReplace >= fIniSin.date() and fechaReplace <= fFinSin.date():
      direDescargaFase = direDescargaParcela+'/'+'sinSiembra'
      print(' sinSiembra',fecha)
  elif fechaReplace >= fIniSiem.date() and fechaReplace <= fFinSiem.date():
    direDescargaFase = direDescargaParcela+'/'+'Siembra'
    print(' Siembra',fecha)
  elif fechaReplace >= fIniCre.date() and fechaReplace <= fFinCre.date():
    direDescargaFase = direDescargaParcela+'/'+'Crecimiento' 
    print(' Crecimiento',fecha)
  else:
    print('No corresponde a la temporada de este cultivo')
  
  try: # comprueba si exista ya el directorio, sino lo crea.
    os.stat(direDescargaFase)
  except:
    os.mkdir(direDescargaFase)
  
  plt.imsave(direDescargaFase+'/'+str(fecha)+'NDVIcolor'+parcela+'.png',ndvi,cmap='BrBG')
  return direDescargaParcela #devuelve la ruta donde estan todas las imagenes categorizadas



def leerParametrosFichero(ruta):
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



def obtenerGeometriaParcela(rutaFicheroGeometria):
  poligono = []
  diccionarioPuntos = leerParametrosFichero(rutaFicheroGeometria) #obtenemos el diccionario con los puntos
  
  for punto in diccionarioPuntos.keys(): #recorremos todas las claves del diccionario
     poligono.append(eval(diccionarioPuntos[punto]))  # y las insertamos en la lista 
  
  geometria  = [{'type': 'Polygon', 'coordinates':[poligono]}] #con la lista podemos crear la geometria.
  return geometria



def procesoCalculoNDVITratamientoImagenes(parametros):
  
  print(parametros)
  #Introducimos el perdiodo de siembra del cultivo
  formatoFecha = "%d-%m-%Y"

  #Inicio del periodo donde no debe haber siembra.
  fechaInicioSinSiembra = parametros['fechaInicioSinSiembra'] 
  dateFechaInicioSinSiembra = datetime.strptime(fechaInicioSinSiembra, formatoFecha)
  #Convertimos al año 2013 por ejemplo, para que podamos comparar ya que solo nos interesan los dias y meses para las cosechas.
  dateFechaInicioSinSiembra = dateFechaInicioSinSiembra.replace(year=2013)
  
  #Fin del periodo donde no debe haber siembra.
  fechaFinSinSiembra = parametros['fechaFinSinSiembra']
  dateFechaFinSinSiembra = datetime.strptime(fechaFinSinSiembra, formatoFecha)
  dateFechaFinSinSiembra = dateFechaFinSinSiembra.replace(year=2013) 
  
  #Inicio del periodo donde comienza la siembra.
  fechaInicioSiembra = parametros['fechaInicioSiembra']
  dateFechaInicioSiembra = datetime.strptime(fechaInicioSiembra, formatoFecha)
  dateFechaInicioSiembra = dateFechaInicioSiembra.replace(year=2013)
  
  #Fin del periodo de siembra.
  fechaFinSiembra = parametros['fechaFinSiembra']
  dateFechaFinSiembra = datetime.strptime(fechaFinSiembra, formatoFecha)
  dateFechaFinSiembra = dateFechaFinSiembra.replace(year=2013)
  
  #Inicio del periodo donde comienza el crecimiento.
  fechaInicioCrecimiento = parametros['fechaInicioCrecimiento']
  dateFechaInicioCrecimiento = datetime.strptime(fechaInicioCrecimiento, formatoFecha)
  dateFechaInicioCrecimiento = dateFechaInicioCrecimiento.replace(year=2013)
  
  #Fin del periodo de crecimiento
  fechaFinCrecimiento = parametros['fechaFinCrecimiento']
  dateFechaFinCrecimiento = datetime.strptime(fechaFinCrecimiento, formatoFecha)
  dateFechaFinCrecimiento = dateFechaFinCrecimiento.replace(year=2013)
  
  
  #Indicamos la ruta donde estan las imagenes descargadas
  rutaImagenesDescargadas = parametros['rutaImagenesDescargadas']
  
  #Indicamos la ruta donde esta el fichero binario con las fechas de las imagenes descargadas
  rutaFechasImagenesDescargadas = parametros['rutaFechasImagenesDescargadas']
  
  #Obtenemos la lista de fechas disponibles en la ruta de imagenes descargadas
  with open(rutaFechasImagenesDescargadas, 'rb') as ficheroFechas:
    listaFechasDescargadas = pickle.load(ficheroFechas)
  ficheroFechas.close
  
  #Obtenemos la geometria de la parcela
  rutaFicheroGeometria = parametros['rutaFicheroGeometria']
  geometria = obtenerGeometriaParcela(rutaFicheroGeometria) 

  
  #Obtenemos el nombre asignado a la parcela
  nombreParcela = parametros['nombreParcela']
  
  #Indicamos el nombre del directorio donde queremos que se guarden las imageness tratadas
  rutaGuardarImagenesTratadas = parametros['rutaGuardarImagenesTratadas']
  
  #Esta fecha se indica porque el fichero imagen esta corrupto. (en otras zonas quizas no sea necesaria)
  fechaProblematica = date(2018, 12, 29)
  
   
  #Recorremos todas las fechas que tenemos descargadas anteriormente
  for fecha in listaFechasDescargadas:
    if fecha == fechaProblematica :
        print("------- La imagen",fecha, "no es valida para procesarla ARCHIVO DAÑADO ------")
    else:
      dateFecha = fecha.replace(year=2013) 
      if dateFecha >= dateFechaInicioSinSiembra.date() and dateFecha < dateFechaFinCrecimiento.date():
        oriX,oriY,data, pixelWidth, pixelHeight = calcularCaracteristicasBanda(rutaImagenesDescargadas,fecha)
        valida = comprobadorPuntosGeometriaImagen(oriX,oriY,data,pixelWidth, pixelHeight,geometria[0]['coordinates'][0],fecha)
    
        if valida:
          print("------- La imagen" ,fecha, "es valida para procesarla -------")
          print("------- Procesando la imagen" ,fecha, " ... -------")
          recortarGeometria(geometria,rutaImagenesDescargadas,fecha)
          NDVI = calcularNDVI(rutaImagenesDescargadas,fecha)
          rutaImagenesProcesada = mostrarYGuardarImagen(rutaGuardarImagenesTratadas,NDVI,fecha,nombreParcela,dateFechaInicioSinSiembra,
                                                        dateFechaFinSinSiembra,dateFechaInicioSiembra,dateFechaFinSiembra,
                                                        dateFechaInicioCrecimiento,dateFechaFinCrecimiento)
          
        else:
          print("------- La imagen",fecha, "no es valida para procesarla ------")
       
      else:
        print("------- La fecha",fecha, "no es valida para esta cultivo. ------")

  
  
  print("------- Comprimiendo las imágenes resultado... --------")  
  
  
  output_filename = 'ImagenesProcesadas' + nombreParcela
  shutil.make_archive(output_filename, 'zip', rutaImagenesProcesada) #Comprimimos la carpeta resultante con las imagenes.

    
  print("------- Fin del proceso de Calculo de NDVI y Tratamiento de Imágenes --------")




#Programa principal donde usamos los métodos definidos.

if len(sys.argv) == 2: # Son 2 porque el primer parametros es el nombre del script py
        parametros = leerParametrosFichero(sys.argv[1])  #ruta del fichero de configuración
        procesoCalculoNDVITratamientoImagenes(parametros)
else:
        print ("Este programa necesita que indiques la ruta del fichero con los parametros de busqueda")
