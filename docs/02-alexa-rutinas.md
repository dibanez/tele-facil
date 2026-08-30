# Rutinas de Alexa: de "enciende TV Telecinco" a "pon Telecinco"

Tras la Fase 6 ya funciona *"Alexa, enciende TV Telecinco"*. Eso no le sirve a
una persona mayor. Las **rutinas** traducen frases naturales a esas acciones.

## Cómo se crea una rutina

App de Alexa → **Más → Rutinas → +**

1. **Cuando ocurra esto** → *Voz* → escribe la frase exacta.
2. **Añadir acción** → *Casa inteligente* → *Controlar dispositivo* → elige el
   dispositivo "TV ..." → **Encender**.
3. Guarda.

Una rutina = una frase. Para admitir varias formas de decir lo mismo hay que
crear varias rutinas apuntando a la misma acción. Es tedioso, pero se hace una
sola vez.

---

## ⚠️ Frases que NO debes usar

Esto es lo más importante de este documento.

| Frase | Por qué falla |
|---|---|
| "Alexa, sube el volumen" | Es un **comando nativo**: sube el volumen del Echo, no de la tele. La rutina nunca se dispara |
| "Alexa, baja el volumen" | Igual que la anterior |
| "Alexa, silencio" | Silencia al propio Echo |
| "Alexa, vuelve atrás" | Alexa lo interpreta como control de reproducción |
| "Alexa, para" | Nativo |

Los comandos nativos de Alexa **siempre ganan** a las rutinas. Por eso todas
las frases de volumen y navegación llevan "la tele" o "la televisión".

---

## Tabla de rutinas a crear

### Canales

| Frase | Dispositivo | Acción |
|---|---|---|
| "pon la uno" | TV La Uno | Encender |
| "pon la primera" | TV La Uno | Encender |
| "pon la dos" | TV La Dos | Encender |
| "pon antena tres" | TV Antena Tres | Encender |
| "pon cuatro" | TV Cuatro | Encender |
| "pon telecinco" | TV Telecinco | Encender |
| "pon la cinco" | TV Telecinco | Encender |
| "pon la sexta" | TV La Sexta | Encender |

Añade, para los canales que más use, variantes con el verbo alternativo:

| Frase | Dispositivo |
|---|---|
| "quiero ver telecinco" | TV Telecinco |
| "cambia a antena tres" | TV Antena Tres |

> Escribe las frases **como se pronuncian**: "antena tres", no "antena 3";
> "la uno", no "la 1". Alexa transcribe voz, no lee cifras.

### Volumen (obligatorio desambiguar)

| Frase | Dispositivo |
|---|---|
| "sube la tele" | TV Subir Volumen |
| "sube el volumen de la tele" | TV Subir Volumen |
| "más alto la tele" | TV Subir Volumen |
| "baja la tele" | TV Bajar Volumen |
| "baja el volumen de la tele" | TV Bajar Volumen |
| "más bajo la tele" | TV Bajar Volumen |
| "silencia la tele" | TV Silencio |
| "quita el sonido de la tele" | TV Silencio |

### Navegación

| Frase | Dispositivo |
|---|---|
| "canal siguiente" | TV Canal Siguiente |
| "siguiente canal" | TV Canal Siguiente |
| "cambia de canal" | TV Canal Siguiente |
| "canal anterior" | TV Canal Anterior |
| "anterior canal" | TV Canal Anterior |
| "atrás en la tele" | TV Atras |
| "abre la guía" | TV Guia |
| "pon la guía" | TV Guia |
| "menú de la tele" | TV Inicio |

Son unas 30 rutinas. Calcula 40 minutos.

---

## Recomendaciones de uso real

**Empieza con pocas.** Crea primero los 4 o 5 canales que la persona ve de
verdad, más volumen y canal siguiente. Añadir el resto es fácil; una lista de
30 frases que nadie recuerda no sirve de nada.

**Pregúntale cómo lo diría.** La frase correcta no es la que te parece lógica a
ti, es la que sale sola. Si dice "ponme el Telecinco", crea esa rutina — con
artículo incluido.

**Deja una chuleta.** Una hoja en letra grande, junto al sofá, con las frases
que funcionan. Sin ella, el sistema se usa dos días.

**No menciones nunca Home Assistant, la Raspberry ni los canales por número.**
Para quien lo usa, esto es "hablarle a la tele".

---

## Si una rutina no responde

1. ¿Funciona *"Alexa, enciende TV Telecinco"*? Si **no**, el problema está en
   HA o en el deco, no en la rutina → mira `03-mantenimiento.md`.
2. Si **sí** funciona, el problema es la frase: chocará con un comando nativo o
   Alexa la transcribe distinto. En la app, **Más → Actividad** puedes ver qué
   entendió exactamente. Ajusta la frase a eso.
