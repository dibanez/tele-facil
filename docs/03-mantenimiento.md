# Mantenimiento y diagnóstico

## Diagnóstico rápido, de fuera hacia dentro

Sigue este orden; cada paso descarta una capa.

| # | Comprobación | Si falla |
|---|---|---|
| 1 | ¿Alexa responde a algo? | Echo sin corriente o sin WiFi |
| 2 | ¿*"Alexa, enciende TV Telecinco"* funciona? | Si no → paso 3. Si sí → el problema es la rutina |
| 3 | ¿Aparecen los dispositivos "TV" en la app de Alexa? | emulated_hue caído → paso 4 |
| 4 | ¿Abre `http://<ip>:8123/`? | Raspberry apagada o sin red |
| 5 | ¿La entidad `remote.*` está `unavailable`? | Deco apagado o cambió de IP |
| 6 | ¿`python3 tools/probe_digi.py` encuentra el deco? | Problema de red o el deco perdió el emparejamiento |

## Fallos habituales

### "Alexa ya no encuentra los dispositivos"

Casi siempre es la IP de la Raspberry. Comprueba que la reserva DHCP sigue en
pie y que `host_ip` / `advertise_ip` coinciden con la IP real.

Para forzar un redescubrimiento: *"Alexa, busca dispositivos"*. Si siguen sin
salir, **borra los dispositivos "TV" en la app de Alexa** y vuelve a buscar —
emulated_hue a veces necesita ese ciclo tras un cambio de red.

### "Cambia de canal pero al equivocado"

Los números de canal cambiaron (DIGI los reordena de vez en cuando). Vuelve a
la Fase 5 de la guía de despliegue y actualiza el campo `number:` de los
scripts afectados.

### "A veces marca mal el canal"

La pausa entre dígitos es corta para este deco. Sube el `delay` de
`script.digi_tune` de 320 a 500 ms.

### "Dejó de funcionar tras un corte de luz"

Si estás en el camino ADB, la depuración por red se habrá desactivado y hay que
volver a activarla en el deco. Es la razón principal por la que se recomienda
Android TV Remote.

Con Android TV Remote, el emparejamiento sobrevive: espera un par de minutos a
que el deco arranque y `script.digi_send_key` reconectará solo.

## Mantenimiento periódico

- **Actualizaciones de HA:** no actualices sin necesidad, y nunca en remoto sin
  poder ir a la casa. Un sistema que funciona no necesita la última versión.
- **Tras actualizar el decodificador:** vuelve a probar un cambio de canal.
  DIGI puede renumerar o cambiar la interfaz.
- **Copia de seguridad:** *Ajustes → Sistema → Copias de seguridad*. Hazla
  cuando todo funcione, y guárdala fuera de la Raspberry.
