# Diagnóstico: por qué Colab no le deja a Mauricio (29 sept)

## Qué subió (PR #13, `fix/arreglos-dependencias`, commit `5f1752f`)

Cambió `test_abides.py` para usar `gymnasium` en vez de `gym`, y agregó `gymnasium==0.29.1` + `shimmy==1.3.0` a `requirements.txt`, con la idea de que `shimmy` sirva de capa de compatibilidad para que ABIDES-Gym (hecho para `gym` viejo) funcione con `gymnasium`.

## Por qué esto no va a resolver el problema (y probablemente sea la causa del loop)

**ABIDES-Gym importa `gym` directamente en su propio código fuente** — no es algo que se pueda parchar cambiando nuestro script. Verificado en el archivo real del repo oficial (`abides_gym/__init__.py`, `markets_execution_environment_v0.py`): tienen `import gym` arriba de todo, registran los entornos con `gym.envs.registration.register(...)`, y `gym.spaces.Discrete`/`gym.spaces.Box` en el código interno.

`shimmy` envuelve un entorno **ya creado** con `gym` viejo para que **otro código externo** lo use con la API de `gymnasium`. No hace que el paquete `abides_gym` en sí deje de necesitar `gym` internamente. Si `gym==0.18.0` no está instalado, `import abides_gym` va a fallar de entrada, sin importar qué tenga nuestro `test_abides.py`.

**Además, esto no toca el otro problema real:** ABIDES-Gym también necesita `numpy==1.22.0` (Colab trae una versión mucho más nueva por defecto, probablemente 2.x), y ese desajuste rompe código interno de ABIDES que usa alias de NumPy que ya no existen (`np.float`, `np.int`, etc. — esto ya estaba anotado en `docs/diagnostico_dependencias.md` desde antes).

**Conclusión:** el cambio de Mauricio ataca sus síntomas (`gym` vs `gymnasium`) sin atacar la causa (versiones exactas: Python 3.9, `gym==0.18.0`, `numpy==1.22.0`). Por eso cada vez que arregla un import aparece otro — está resolviendo síntomas uno por uno en vez de fijar el entorno completo de una vez.

## Lo que de verdad hace falta: un Python 3.9 real dentro de Colab

El problema de fondo (que ya habíamos anticipado en `PENDIENTE_MAURICIO.md`) es que `apt-get install python3.9` + `update-alternatives` cambia qué `python3` corre desde la terminal, pero **no cambia el Python que ya está corriendo el kernel de la notebook**. Por eso "lo instalo y el import no lo encuentra": se instaló para un Python, y la celda corre en otro.

### La solución estándar para esto: `condacolab`

Es una herramienta hecha específicamente para forzar un entorno Conda real (con la versión de Python que uno quiera) como kernel de Colab, reiniciando el runtime para que quede así desde cero. **No lo he podido probar yo mismo** (sin acceso a Colab) — es la solución más conocida para este problema exacto, pero hay que verificarla en la práctica.

```python
# Celda 1 — instala condacolab y reinicia el runtime automáticamente
!pip install -q condacolab
import condacolab
condacolab.install()
# ADVERTENCIA: esta celda reinicia el kernel solo. Es normal que la
# ejecución "se corte" acá — hay que volver a correr desde la celda 2.
```

```python
# Celda 2 (después del reinicio automático) — crear el entorno con Python 3.9
!conda create -n abides python=3.9 -y
!conda run -n abides pip install pip==23.3.2 setuptools==57.5.0 wheel==0.38.4
!conda run -n abides pip install numpy==1.22.0 cython
!conda run -n abides pip install gym==0.18.0 pandas==1.2.4 scipy==1.10.0 coloredlogs==15.0.1 psutil==5.8.0 tqdm==4.61.1
!conda run -n abides pip install pomegranate==0.14.5
!conda run -n abides pip install "ray[rllib]==1.7.0"
```

```bash
# Celda 3 — clonar e instalar ABIDES-Gym DENTRO del entorno abides
!git clone https://github.com/jpmorganchase/abides-jpmc-public.git
%cd abides-jpmc-public/abides-core
!conda run -n abides python setup.py install
%cd ../abides-markets
!conda run -n abides python setup.py install
%cd ../abides-gym
!conda run -n abides python setup.py install
%cd ../..
```

```python
# Celda 4 — probar SIN depender de que el kernel de la notebook sea Python 3.9:
# se corre como script dentro del entorno correcto, no como import en la celda.
!conda run -n abides python src/envs/test_abides.py
```

**Por qué esto evita el problema del kernel:** `conda run -n abides` ejecuta el comando completo dentro del entorno de Python 3.9, sin necesitar que la notebook misma esté corriendo esa versión. El precio es que el training loop también tendría que correr así (`!conda run -n abides python train.py`), no como celdas sueltas con `import` directo — como script, no interactivo.

## Qué le diría a Mauricio ahora

1. Revertir `test_abides.py` a `import gym` (no `gymnasium`) — es lo correcto mientras se hable directo con ABIDES-Gym. Quitar `shimmy`, no soluciona nada acá.
2. Probar `condacolab` como arriba. Si en un intento (con límite de tiempo, no todo el día) no funciona, entrenar en su Docker local, que ya tiene el Python correcto.
3. No seguir agregando parches "un import a la vez" — el patrón que está siguiendo (arreglar un error, aparece el siguiente) es señal de que faltan 2-3 versiones fijadas a la vez (Python, gym, numpy), no un paquete suelto.
