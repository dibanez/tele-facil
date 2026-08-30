# Despliegue paso a paso

Cada fase se verifica antes de pasar a la siguiente. Si una falla, no sigas:
el problema se vuelve mucho más difícil de aislar más adelante.

---

## Fase 0 — Antes de ir a la casa destino

- [ ] Copia este repositorio en un pendrive o clónalo en la Raspberry.
- [ ] Lleva un teclado/ratón USB o el mando del deco: harán falta para
      emparejar y para leer los números de canal en pantalla.
- [ ] Anota el usuario y contraseña de Home Assistant.

---

## Fase 1 — Red

El sistema depende de que la Raspberry y el decodificador se vean entre sí.

1. Conecta ambos a la **misma red** (mismo SSID o cable, nunca la red de
   invitados).
2. En el router, crea **reservas DHCP por MAC** para la Raspberry y para el
   decodificador. Sin esto, el día que cambien de IP el sistema deja de
   funcionar y nadie sabrá por qué.
3. Comprueba que el router **no tiene aislamiento de clientes** (*AP isolation*
   / *client isolation*). Si lo tiene, desactívalo.

**Verificación:** desde la Raspberry, `ping <ip-del-deco>` responde.

---

## Fase 2 — ¿Qué vía de control admite el decodificador?

Enciende el decodificador (que se vea imagen, no en reposo) y ejecuta:

```bash
python3 tools/probe_deco.py
```

Interpreta la salida:

| Resultado | Significado | Acción |
|---|---|---|
| `remote v2 : YES` | El deco admite Android TV Remote | **Camino recomendado.** Sigue a la Fase 3 |
| `remote v2: no` / `adb tcp: YES` | Solo ADB disponible | Sigue a la Fase 3-bis |
| `cast alive: YES`, resto `no` | Está vivo pero sin control | Activa el servicio de mando (Fase 3) o ADB (Fase 3-bis) |
| No encuentra nada | No hay conectividad | Vuelve a la Fase 1 |

---

## Fase 3 — Emparejar por Android TV Remote (recomendado)

1. En HA: **Ajustes → Dispositivos y servicios → Añadir integración**.
2. Busca **Android TV Remote**. A menudo el deco ya aparece descubierto solo.
3. Introduce la IP del decodificador.
4. En el televisor aparecerá un **código de emparejamiento**. Escríbelo en HA.
5. Anota el `entity_id` que se crea (normalmente `remote.<nombre_del_deco>`).

> Si el `entity_id` **no** es `remote.digi_tv`, edita la línea
> `target_remote:` en `homeassistant/packages/tele_facil.yaml`. Es el único sitio
> donde aparece.

**Verificación:** la entidad `remote.*` aparece con estado `on` u `off`, nunca
`unavailable`.

### Fase 3-bis — Alternativa por ADB

Solo si la Fase 3 no fue posible.

En el R2A **el método clásico no funciona**: pulsar siete veces sobre "Número
de compilación" no activa nada. Hay que instalar una app de *Developer Tools*
desde Google Play y desde ella entrar en *System Settings → Developer options*,
activando **Depuración USB** y **Depuración por red**.

Después, en HA añade la integración **Android Debug Bridge** apuntando a
`<ip>:5555` y acepta el diálogo de autorización que sale en el televisor.

Luego edita `script.tv_send_key` y sustituye la llamada `remote.send_command`
por `androidtv.adb_command`. **Es el único cambio necesario**: todo lo demás
del paquete funciona igual.

> Aviso: la depuración por red se desactiva sola tras un reinicio en muchos
> Android TV. Si acabas en este camino, cuenta con que habrá que reactivarla
> tras cortes de luz o actualizaciones del deco.

---

## Fase 4 — Verificar las teclas

Copia `homeassistant/packages/tele_facil.yaml` a `<config>/packages/` y añade a
`configuration.yaml` la línea de `packages:` (ver `configuration.snippet.yaml`).
Reinicia Home Assistant.

En **Herramientas para desarrolladores → Acciones**, ejecuta
`script.tv_send_key` con cada tecla y anota cuál responde:

| Tecla | Efecto esperado | ¿Funciona? |
|---|---|---|
| `KEYCODE_CHANNEL_UP` | Sube un canal | |
| `KEYCODE_CHANNEL_DOWN` | Baja un canal | |
| `KEYCODE_VOLUME_UP` | Sube volumen | |
| `KEYCODE_VOLUME_DOWN` | Baja volumen | |
| `KEYCODE_MUTE` | Silencia | |
| `KEYCODE_BACK` | Vuelve atrás | |
| `KEYCODE_GUIDE` | Abre la guía | |
| `KEYCODE_HOME` | Pantalla de inicio | |
| `KEYCODE_5` | Salta al canal 5 | |

### Si el volumen no responde

Es el fallo más habitual y **no es culpa de la configuración**. En muchos
montajes el decodificador saca audio por HDMI a volumen fijo y quien manda es
el televisor. Comprueba:

1. ¿El botón de volumen del mando del deco cambia el volumen? Si tampoco, el
   deco no controla el volumen y ningún comando lo hará.
2. Si el mando sí funciona pero por HDMI-CEC, activa **CEC** en el televisor
   (Bravia Sync, Anynet+, Simplink, según marca).
3. Si nada de lo anterior, el volumen habrá que controlarlo por otra vía
   (integración del televisor si es smart, o un emisor de infrarrojos). Anótalo
   y sigue: el resto del sistema no depende de esto.

---

## Fase 5 — Averiguar la posición real de cada canal

**No des por buenas las posiciones del paquete.** Los canales no se piden por
su número de dial, sino por el lugar que ocupan en la rejilla de la app, y el
operador la reordena de vez en cuando.

Abre la rejilla en el deco (botón **Canales** del panel, o el enlace
`digitv://channel`) y cuenta desde la izquierda, empezando en 1:

| Canal | Posición real |
|---|---|
| La 1 | |
| La 2 | |
| Antena 3 | |
| Cuatro | |
| Telecinco | |
| laSexta | |

> Cuidado: la posición 1 suele ser la desconexión autonómica ("La 1 Galicia"),
> no la nacional. Y los nombres de programa **no** identifican el canal: cambian
> con la hora. Para saber qué canal estás viendo, pulsa `ARRIBA` durante la
> reproducción y lee la barra de información.

Edita el valor `posicion:` de cada script de canal en
`homeassistant/packages/tele_facil.yaml` con lo que hayas anotado.

**Verificación:** ejecutar `script.tv_telecinco` desde HA cambia a Telecinco
desde cualquier canal de partida.

---

## Fase 6 — Exponer a Alexa

1. Aplica el resto de `configuration.snippet.yaml`, ajustando `host_ip` y
   `advertise_ip` a la IP real de la Raspberry.
2. **Home Assistant pasará del puerto 80 al 8123.** A partir de aquí se accede
   por `http://<ip>:8123/`. Actualiza la app del móvil y los marcadores.
3. Reinicia Home Assistant.
4. Comprueba que el puente responde: `curl http://<ip>/description.xml` debe
   devolver un XML de Hue.
5. Di: **"Alexa, busca dispositivos"** (tarda ~45 s), o hazlo desde la app.
6. Deben aparecer los 14 dispositivos con prefijo "TV".

**Verificación:** *"Alexa, enciende TV Telecinco"* cambia de canal.

Continúa en `02-alexa-rutinas.md` para convertir esto en frases naturales.

---

## Fase 7 — Acceso remoto para dar soporte

Sin Nabu Casa no puedes entrar desde fuera, y el sistema vive en casa ajena.
Instala **Tailscale** (Community Add-on, gratuito).

Guía completa en **[04-tailscale.md](04-tailscale.md)**. Dos avisos que no
puedes saltarte:

- **Desactiva la caducidad de clave** en la consola de Tailscale. Si no, a los
  180 días pierdes el acceso y solo se recupera estando allí en persona.
- **Si la casa destino usa `192.168.1.0/24` igual que la tuya**, cámbiala ahora
  (por ejemplo a `192.168.20.0/24`). Con rangos iguales no podrás llegar al
  decodificador en remoto, y después ya no hay forma de arreglarlo a distancia.

Hazlo **antes de irte**. Es la diferencia entre arreglar un problema en cinco
minutos y tener que conducir hasta allí.
