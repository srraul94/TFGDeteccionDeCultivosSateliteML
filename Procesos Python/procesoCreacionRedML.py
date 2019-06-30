import sys
import os
from tensorflow.python.keras.preprocessing.image import ImageDataGenerator
from tensorflow.python.keras import optimizers
from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import Dropout, Flatten, Dense, Activation
from tensorflow.python.keras.layers import  Convolution2D, MaxPooling2D
from tensorflow.python.keras import backend as K
import shutil
K.clear_session()



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




def preparacionGeneradorImagenesEntrenamiento(alt,long,bsize,data_entrenamiento):
  entrenamiento_datagen = ImageDataGenerator(rescale=1. / 255, shear_range=0.2,zoom_range=0.2, horizontal_flip=True)
  
  entrenamiento_generador = entrenamiento_datagen.flow_from_directory(
    data_entrenamiento,
    target_size=(alt, long),
    batch_size=bsize,
    class_mode='categorical')
  
  return entrenamiento_generador



def preparacionGeneradorImagenesValidacion(alt,long,bsize,data_validacion):
  test_datagen = ImageDataGenerator(rescale=1. / 255, validation_split=0.2)
  
  validacion_generador = test_datagen.flow_from_directory(
    data_validacion,
    target_size=(alt, long),
    batch_size=bsize,
    class_mode='categorical',
    subset='validation')
  
  return validacion_generador


def procesoClasificacionParcelasML(parametros):
  
  print(parametros)  
  enFormatoZIP = eval(parametros['enFormatoZIP'])
  
  try:
    rutaDatosEntrenamiento = parametros['rutaDatosEntrenamiento']
    os.stat(rutaDatosEntrenamiento) 
    print("Ya existe el directorio, no es necesario descomprimir el archivo ZIP.")
  except:
    if (enFormatoZIP):
      
      #Ruta donde se encuentra los ficheros ZIP con los datos de entrenamiento y validación.
      rutaDatosEntrenamientoZIP = parametros['rutaDatosEntrenamientoZIP']
    
      #Ruta donde queremos que de descompriman los datos de entrenamiento y validación.
      rutaDatosEntrenamiento = parametros['rutaDatosEntrenamiento']
      
      if ".zip" not in rutaDatosEntrenamientoZIP and ".zip" not in rutaDatosValidacionZIP:  
        
        rutaDatosEntrenamientoZIP = rutaDatosEntrenamientoZIP+'.zip'
        
        print("------- Descompriminedo los Datos de Entrenamiento... -------")
        shutil.unpack_archive(rutaDatosEntrenamientoZIP)
        
      else:
        print("------- Descompriminedo los Datos de Entrenamiento... -------")
        shutil.unpack_archive(rutaDatosEntrenamientoZIP)
        
    else:
      rutaDatosEntrenamiento = parametros['rutaDatosEntrenamiento']
  
  
 
  print("------- Leyendo las carácteristicas de la Red... -------")

  #Parametros para la red.
  epochs = int(parametros['epochs'])
  print("El número de Epochs es: ",epochs)
  
  longitudImagen = int(parametros['longitudImagen'])
  print("La Longitud para las imágenes es: ",longitudImagen)
  
  alturaImagen = int(parametros['alturaImagen'])
  print("La Altura para las imágenes es: ",alturaImagen)

  batch_size = int(parametros['batch_size'])
  print("El número de Batch Sizee es: ",batch_size)
  
  pasos = int(parametros['pasos'])
  print("El número de Pasos es: ", pasos)
  
  validation_steps = int(parametros['validation_steps'])
  print("El número de Pasos de Validacion es: ",validation_steps)

  filtrosConv1 = int(parametros['filtrosConv1'])
  print("El numero del primer filtro de Convolución es: ",filtrosConv1)
  
  filtrosConv2 = int(parametros['filtrosConv2'])
  print("El numero del segundo filtro de Convolución es: ",filtrosConv2)

  tamano_filtro1 = eval(parametros['tamano_filtro1'])
  print("El numero del primer filtro de Convolución es: ",tamano_filtro1)

  tamano_filtro2 = eval(parametros['tamano_filtro2'])
  print("El tamaño del segundo filtro de Convolución es: ", tamano_filtro2)

  tamano_pool = eval(parametros['tamano_pool'])
  print("El tamaño del filtro de Pooling es: ",tamano_pool)

  clases = int(parametros['clases'])
  print("El número de clases es: ", clases)
  
  lr = float(parametros['lr'])
  print("El número de Learning Rate: ", lr)
  
  
  print("------- Creando los generadores... -------")
  generadorEntrenamiento = preparacionGeneradorImagenesEntrenamiento(alturaImagen,longitudImagen,batch_size,rutaDatosEntrenamiento)
  generadorValidacion = preparacionGeneradorImagenesValidacion(alturaImagen,longitudImagen,batch_size,rutaDatosEntrenamiento)
  
  print("------- Construyendo la red... -------")
  parcelasModel = Sequential()
  parcelasModel.add(Convolution2D(filtrosConv1, tamano_filtro1, padding ="same", input_shape=(longitudImagen, alturaImagen, 3), activation='relu'))
  parcelasModel.add(MaxPooling2D(pool_size=tamano_pool))

  parcelasModel.add(Convolution2D(filtrosConv2, tamano_filtro2, padding ="same"))
  parcelasModel.add(MaxPooling2D(pool_size=tamano_pool))

  parcelasModel.add(Flatten())
  parcelasModel.add(Dense(256, activation='relu'))
  parcelasModel.add(Dropout(0.5))
  parcelasModel.add(Dense(clases, activation='softmax'))

  print("------- Red construida -------")
  parcelasModel.summary()
  
  print("------- Compilando la red... -------")
  parcelasModel.compile(loss='categorical_crossentropy', optimizer=optimizers.Adam(lr=lr), metrics=['accuracy'])
  
  print("------- Entrenando la red... -------")
  parcelasModel.fit_generator(generadorEntrenamiento, steps_per_epoch=pasos, epochs=epochs, validation_data=generadorValidacion, validation_steps=validation_steps)


  rutaDatosModelo = parametros['rutaDatosModelo']
  if not os.path.exists(rutaDatosModelo):
    os.mkdir(rutaDatosModelo)
  

  print("------- Guardando el modelo y los pesos de la red... -------")
   
  nombreModelo = parametros['nombreModelo']
  nombrePesos = parametros['nombrePesos']
  parcelasModel.save(rutaDatosModelo +'/'+ nombreModelo+'.h5')
  parcelasModel.save_weights(rutaDatosModelo +'/'+ nombrePesos+'.h5')
  
  
  
  # --- COMPRIMIMOS LA CARPETA RESULTANTE ------
  
  print("------- Comprimiendo los ficheros... -------")
  nombreModeloZIP = parametros['nombreModeloZIP']
  
  shutil.make_archive(nombreModeloZIP, 'zip', rutaDatosModelo) #NombreDelZIP,formato,y directorio a comprimir
  
  
  print("------- Fin del preoceso de creación de la red --------")







#Programa principal donde usamos los métodos definidos.

if len(sys.argv) == 2: # Son 2 porque el primer parametros es el nombre del script py
        parametros = leerParametrosFichero(sys.argv[1])  #ruta del fichero de configuración
        procesoClasificacionParcelasML(parametros)
else:
        print ("Este programa necesita que indiques la ruta del fichero con los parametros de busqueda")
