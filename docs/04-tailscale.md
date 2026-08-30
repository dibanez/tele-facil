# Acceso remoto con Tailscale

Sin Nabu Casa no hay acceso remoto incluido, y el sistema vive en casa ajena.
Tailscale crea una red privada entre tus dispositivos **sin abrir un solo
puerto en el router**. El plan Personal es gratuito (hasta 100 dispositivos).

**Instálalo antes de irte de la casa destino.** Si el sistema falla y no tienes
acceso, la alternativa es conducir hasta allí.

---

## ⚠️ Antes de nada: el conflicto de subredes

Tu casa usa `192.168.1.0/24`. Los routers domésticos españoles usan casi
siempre ese mismo rango, así que **es muy probable que la casa destino use el
mismo**.

Si ambas redes son `192.168.1.0/24`:

| Qué quieres hacer | ¿Funciona? |
|---|---|
| Abrir Home Assistant en remoto | **Sí**, siempre. Se accede por la IP de Tailscale, no por la local |
| Llegar al decodificador o al router de la casa destino | **No.** Las rutas chocan |

Para administrar Home Assistant, con lo primero basta. Pero si quieres poder
diagnosticar el deco en remoto (por ejemplo ejecutar `probe_digi.py` contra la
red de allí), **cambia la subred de la casa destino a algo distinto**, por
ejemplo `192.168.20.0/24`, en el router.

Hacerlo estando allí cuesta cinco minutos. Hacerlo después es imposible en
remoto: te desconectarías a ti mismo.

---

## Instalación

### 1. Crea la cuenta

Regístrate en [tailscale.com](https://tailscale.com) (Google, Microsoft o
GitHub sirven). Instala también Tailscale en tu móvil o portátil, que será
desde donde te conectes.

### 2. Instala el add-on

En Home Assistant: **Ajustes → Complementos → Tienda de complementos**, busca
**Tailscale** e instala.

Es un *Community Add-on*, no del repositorio oficial. Suele aparecer en la
tienda por defecto; si no lo ves, añade el repositorio desde el menú **⋮ →
Repositorios**:

```
https://github.com/hassio-addons/repository
```

### 3. Activa Watchdog y arranque automático

En la pestaña **Información** del add-on, activa:

- **Iniciar al arrancar**
- **Watchdog** — reinicia el add-on si se cae

Sin estos dos, un reinicio de la Raspberry te deja sin acceso remoto.

### 4. Inicia y autentica

Pulsa **Iniciar** y espera unos segundos. Luego pulsa **Abrir interfaz web**
(no busques el enlace en los logs). Se abrirá el inicio de sesión de Tailscale:
confirma que quieres conectar este dispositivo.

Cuando veas el mensaje de sesión iniciada, el dispositivo aparecerá en tu
[consola de administración](https://login.tailscale.com/admin/machines).

### 5. 🔴 Desactiva la caducidad de la clave

**Este es el paso que la gente olvida y el que te va a doler.**

Por defecto la clave del dispositivo caduca a los 180 días. El día que caduque,
Home Assistant desaparece de tu red privada y **solo se puede reautenticar
estando físicamente delante**.

En la consola: **Machines → los tres puntos (…) junto a tu Home Assistant →
Disable key expiry**.

Hazlo ahora, no "luego".

### 6. Comprueba el acceso

En la consola verás una IP tipo `100.x.y.z`. Desde tu móvil con Tailscale
activo (y con los **datos móviles**, no el WiFi de la casa, para probarlo de
verdad):

```
http://100.x.y.z:8123
```

Si carga Home Assistant, ya tienes acceso remoto.

---

## Opciones útiles del add-on

Se editan en la pestaña **Configuración** del add-on.

| Opción | Por defecto | Cuándo tocarla |
|---|---|---|
| `userspace_networking` | `true` | Ponla a **`false`** si quieres actuar como subnet router (ver abajo) |
| `advertise_routes` | `local_subnets` | Ya anuncia la red local automáticamente |
| `accept_routes` | `true` | Déjala |
| `share_homeassistant` | `disabled` | Ver más abajo |

### Llegar al resto de la red remota (subnet router)

Solo si has resuelto el conflicto de subredes. Pon `userspace_networking:
false` y reinicia el add-on.

Después, **aprueba las rutas en la consola**: *Machines → tu Home Assistant →
Edit route settings → activa la subred*. Sin este paso las rutas se anuncian
pero no se usan, y es el fallo más común.

Con esto podrás llegar al decodificador y al router de la casa destino como si
estuvieras allí.

### "Pending approval to run as exit node"

Sale siempre, porque el add-on trae `advertise_exit_node: true` por defecto.

**No bloquea nada.** Un *exit node* sirve para que otros dispositivos saquen su
tráfico de internet por esa casa; no tiene relación con acceder a Home
Assistant en remoto.

Desactívalo para quitar el aviso: **Configuración → `advertise_exit_node:
false` → Guardar → Reiniciar** el add-on. Una Raspberry Pi 3 sería un exit node
muy lento de todos modos (Ethernet de 100 Mbps compartida con el bus USB).

> No confundas este aviso con el de **rutas de subred**. El de exit node se
> ignora; el de rutas (`192.168.x.0/24`) **sí hay que aprobarlo** si quieres
> llegar al decodificador en remoto.

### MagicDNS

En la consola, **DNS → MagicDNS** te permite usar un nombre en vez de la IP:

```
http://homeassistant:8123
```

Más cómodo de recordar y no cambia nunca.

### Tailscale Serve (opcional)

`share_homeassistant: serve` da acceso por HTTPS con nombre bonito
(`https://homeassistant.tured.ts.net`), pero exige añadir `use_x_forwarded_for`
y `trusted_proxies` a la configuración de Home Assistant.

**No lo necesitas.** El acceso por IP y puerto 8123 funciona igual de bien.

> **Nunca actives Funnel** (`share_homeassistant: funnel`). Expone tu Home
> Assistant a Internet abierto, que es justo lo que Tailscale evita.

---

## Comprobación final antes de irte

- [ ] El add-on arranca solo y tiene Watchdog activado
- [ ] La caducidad de clave está desactivada en la consola
- [ ] Has abierto HA desde **datos móviles**, no desde el WiFi de la casa
- [ ] Has anotado la IP `100.x.y.z` o el nombre MagicDNS
- [ ] Si vas a necesitar el subnet router, la subred de la casa destino ya no
      es `192.168.1.0/24`
