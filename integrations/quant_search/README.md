# Piloto local de optimización

El piloto ejecuta Optuna 4.9.0 y el calculador cuantitativo de JAIME sobre una serie sintética de desarrollo. Está preparado para Windows x64 y CPython 3.14. En el entorno principal del backend se utiliza este comando.

```powershell
.\.venv\Scripts\python.exe scripts/probe_quant_search.py
```

Una segunda ejecución consulta el resultado guardado y verifica su traza. Para repetir el cálculo con el protocolo original y comprobar la igualdad del resultado se utiliza `--replay`. El resumen indica intentos, parámetros únicos, poda y cálculos recuperados durante la auditoría. La medición de tiempo y memoria se conserva por ejecución, fuera del identificador determinista.

El protocolo fija una familia de medias móviles, los costes, las semillas, los cuatro tramos, la poda y el presupuesto de 192 propuestas. El registro de diseño se publica antes de ejecutar el trabajador. El log conserva el registro y cierre de cada intento. Una interrupción deja su log privado y la siguiente ejecución puede empezar un intento completo bajo el mismo protocolo. Un cierre verificado publica el resultado de forma atómica. Solo se admite un trabajador de este piloto. El proceso recibe los parámetros del protocolo local y dispone de un límite de 120 segundos.

La vista para el autor de hipótesis se puede consultar con el siguiente comando. Obtiene del expediente verificado la estructura de las reglas ya evaluadas y el periodo observado.

```powershell
.\.venv\Scripts\python.exe scripts/validate_strategies.py --show 5b3f92b437746935f3a4d58991c84962e5f1f2dd7f774083659b66fbe5a35421 --format proposer
```

## Instalación reproducible del entorno opcional

El entorno ya instalado está en `.tools/quant-search`. Para recrearlo en otra copia del proyecto, desde la raíz se ejecutan estos dos comandos una vez.

```powershell
.\.tools\Scripts\uv.exe --cache-dir .tools/quant-search-cache venv --python .venv/Scripts/python.exe .tools/quant-search
.\.tools\Scripts\uv.exe --cache-dir .tools/quant-search-cache pip install --require-hashes --only-binary :all: --python .tools/quant-search/Scripts/python.exe --default-index https://pypi.org/simple -r integrations/quant_search/requirements-win-py314.lock
```

El lock fija las ruedas y sus dependencias. El piloto verifica las versiones instaladas al arrancar. La red se utiliza para la instalación inicial. El cálculo y la auditoría se ejecutan localmente. El backend conserva su entorno de dependencias. [Evaluación de herramientas y resultados](../../docs/actual/MINERIA_REPOS_2026_11_20.md) · [Protocolo del piloto](pilot_protocol.json).
