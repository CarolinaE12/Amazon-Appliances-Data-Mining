# Exploración de Patrones de Falla en Electrodomésticos: Minería de Datos sobre Amazon 2023
## Descripción:
Este proyecto aplica técnicas de **Minería de Datos** y Procesamiento de Lenguaje Natural (NLP) sobre el dataset masivo de reseñas de Amazon (edición 2023) para la categoría de Appliances (Electrodomésticos).

El objetivo principal es identificar y clasificar las causas recurrentes de fallos técnicos reportados por los usuarios. A través del análisis de sentimientos y la extracción de palabras clave en reseñas con bajas calificaciones **(1 y 2 estrellas)**, el sistema busca detectar patrones de defectos de fabricación, problemas de materiales y fallas de funcionamiento.

## Características principales:
Análisis de Sentimiento Crítico: Filtrado de experiencias negativas para identificar puntos de dolor del usuario.

Clasificación de Fallos: Categorización automática de problemas (daño físico, fallas eléctricas, errores de sensores).

Procesamiento Eficiente: Implementación mediante Streaming y lectura de archivos JSONL.GZ para manejar grandes volúmenes de datos (6GB+) sin saturar la memoria local.

## Dataset

Este proyecto utiliza el dataset:

Amazon Reviews 2023

Disponible en:
https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023
https://amazon-reviews-2023.github.io/
Debido a su gran tamaño, el dataset no se incluye en este repositorio.
Debe descargarse manualmente y ubicarse en la carpeta:
data/

