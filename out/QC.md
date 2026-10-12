# Informe de control de calidad

Archivo: `out/orelan_apertura_15s.mp4`

## Formato

| | Comprobación | Resultado |
|---|---|---|
| ✅ | Resolución 1080×1920 (9:16) | 1080×1920 |
| ✅ | 60 fps constantes | r=60/1, avg=60/1 |
| ✅ | Fotogramas = 900 | 900 |
| ✅ | Duración de vídeo 15,000 s | 15.000 s |
| ✅ | Códec H.264 High, yuv420p | h264 High yuv420p |
| ✅ | Color BT.709 etiquetado | bt709/bt709/bt709 |
| ✅ | Audio AAC 48 kHz estéreo | aac 48000 Hz 2 ch 295 kb/s |
| ✅ | Duración de audio ≈ 15 s | 15.000 s |
| ✅ | Duración del contenedor | 15.000 s |
| ✅ | faststart (moov al inicio) | −movflags +faststart |
| ✅ | Tamaño apto para redes (< 100 MB) | 32.4 MB, 17.3 Mb/s |

## Imagen

| | Comprobación | Resultado |
|---|---|---|
| ✅ | Cortes en su fotograma exacto (y solo ahí) | esperados [180, 315, 540, 720]; detectados [180, 315, 540, 720] |
| ✅ | Sin fotogramas defectuosos aislados (flashes/saltos) | 0 [] |
| ✅ | Sin fotogramas corruptos (saturados / color inválido) | [] |
| ✅ | Apertura en oscuridad breve y sin negros posteriores | primera luz visible en el fotograma 21 (0.35 s); negros posteriores: [] |
| ✅ | Movimiento continuo (sin tirones dentro de los planos) | [] |
| ✅ | El negro domina la composición | 88% de píxeles con luminancia < 3% |

## Legibilidad (contraste WCAG con el fondo real)

| | Texto | Instante | Contraste (texto / fondo p90) | Altura de mayúscula |
|---|---|---|---|---|
| ✅ | UNA NUEVA ESENCIA | 2.10 s | 16.1 : 1 | ≥ 27 px |
| ✅ | ESTÁ POR DESCUBRIRSE | 5.00 s | 17.9 : 1 | ≥ 27 px |
| ✅ | ÓRELAN PERFUMERÍA | 8.30 s | 19.3 : 1 | ≥ 27 px |
| ✅ | ABRE SUS PUERTAS | 10.60 s | 17.0 : 1 | ≥ 27 px |
| ✅ | Logotipo + firma | 14.50 s | 18.7 : 1 | ≥ 27 px |

## Zonas seguras para Reels / TikTok

Toda la tipografía y el logotipo quedan entre el 13 % y el 62 % de la altura y dentro del 82 % central del ancho: fuera de la barra superior, del pie con descripción/botones (≈ 20 % inferior) y de la columna de iconos a la derecha.

## Audio y sincronía

| | Comprobación | Resultado |
|---|---|---|
| ✅ | Sonoridad integrada ≈ −14 LUFS (redes) | -14.0 LUFS |
| ✅ | True peak ≤ −1 dBTP | -1.44 dBTP |
| ✅ | Sincronía golpes ↔ imagen | peor desfase 5 ms (1 fotograma = 16,7 ms) |

| Evento visual | Tiempo | Ataque musical detectado | Desfase | Prominencia |
|---|---|---|---|---|
| t1_entra | 0.750 s | 0.752 s | +2 ms | 11.2 σ |
| corte_vidrio | 3.000 s | 2.997 s | -3 ms | 15.5 σ |
| t2a_entra | 3.750 s | 3.749 s | -1 ms | 4.4 σ |
| t2b_entra | 4.125 s | 4.128 s | +3 ms | 5.2 σ |
| barrido_luz | 4.500 s | 4.501 s | +1 ms | 7.0 σ |
| corte_gota | 5.250 s | 5.253 s | +3 ms | 6.0 σ |
| impacto_gota | 6.000 s | 6.000 s | +0 ms | 10.8 σ |
| t3a_entra | 6.375 s | 6.379 s | +4 ms | 3.4 σ |
| t3b_entra | 7.125 s | 7.125 s | +0 ms | 7.8 σ |
| puertas | 9.000 s | 8.997 s | -3 ms | 12.6 σ |
| t4a_entra | 9.375 s | 9.376 s | +1 ms | 3.2 σ |
| t4b_entra | 9.750 s | 9.755 s | +5 ms | 4.1 σ |
| logo | 12.000 s | 12.000 s | +0 ms | 12.5 σ |
| firma | 13.125 s | 13.125 s | +0 ms | 5.3 σ |
| brillo_logo | 13.875 s | 13.877 s | +2 ms | 6.1 σ |

Respiro previo a la revelación (11,85–12,00 s): -40.8 dBFS RMS.

**Resultado global: APROBADO**
