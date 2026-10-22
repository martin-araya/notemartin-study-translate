<!-- version: 1.0.0 -->

# Portabilidad del paquete (fase 147)

El paquete se declara portable. Eso no es lo mismo que haberlo probado en
varios sistemas. Esta fase separa las dos cosas:

- `verified`: la suite se ejecutó en ese sistema y el informe está guardado.
- `design_only`: el paquete está diseñado para ese sistema y **no se ha
  comprobado**. No significa que falle; significa que nadie lo ha visto
  funcionar.

Una fila nunca llega a `verified` sin un informe de ejecución. El mecanismo,
no el texto, decide el estado.

## 1. Herramientas

| Script | Qué hace |
|---|---|
| `scripts/probe_platform.py` | ejecuta las comprobaciones del entorno y escribe el informe |
| `scripts/check_portability.py` | combina la sonda local y los informes externos en la matriz |

```bash
python scripts/probe_platform.py --out reports/maintenance/platform_probe.json

python scripts/check_portability.py \
    --probe reports/maintenance/platform_probe.json \
    --external reports/maintenance/external/linux-cpython-3.12.json \
    --out reports/maintenance/portability_matrix.json
```

## 2. Qué sondea

| Comprobación | Por qué importa |
|---|---|
| `fcntl` con bloqueo real | el coordinador de la fase 114 usa `fcntl.flock` en POSIX y un `threading.Lock` como reserva |
| `os.replace` | la escritura atómica de informes y manifiestos depende de ella |
| sensibilidad a mayúsculas | dos rutas que solo difieren en mayúsculas colisionan en macOS y no en Linux |
| normalización Unicode | NFC y NFD son el mismo archivo en macOS y dos archivos en Linux |
| nombres con tildes, emoji y espacios | el corpus real los tiene |
| componentes de nombre largos | límites de 255 bytes por componente |
| `zoneinfo` | las marcas de tiempo del manifiesto son ISO-8601 en UTC |
| codificación yalgorithms de hash | `sha256` es la base de todas las huellas del proyecto |

La sonda no necesita red y borra lo que crea. Un fallo de limpieza se
comprueba con una prueba propia (`test_la_sonda_crea_y_borra_sus_ficheros`).

## 3. Matriz registrada

| Sistema | Estado | Evidencia |
|---|---|---|
| macOS sobre Darwin | `verified` | `reports/maintenance/platform_probe.json` (Python 3.9.6) |
| Linux con CPython | `verified` | `reports/maintenance/external/linux-cpython-3.12.json` (Python 3.12.15, `python:3.12-slim`) |
| Windows con CPython | `design_only` | ninguna: no hay máquina ni imagen disponible aquí |

La ejecución externa se hizo así, con el repositorio montado en el
contenedor y las dependencias de `requirements.txt`:

```bash
docker run --rm -e PYTHONDONTWRITEBYTECODE=1 -v "$PWD":/w -w /w \
  python:3.12-slim sh -c "python -m pip install -r requirements.txt && \
  python -m pytest tests/ -q --no-header -p no:cacheprovider"
```

## 4. Qué encontró esta fase

La primera ejecución en Linux falló **108 de 891 pruebas**. Ninguna era un
fallo de lógica de traducción; las cuatro causas eran reales:

| Causa | Qué era | Corrección |
|---|---|---|
| 78 pruebas fijaban `/var/folders/.../T/kilo`, una ruta de macOS | los directorios temporales estaban codificados a mano | `tests/conftest.py` crea un directorio con `tempfile.gettempdir()` y las pruebas lo usan |
| `langdetect` importado en `scripts/detect_language.py` sin declarar | dependencia no declarada: en un entorno limpio el clasificador no arrancaba | añadida y pineada en `requirements.txt` |
| `__pycache__` dentro del paquete | la suite escribía bytecode en `scripts/` y `tests/`, y `check_distribution.py` lo marca como artefacto prohibido | `sys.dont_write_bytecode = True` en `conftest.py` |
| `test_rechaza_colision_por_unicode` nunca comprobaba nada en macOS | el `skip` por normalización Unicode ocultaba que el test no creaba las dos variantes | el test crea NFC y NFD de verdad |

Y una quinta, más interesante: `validate.py` **no** comprobaba marcadores de
protección sobrantes en documentos que no tenían literales protegidos
(`if not expected: continue`). En Linux el orden de lectura del directorio
hizo que la prueba del marcador cayera en uno de esos documentos y fallara.
La comprobación se quitó del salto: un documento sin literales tampoco puede
dejar marcadores puestos.

Después de las correcciones: **885 pruebas pasan en Linux** y 886 en macOS,
con una única diferencia pendiente y explicada (la auditoría documental
mientras se cerraban las fases 148 y 149).

Esto es exactamente para lo que existe la fase: una afirmación de
portabilidad sin ejecución es una afirmación, no una evidencia.

## 5. Requisitos por sistema

| Sistema | Requisito | Nota |
|---|---|---|
| macOS | Python >= 3.9, `fcntl`, POSIX | sistema de referencia del desarrollo |
| Linux | Python >= 3.9, `fcntl`, POSIX | comprobado en 3.12 |
| Windows | Python >= 3.9 | `fcntl` no existe: el coordinador usa el `threading.Lock` de reserva (fase 114) |

## 6. Qué NO demuestra esta fase

- **No demuestra que Windows funcione.** Está en `design_only` y sigue así.
- **No demuestra que el corpus real se procese igual en ambos sistemas.** Se
  ejecutó la suite con sus fixtures, no el corpus de 4832 archivos.
- **No demuestra equivalencia semántica.** Una prueba pasa o no pasa; que
  pase en dos sistemas no dice nada sobre la calidad de la traducción.
- **No cubre otras versiones de Python.** Solo 3.9 y 3.12.
- **No sustituye una integración continua.** Ejecutar esto a mano el día que
  se rompe un supuesto es tarde. Es la base para un CI, no el CI.

## 7. Relación con otras fases

| Fase | Relación |
|---|---|
| 111 | `measure_execution.py` mide dentro de un sistema; esta compara entre sistemas |
| 114 | el bloqueo de archivo es el supuesto más dependiente de la plataforma |
| 147 | entregable de esta fase |
| 149 | la matriz entra en el candidato como evidencia del módulo `maintenance` |