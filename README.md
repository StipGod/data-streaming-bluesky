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

### Configuracion Kinesis Data Streams

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

### Configuracion Grafana Datasource

Entrar en la maquina EC2 de Grafana e insertar el archivo de .aws credential en la siguiente ubicacion:  /usr/share/grafana/.aws/credentials


![grafana](/docs/grafana3.jpeg "grafana")

![grafana](/docs/grafana4.jpeg "grafana")


Despues de esto, añadir en la secion de datasource Athena, y configurarlo con los siguientes datos:

![grafana](/docs/grafana1.jpeg "grafana")

![grafana](/docs/grafana2.jpeg "grafana")

Ya se tiene el datasource agregado. Ahora crea un dashboard nuevo con este datasource.