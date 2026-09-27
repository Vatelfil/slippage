# Conexión entre ABIDES-Gym (Docker Local) y Google Colab (Entrenamiento)

Dado que el simulador ABIDES-Gym corre localmente en Docker, pero el entrenamiento del modelo se realizará en Google Colab para aprovechar sus recursos (ej. GPUs), necesitamos establecer una comunicación en red bidireccional entre el contenedor local y el entorno de Google Colab.

Debido a que Google Colab es un entorno en la nube y el Docker local está detrás de un firewall/NAT (tu red local), la mejor estrategia es utilizar un túnel inverso o exponer una API.

## Arquitectura de Conexión Recomendada: WebSocket + Ngrok

Los entornos tipo "Gym" se basan en llamadas secuenciales (`env.step()`, `env.reset()`). Para ejecutar esto remotamente:
1. **Local (Docker)**: Envolveremos el entorno ABIDES-Gym en un servidor WebSocket (por ejemplo, usando `FastAPI`).
2. **Túnel (Ngrok / Cloudflare)**: Expondremos el puerto de este servidor local a internet.
3. **Google Colab (Cliente)**: Implementaremos un entorno "Proxy" de Gym (`gym.Env`) que redirija las llamadas `step` y `reset` a la URL pública del túnel WebSocket.

---

## Paso 1: Configuración del Túnel (Local)

Debes ejecutar un túnel para exponer el contenedor Docker al exterior. Recomendamos **Ngrok**:

1. Descarga e instala Ngrok (https://ngrok.com/).
2. Autentícate y corre el comando para exponer el puerto donde corre tu entorno envuelto en API (suponiendo que sea el 8000):
   ```bash
   ngrok http 8000
   ```
   *Esto generará una URL pública como `https://xyz.ngrok-free.app`.*

## Paso 2: Ejecutar SSH en Colab (Alternativa de Conexión Directa)

Si en lugar de exponer el contenedor local a Colab, prefieres conectar tu entorno local a Colab como si fuera un servidor remoto (para sincronizar código o correr scripts remotos):

Puedes ejecutar el siguiente bloque en una celda de Colab para iniciar un servidor SSH mediante `colab-ssh`:

```python
!pip install colab_ssh --upgrade
from colab_ssh import launch_ssh_cloudflared, init_git_cloudflared
launch_ssh_cloudflared(password="tu_contraseña_segura")
```
Colab te devolverá un comando SSH. ¡Deberás compartir esa información para que podamos conectarnos desde la máquina local!

## Paso 3: Sincronización e Integración
Una vez que el túnel o el acceso SSH estén levantados, el Agente en Colab solicitará las observaciones (states) de ABIDES-Gym a través de la red, tomará las decisiones con el modelo, y enviará las acciones de vuelta.

