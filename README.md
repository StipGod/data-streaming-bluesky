# Data Streaming Desde Bluesky

## Arquitectura general 
![architecture](/docs/architecture.jpeg "architecture")


### Configuracion S3

Se necesita crear dos S3 con la siguiente configuración: 

![s3](/docs/s3-configuration1.jpeg "s3")
![s3](/docs/s3-configuration2.jpeg "s3")

El resto de la configuración está por defecto.  

Cuando se tenga creado el S3 se añadirá una carpeta llamada “Athena” para tener todos los resultados de las consultas que se hagan en Amazon Athena. 

![s3](/docs/s3-configuration3.jpeg "s3")

### Configuracion Kinesis Data Streams

Se necesitan 2 Data Stream, a estas se les deja con la configuración predeterminada 

![data-streams](/docs/data-streams.jpeg "data-streams")

### Configuracion Firehose

![firehose](/docs/firehose1.jpeg "firehose")
![firehose](/docs/firehose2.jpeg "firehose")
![firehose](/docs/firehose3.jpeg "firehose")

### Configuracion Lambda

Se necesita crear una función lambda, que la fuente de datos sea el Datastream (Bluesky).

![lambda](/docs/lambda1.jpeg "lambda")

En la función se ejecutará el siguiente código: 

```python
import boto3
import json
import base64
import re

# Cliente de Firehose
firehose_client = boto3.client('firehose')

def lambda_handler(event, context):
    # Nombre del stream de Firehose al que se enviarán los datos
    firehose_stream_name = "BlueskyCleanedData"  # Cambiar por el nombre de tu Firehose

    # Lista para los registros procesados
    records_to_send = []

    for record in event['Records']:
        # Decodificar los datos de Kinesis (los datos vienen en Base64)
        payload = record['kinesis']['data']
        decoded_data = base64.b64decode(payload).decode('utf-8')
        
        # Limpiar los datos: Eliminar "null" inicial y separar objetos JSON
        cleaned_data = re.sub(r'^null', '', decoded_data)  # Quitar "null" inicial si existe
        separated_jsons = re.findall(r'\{.*?\}', cleaned_data)  # Extraer objetos JSON

        # Agregar cada JSON procesado como un registro para enviar a Firehose
        for json_obj in separated_jsons:
            records_to_send.append({
                'Data': json_obj + '\n'  # Los datos deben terminar con una nueva línea
            })

    # Enviar los datos procesados a Firehose
    if records_to_send:
        response = firehose_client.put_record_batch(
            DeliveryStreamName=firehose_stream_name,
            Records=records_to_send
        )
        
        # Registrar el resultado en los logs
        print(f'Successfully sent {len(records_to_send)} records to Firehose.')
        print(f'Response: {response}')
    else:
        print("No valid records to send.")

    return {
        'statusCode': 200,
        'body': f'{len(records_to_send)} records processed and sent to Firehose'
    }
```
### Configuracion Glue

Se necesita crear un crawler con el nombre CatalogBlueskyCleaned 

![glue](/docs/glue1.jpeg "glue")

IMPORTANTE: excluir la carpeta Athena 

![glue](/docs/glue2.jpeg "glue")

Para la seguridad se usa el LabRole 

Se crea una db  
El resto de las configuraciones se quedan en el valor predeterminado 

![glue](/docs/glue3.jpeg "glue")

Asi se veria nuestro athena

![athena](/docs/athena.jpeg "athena")


### Configuracion procesador de datos flink

Correr la aplicación de java en una maquina EC2

Crear una nueva maquina de ubuntu 24.04, importante que sea al menos large
![flink](/docs/flink1.png)

Y agregarle el profile de LabInstanceProfile en Advanced Details
![flink](/docs/flink2.png)


Ahora dentro de la maquina podemos clonar el repositorio para correr el codigo
```
git clone https://github.com/StipGod/data-streaming-bluesky
```

Antes de correr el codigo es necesario instalar java17.
```
sudo apt update
```
```
sudo apt install openjdk-17-jdk
```
Ahora con esto instalado podemos proceder a correr el código

**Nota:**
Si se va a reproducir desde cero es necesario tener creados dos datastreams, uno de input y otro de output y hacer unas modificaciones de código:
```
nano data-streaming-bluesky/sentiment-analysis/src/main/java/com/example/SentimentAnalysis.java
```
Y cambiar en las lineas 41 y 51 los arn de los streams por los propios creados:
![ec2](/docs/flink3.png)

Una vez hecho esto podemos correr el código:
```
cd data-streaming-bluesky/sentiment-analysis/
```
```
./gradlew run
```
### Configuración ingessta de datos

En la misma maquina desde la raiz vamos a movernos al proyecto de python:
```
cd ~/data-streaming-bluesky/src
```
Instalamos pip
```
sudo apt install python3-pip
```
Instalamos para crear un ambiente virtual de python
```
apt install python3.12-venv
```
Lo creamos e iniciamos
```
python3 -m venv env 
```
```
source env/bin/activate
```

E instalamos las librerias de python
```
pip install -r requirements.txt
```
Ahora tenemos que escribir un .env donde vamos a especficar el nombre de nuestro nuestro stream y la region:
```
nano .env
```

```
REGION=YourRegion
STREAMNAME=NameOfYourStream
```

Y finalmente podemos correr el programa:
```
python producer.py
```
### Configurar envio de los datos procesados a Athena

Con el paso anterior ya tenemos todas las librerias instaladas, nos quedaria solo modificar el codigo stream-to-athena.py:
![sta](image-1.png)
Debemos cambiar estos parametros por los propios y finalmente correr el programa
```
python stream-to-athena.py
```



### Configuracion Grafana 

Instalación de Grafana en EC2 (Ubuntu)

Requisitos previos

	1.	Grupo de Seguridad:
	•	Permitir tráfico en:
	•	Puerto 22: SSH.
	•	Puerto 3000: Acceso a Grafana.
	2.	Conexión a la instancia:

```bash
ssh -i <tu-clave.pem> ubuntu@<tu-ip-pública>
```

Comandos clave

	1.	Actualizar sistema:

```bash
sudo apt update && sudo apt upgrade -y
```


	2.	Instalar Grafana:

```bash
sudo apt install -y software-properties-common
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install -y grafana
```


	3.	Iniciar Grafana:

```bash
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

	4.	Configurar firewall (si está activo):

```bash
sudo ufw allow 3000
sudo ufw allow OpenSSH
sudo ufw enable
```

Acceso

	1.	Abre en tu navegador:

http://<tu-ip-pública>:3000


	2.	Credenciales iniciales:
	•	Usuario: admin
	•	Contraseña: admin (te pedirá cambiarla).

Comandos de administración

	•	Ver estado del servicio:

sudo systemctl status grafana-server


	•	Reiniciar Grafana:

sudo systemctl restart grafana-server

## proceso de visualizacion de datos

Para el proceso de visualizar datos vamos a crear una base de datos:

  	• El objetivo es traer la data procesada del bucket s3 creado anteriormente en nuestra nueva db para despues visualizar la data en grafana

![image](https://github.com/user-attachments/assets/634ad8e7-152d-4af3-8365-3a840b3368d7)


El siguiente paso es crear un crawler que nos arrastre la información del bucket s3 (con la data procesada) a la base de datos anteriormente creada

	 • Se asigna un tiempo de ejecución cada 5 minutos (minimo permitido por AWS glue crawlers) para que lleve la data a la bd

![image](https://github.com/user-attachments/assets/5d08f2bf-6127-4c42-bdc0-383ab8d948b5)

![image](https://github.com/user-attachments/assets/aea41aa2-f03d-44f5-90f8-6cbc56b5396a)


Una vez el crawler es ejecutado se puede visualizar la data llevada a la base de datos

![image](https://github.com/user-attachments/assets/12288f87-a8d0-478e-8f82-ae08c384a8f5)


### Configuracion Grafana Datasource

Entrar en la maquina EC2 de Grafana e insertar el archivo de .aws credential en la siguiente ubicacion:  /usr/share/grafana/.aws/credentials


![grafana](/docs/grafana3.jpeg "grafana")

![grafana](/docs/grafana4.jpeg "grafana")


Despues de esto, añadir en la secion de datasource Athena, y configurarlo con los siguientes datos:

![grafana](/docs/grafana1.png "grafana")

![grafana](/docs/grafana2.png "grafana")

Ya se tiene el datasource agregado. Ahora crea un dashboard nuevo con este datasource.
