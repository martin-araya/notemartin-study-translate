# `oracle.md` — términos observados en la documentación de Oracle

**Material leído:** `oracle/resúmenes/INDICE.md`,
`oracle/resúmenes/04_Get_Started_resumen.md`,
`oracle/resúmenes/05_Generate_Vector_Embeddings_resumen.md`.

## Reglas generales observadas

- Es el **único directorio del alcance cuyo corpus ya está escrito en
  español**: la fuente (`resúmenes/*.md`) es una versión simplificada
  y conservativa del manual original de Oracle, generada por el
  pipeline interno del usuario. Por eso el detector de idioma los
  clasifica como `already_target`.
- **Oracle publica una guía de estilo explícita** para sus términos
  técnicos (en `INDICE.md:22`): «los términos whitelist que aparecen
  a lo largo del capítulo — `VECTOR`, `VECTOR_CHUNKS`,
  `VECTOR_EMBEDDING`, `VECTOR_DISTANCE`, `DBMS_VECTOR`,
  `DBMS_VECTOR_CHAIN`, `DBMS_DATA_MINING`, `ONNX`, `ONNXPipeline`,
  `HNSW`, `IVF`, `EUCLIDEAN`, `COSINE`, `DOT`, `MANHATTAN`, `HAMMING`,
  `JACCARD`, `RAG`, `top-K`, `k-NN`, `FETCH APPROX`, `FETCH EXACT` y
  muchos otros — se mantienen en inglés».
- **Clasificación de términos Oracle** según la guía de estilo:
  1. **Paquetes PL/SQL**: van en MAYÚSCULAS con guiones bajos
     (`DBMS_VECTOR`, `UTL_TO_TEXT`).
  2. **Funciones SQL**: también MAYÚSCULAS (`VECTOR_EMBEDDING`,
     `VECTOR_CHUNKS`).
  3. **Modelos y algoritmos**: nombre propio (`ONNX`,
     `HNSW`, `IVF`).
  4. **Métricas**: nombre propio (`COSINE`, `EUCLIDEAN`,
     `HAMMING`).
  5. **Técnica**: nombre propio o término técnico estándar
     (`RAG`).
- La prosa explicativa está en español **con anglicismos técnicos
  razonables**: «vectorizar», «chunkear», «embedding», «token», etc.
  Estos anglicismos están admitidos por el manual y deben mantenerse.

## Propuestas por entrada

### Paquetes PL/SQL

- `DBMS_VECTOR` — paquete principal de Oracle AI Vector Search.
  **Status:** `mantener`
- `DBMS_VECTOR_CHAIN` — paquete de operaciones avanzadas. **Status:**
  `mantener`
- `DBMS_DATA_MINING` — paquete histórico de data mining; convive
  con `DBMS_VECTOR` para importar modelos. **Status:** `mantener`
- `UTL_TO_TEXT`, `UTL_TO_SUMMARY` — utilidades de la cadena
  (`chainable utility functions`). **Status:** `mantener`

### Funciones SQL

- `VECTOR_CHUNKS` — divide texto en chunks según parámetros. **Status:** `mantener`
- `VECTOR_EMBEDDING` — vectoriza texto o imagen con un modelo ONNX
  local. **Status:** `mantener`
- `VECTOR_DISTANCE` — distancia entre dos vectores. **Status:**
  `mantener`

### Modelos y formatos

- `ONNX` — formato Open Neural Network Exchange. **Status:**
  `mantener`
- `ONNXPipeline` — clase Python para descargar y convertir modelos
  Hugging Face a ONNX. **Status:** `mantener`
- `FLOAT32` — tipo numérico del vector (32 bits). **Status:**
  `mantener`
- `BINARY` — tipo de vector empaquetado en bits. **Status:**
  `mantener`

### Índices vectoriales

- `HNSW` (Hierarchical Navigable Small World) — algoritmo de
  búsqueda aproximada por vecino más cercano. **Status:**
  `mantener`
- `IVF` (Inverted File) — algoritmo de búsqueda aproximada.
  **Status:** `mantener`
- `Hybrid Vector Index` — combina Oracle Text + búsqueda vectorial
  en el mismo índice. **Status:** `mantener`

### Métricas de distancia

- `EUCLIDEAN` (L2). **Status:** `mantener`
- `COSINE` (similitud coseno). **Status:** `mantener`
- `DOT` (producto escalar). **Status:** `mantener`
- `MANHATTAN` (L1). **Status:** `mantener`
- `HAMMING` (para vectores BINARY). **Status:** `mantener`
- `JACCARD` (similitud Jaccard para BINARY). **Status:** `mantener`

### Patrones de búsqueda

- `top-K` — patrón que devuelve los `K` vecinos más cercanos.
  **Status:** `mantener`
- `k-NN` — algoritmo subyacente (k-Nearest Neighbors). **Status:**
  `mantener`
- `FETCH APPROX` — orden SQL específico de Oracle. **Status:**
  `mantener`
- `FETCH EXACT` — búsqueda exacta. **Status:** `mantener`
- `RAG` (Retrieval-Augmented Generation) — patrón de generación
  aumentada. **Status:** `mantener`

### Tecnología del entorno

- `PDB` (Pluggable Database). **Status:** `mantener`
- `OCI Object Storage` — almacenamiento de objetos en Oracle Cloud.
  **Status:** `mantener`
- `OML4Py Client` (Oracle Machine Learning for Python). **Status:**
  `mantener`

### Anglicismos asentados en el corpus

| Anglicismo | Sustituto técnico | Sentido en el corpus |
|---|---|---|
| vectorizar | (sin sustituto natural) | acción de generar el vector a partir de un texto o imagen |
| chunkear | trocear | dividir texto en chunks según parámetros |
| embedding | representación vectorial | vector producido por un modelo |
| endpoint | punto de acceso | URL de un servicio (Cohere, OpenAI, Ollama) |
| pipeline | cadena (de pasos) | secuencia de operaciones |
| runtime | tiempo de ejecución / runtime | tanto el software como el momento |
| trade-offs | compromisos | opuesto a «garantías» |
| chunks | fragmentos | cada trozo de texto troceado |
| token | unidad léxica | salida del tokenizador o del modelo |

**Status:** `mantener` para todos. El manual los acepta y traducirlos
cambia la prosa sin ayuda.

## Espanglish técnico en la prosa

Hay varias frases en los resúmenes que **mezclan sintaxis inglesa y
española**, normalmente por calco sintáctico:

- *«end-to-end»* (figura «Figura 3-1 *Vector Clusters*»): **mantener**.
- *«paso a paso»*: correcto en español, mezclarlo con *«quick
  start»* produciría castellano forzado. Mantener ambos.
- *«el camino "dentro de la base de datos"»* y *«el camino "fuera de la
  base de datos"»*: **mantener** las comillas y la construcción.
- *«runtime ONNX embebido»*: **mantener**.
- *«trade-offs en términos de latencia»*: **mantener**.

## Lo que falta por leer

- `oracle/resúmenes/06_Store_Vector_Embeddings_resumen.md`,
  `07_Create_Vector_Indexes_resumen.md` — algoritmos de
  almacenamiento, TYPED y UNTYPED, `HNSW`/`IVF` con más detalle,
  `AUXILIARY`/`METADATA`.
- `08_Use_SQL_Functions_resumen.md`, `09_Query_Data_resumen.md` —
  operadores (`<->`, `<=>`, `L2_DISTANCE`, `COSINE_DISTANCE`,
  vectorización de filas).
- `10_LLM_APIs_and_RAG_resumen.md` — proveedores de LLM (Cohere,
  Google AI, Hugging Face, OpenAI, Vertex AI), credenciales,
  `UTL_TO_GENERATE_TEXT`.
- `13_Vector_Search_PLSQL_Packages_resumen.md` — APIs de PL/SQL:
  `DBMS_VECTOR_CHAIN.UTL_TO_*`, `CHUNK_TEXT`,
  `CREATE_PREFERENCE`, `CREATE_INDEX`.

Estos capítulos añadirán términos específicos sobre el modelo
(CLIP multi-modal, reranker, similitud) y nombres de operaciones
SQL que la guía lleva en mayúsculas.

## Cierra de la fuente

La guía de estilo de Oracle ya decidió por su cuenta. El glosario v3
de la beta **no necesita entrada para Oracle**: esos términos se
glosan a sí mismos y basta con marcar su `preservation_policy` en
una sola entrada global. Mantener `oracle.md` como referencia para
que el lector humano vea la lista, **no** como entrada del
glosario.