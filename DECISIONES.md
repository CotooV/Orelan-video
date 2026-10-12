# «UMBRAL» — Anuncio de apertura de Órelan Perfumería

**Entregable:** `out/orelan_apertura_15s.mp4` · 1080 × 1920 · 9:16 · 60 fps · 15,000 s (900 fotogramas) · H.264 + AAC 48 kHz
**Control de calidad:** `out/QC.md` (generado automáticamente sobre el MP4 final)
**Reproducible:** `./build.sh` reconstruye música, imagen y control de calidad desde el código.

---

## 1. La idea: una sola línea de luz que se abre

Un anuncio de apertura no debería vender perfume: debería presentar una casa. Construí toda la pieza sobre una única metáfora, **el umbral**: una puerta que se abre es, literalmente, «abrir sus puertas», y la luz que se filtra por una rendija es la promesa de algo que *está por descubrirse*.

De ahí sale un gesto gráfico único que recorre los cinco planos y le da identidad propia al spot: **una línea vertical de luz que se abre**.

| Plano | La línea vertical se convierte en… |
|---|---|
| 1 · Umbral | la rendija de luz entre dos hojas negras, que se enciende de abajo arriba |
| 2 · Vidrio | la arista luminosa del monolito y el barrido de luz que lo atraviesa |
| 3 · La gota | la trayectoria de la gota y el chorro que sube tras el impacto |
| 4 · Puertas | la rendija que, por fin, se abre |
| 5 · Revelación | la misma rendija reaparece sobre negro, se abre en horizontal y descubre el logotipo |

El spot arranca en oscuridad total durante 0,35 s (la primera luz aparece en el fotograma 21) y crece con el dron grave: es un silencio visual deliberado, lo bastante corto para no perder al espectador en redes.

El cierre «rima» con el primer fotograma: el espectador ve nacer la línea en el segundo 0 y la ve abrirse sobre la marca en el segundo 12. Es la firma visual de la campaña.

## 2. Estructura, ritmo y sincronía

La pieza está escrita sobre una rejilla musical: **80 BPM, 1 tiempo = 0,75 s = 45 fotogramas exactos**; 5 compases de 4/4 = 15,000 s. Imagen y música leen la misma tabla (`src/timeline.py`), así que cada corte, letra y golpe comparten reloj.

| Tiempo | Plano | Tipografía | Música |
|---|---|---|---|
| 0,00 | **Umbral** — oscuridad; la rendija se enciende desde el suelo; travelling lateral lento con paralaje | — | Rem(add9): dron subgrave, cuerdas que nacen del silencio |
| 0,75 | | «UNA NUEVA» / «ESENCIA» (foco y tracking que convergen desde el centro) | primera nota de piano de fieltro + campana de cristal |
| 3,00 | **Vidrio** — corte en golpe; látigo de cámara alrededor de un monolito de vidrio oliva | | golpe grave + Sib(maj7) |
| 3,75 / 4,125 | | «ESTÁ POR» · «DESCUBRIRSE» (cada letra emerge tras una línea de máscara) | dos notas del motivo descendente |
| 4,50 | barrido de luz cruzando el vidrio | | nota + campana |
| 5,25 | **La gota** — corte; la gota cae a cámara lenta (el texto anterior cruza el corte) | | destello de cristal y aspiración invertida |
| 6,00 | impacto, chorro de Worthington, ondas capilares | | gota sintetizada + golpe + Solm9 |
| 6,375 / 7,125 | grúa ascendente | «ÓRELAN» se expande desde el centro como una onda y se refleja quebrado en el líquido · «PERFUMERÍA» | firma melódica: 5ª descendente re–la |
| 9,00 | **Puertas** — corte en golpe; las hojas se desbloquean y se deslizan | | cierre metálico (síntesis modal) + La sus4 |
| 9,375 / 9,75 | | «ABRE SUS» · «PUERTAS» (las letras se separan desde el eje al ritmo de las hojas) | notas + latido que se acelera |
| 10,5–11,85 | la luz avanza, la cámara acelera hacia el vano | | La7 (sensible do♯), crescendo y *riser* |
| 11,85 | | | **respiro: 150 ms de silencio** |
| 12,00 | **Revelación** — corte a negro; la línea de luz reaparece y se abre | logotipo | golpe final + Re mayor(add9) en tutti, campanas |
| 13,125 | | firma «ABRE SUS PUERTAS» en oliva | nota de piano |
| 13,875 | destello satinado que recorre el logotipo | | campana aguda |
| 15,00 | fin sobre el logotipo | | cola de reverberación con microfundido |

Curva emocional: **misterio → anticipación → revelación**. Los planos se acortan (3,0 → 2,25 → 3,75 → 3,0 s) mientras la música pasa de menor a mayor y el pulso se acelera; el respiro de silencio antes del último golpe hace que la revelación «caiga» con todo su peso.

## 3. Dirección de arte

**Negro dominante.** En todo el spot la mayor parte de los píxeles tiene una luminancia inferior al 3 % (medido en `out/QC.md`). La luz se usa como un bien escaso: nunca hay más de una fuente protagonista por plano.

**Verde oliva como acento, no como relleno.** Aparece en cinco lugares concretos:
1. el velo de la luz que atraviesa la rendija (blanco cálido con alma oliva),
2. el volumen del monolito: el vidrio se tiñe por absorción física (Beer–Lambert), no por un color plano,
3. la gota de esencia, oro oliva translúcido, y el cuerpo del líquido,
4. las líneas tipográficas secundarias («UNA NUEVA», «ESTÁ POR», «ABRE SUS», «PERFUMERÍA», firma final), en un oliva claro (#B3B981 aprox.) con contraste > 7 : 1 sobre negro,
5. los bordes de la rendija que revela el logotipo.

**Blanco** cálido (#F1EDE3 aprox.), nunca blanco puro, para la tipografía principal y la luz.

**Materiales y luz.** Piedra negra pulida con rugosidad variable, vidrio grueso con aristas biseladas, dispersión cromática real y reflexión interna total, líquido con fresnel físico, bruma volumétrica con función de fase Henyey–Greenstein. Iluminación de estudio con softboxes en tiras (el lenguaje de la fotografía de perfumería), con banderas: el fondo directo se mantiene negro y la luz solo se ve en los reflejos.

**Tipografía.** Pareja de alta gama:
- **Bodoni Moda** (tamaño óptico 96, peso 400): didona de alto contraste, la voz clásica de la alta perfumería, para las palabras protagonistas.
- **Jost** (300–340): sans geométrica de raíz Futura, muy espaciada (tracking 0,50–0,66 em), para las líneas de apoyo.

Sistema constante: línea corta en sans oliva arriba + palabra protagonista en didona blanca abajo. Así cada frase tiene un acento y una jerarquía clara en una pantalla vertical. Ambas fuentes tienen licencia SIL OFL (incluidas en `fonts/`).

**Móvil.** Toda la tipografía queda entre el 13 % y el 62 % de la altura y dentro del 82 % central del ancho, lejos de la interfaz de Reels/TikTok/Facebook (barra superior, descripción y botones inferiores, iconos a la derecha). Alturas de mayúscula de 27 a 120 px a 1080 px de ancho; donde una frase cruza la luz (planos 1 y 4) las letras llevan una sombra difusa casi imperceptible para mantener el contraste.

## 4. Banda sonora

Compuesta y sintetizada desde cero en `src/music.py` (numpy/scipy). Sin samples, sin bancos de sonidos.

- **Piano de fieltro:** síntesis aditiva con parciales inarmónicos (coeficiente B de rigidez de cuerda), tres cuerdas ligeramente desafinadas por nota, decaimiento en dos etapas y golpe de macillo.
- **Cuerdas:** síntesis aditiva de diente de sierra con envolvente espectral de formantes, ensamble de seis voces con desafinación y vibrato independientes, panorama estéreo.
- **Campanas de cristal:** FM con relación inarmónica 1 : 3,5 y parciales de vidrio.
- **Golpes cinematográficos:** barrido de seno 100 → 33 Hz saturado + transitorio de ruido grave + cola subsónica.
- **Gota:** resonancia de burbuja con chirp ascendente (modelo de Minnaert).
- **Puertas:** síntesis modal de una pieza metálica pesada + rumor grave del deslizamiento.
- **Risers y aire:** ruido con filtro de banda móvil (STFT); *reverse swells* reverberados e invertidos que desembocan exactamente en cada golpe.
- **Espacio:** reverberación por convolución con respuesta al impulso sintética (decaimiento dependiente de la frecuencia, reflexiones tempranas).
- **Máster:** compresión de bus suave, limitador con anticipación, −14 LUFS integrados y true peak ≤ −1 dBTP (estándar de redes sociales).

Armonía: re menor → re mayor. La firma melódica de ÓRELAN es una quinta descendente (re–la), noble y reconocible; el último acorde la resuelve en mayor con la novena añadida, que da la sensación de «presentación oficial».

**Verificación de sincronía:** `tools/audio_report.py` y `tools/qc.py` detectan los ataques del audio final por flujo espectral y los comparan con los eventos visuales. Todos los golpes caen dentro de ±5 ms (menos de un tercio de fotograma).

## 5. Ejecución técnica

Todo es código: `src/` contiene el motor, los shaders y la música; no hay imágenes, vídeos, modelos 3D ni audio externos.

- **Render:** GLSL 3.3 (moderngl, OpenGL por software llvmpipe). Geometría analítica (puertas, monolito, gota, líquido) y raymarching solo donde aporta (chorro y gota tras el impacto).
- **Motion blur real:** cada fotograma integra entre 12 y 40 submuestras temporales dentro de un obturador de 180°. Las submuestras se recortan al intervalo de su plano, de modo que **ningún fotograma mezcla imágenes a través de un corte**. El látigo del plano 2 usa 40 submuestras para que el desenfoque sea continuo.
- La misma acumulación aporta **antialiasing** (jitter subpíxel de Halton) y la **dispersión espectral** del vidrio (cada submuestra traza una longitud de onda).
- **Revelado:** bloom físico de 7 niveles con umbral y techo por plano, gradación sutil, curva fílmica ACES, viñeta óptica, grano fino concentrado en medios tonos y dither de 1 LSB contra el *banding* en los negros.
- **Tipografía** compuesta después del tonemapping (color exacto en pantalla), con desenfoque de movimiento y foco por letra mediante un atlas con seis niveles de desenfoque gaussiano precalculados. «ÓRELAN» en el plano 3 vive en el espacio 3D para poder reflejarse en el líquido.
- **Codificación:** x264 High 4.2, CRF 12, `tune film`, yuv420p BT.709 etiquetado, GOP de 1 s, `faststart` para reproducción inmediata en redes.

## 6. Logotipo — situación y decisión

El encargo indica usar `./brand/orelan-logo.svg`. **El repositorio llegó vacío: no existía ese archivo ni ninguna referencia visual de la marca.** Siguiendo la instrucción de no inventar ni sustituir el monograma:

- El pipeline está preparado para el SVG oficial: si se coloca en `brand/orelan-logo.svg`, `src/brand.py` lo rasteriza fielmente (sin redibujar ni deformar), lo centra ópticamente y lo revela con la misma rendija de luz. Basta con ejecutar `./build.sh`.
- Mientras tanto, el cierre presenta **únicamente el nombre comercial «ÓRELAN PERFUMERÍA»** compuesto con la tipografía de campaña. **No se ha dibujado ningún monograma ni símbolo.** El MP4 entregado lleva esta composición tipográfica en el cierre; para la versión definitiva con el monograma oficial hay que añadir el SVG y volver a renderizar (unos 25 minutos).

## 7. Alternativas descartadas

| Alternativa | Por qué se descartó |
|---|---|
| Frasco de perfume procedural como protagonista | El brief prohíbe atribuir a Órelan diseños de frasco no proporcionados; además es el recurso de cualquier plantilla. El monolito y la gota son conceptuales. |
| Partículas doradas, polvo flotante, humo denso | Cliché de «lujo» genérico y con aspecto de IA. La bruma es casi invisible y solo existe donde la cruza la luz. |
| Destellos anamórficos (*lens flares*) | Efectistas; competían con la línea de luz, que ya es la firma. |
| Percusión de tráiler a 120 BPM | Demasiado agresiva para una casa de perfumería; se eligió 80 BPM, piano, cuerdas y vidrio. |
| Playfair Display / Cormorant / Italiana | Playfair está sobreexplotada; Cormorant pierde contraste en móvil; Italiana es demasiado fina para leer en movimiento. Bodoni Moda óptico 96 da el contraste de una didona de imprenta. |
| Texto con efecto máquina de escribir o *glitch* | Lenguaje tecnológico, no de lujo. |
| Monolito completamente retroiluminado | Parecía un letrero luminoso; se sustituyó por una tira estrecha con degradado vista solo a través del vidrio. |
| Reflejo especular del logotipo sobre el suelo | Duplicaba el nombre y competía con la firma «ABRE SUS PUERTAS»; el cierre queda más limpio sin él. |
| Mantener la pantalla en blanco ~0,8 s al abrirse las puertas | Rompía el dominio del negro; el desbordamiento de luz se limitó a los últimos 0,2 s antes del corte a negro. |

## 8. Iteraciones realizadas

1. **Puertas v1:** bruma y luz sobreexpuestas (todo el cuadro gris). Se recalibró la dispersión con una ventana geométrica exacta de la rendija y densidad dependiente de la apertura.
2. **Vidrio v1 (raymarching SDF):** aristas dentadas en ángulos rasantes → intersección analítica con normales biseladas en el sombreado.
3. **Vidrio v2:** casi invisible (campo oscuro) → softbox trasero visible solo a través del vidrio (campo claro). **v3:** parecía un panel luminoso → tira estrecha con degradado vertical; el suelo dejó de reflejar el softbox y se disolvió el horizonte.
4. **Color del vidrio:** el coeficiente de absorción se ajustó para un oliva real (no dorado) tras la curva fílmica.
5. **La gota:** error geométrico (el chorro era un cilindro infinito), horizonte de luz demasiado ancho → rugosidad dependiente de la distancia y líneas de luz más finas; la base del chorro se afinó.
6. **Título 3D:** cambiaba de tamaño con la grúa → plano más lejano y movimiento de grúa ascendente con distancia casi constante.
7. **Bloom:** la cadena sumaba 7 niveles (exceso de halo) → normalización y techo de entrada por plano; desapareció el velo gris en el plano de las puertas.
8. **Bug de borde:** una línea brillante en la parte superior venía de muestrear en modo repetición la textura acumulada → texturas en *clamp*.
9. **Plano 1 estático:** se añadió un travelling lateral con paralaje que revela la profundidad de la rendija.
10. **Legibilidad:** tamaño de las líneas sans de 34 a 40 px, oliva más claro y sombra difusa bajo el texto que cruza la luz.
11. **Música v1:** mezcla plana y piano enmascarado por las cuerdas (las notas de «DESCUBRIRSE» y «PUERTAS» no se detectaban) → rebalanceo dinámico (compás 1 más íntimo, compás 5 el más intenso), refuerzo de octava + campana en esas notas y eliminación de un silbido invertido.
12. **Motion blur:** escalonado visible en el látigo inicial del plano 2 → muestreo adaptativo de 40 submuestras.
13. **QC del máster final:** los dos acentos del cierre (firma a 13,125 s y destello a 13,875 s) quedaban enmascarados por la cola del acorde final y no se detectaban como ataques → se reforzaron (piano con tercera mayor + campana) y se remezcló solo el audio sobre el mismo vídeo, sin recodificar la imagen. El detector de cortes del QC confundía la apertura continua de la rendija con un corte → se pasó a un criterio relativo a la variación local.

Cada iteración se validó con fotogramas sueltos, hojas de contactos, una previsualización completa a media resolución con audio y, para la música, espectrograma, envolvente y detección de ataques.

## 9. Control de calidad

`tools/qc.py` se ejecuta sobre el MP4 final y genera `out/QC.md`. Verifica formato, 900 fotogramas a 60 fps constantes, duración exacta, cortes en su fotograma, ausencia de fotogramas aislados defectuosos o corruptos, continuidad del movimiento, dominio del negro, contraste WCAG de cada texto sobre su fondo real, sonoridad, true peak y sincronía golpe a golpe.

## 10. Tiempo de producción

Tiempo total de producción: **≈ 1 h 35 min** de reloj (08:14 – 09:49 UTC), en un único ordenador sin GPU (OpenGL por software, 4 núcleos).

| Fase | Tiempo aprox. |
|---|---|
| Concepto, guion técnico y rejilla musical | 5 min |
| Look-dev de los shaders (puertas, vidrio, líquido, revelación) con fotogramas de prueba | 25 min |
| Sistema tipográfico y coreografía letra a letra | 8 min |
| Composición, síntesis y mezcla de la música + análisis espectral | 10 min |
| Previsualización completa a media resolución e iteraciones de ajuste | 10 min |
| Render final 1080 × 1920 a 60 fps (900 fotogramas, 12–40 submuestras cada uno) | 39 min |
| Control de calidad, corrección de acentos del cierre y remezcla del audio | 8 min |

Con una GPU dedicada el render final bajaría a pocos minutos.

## 11. Estructura del proyecto

```
build.sh                 reconstrucción completa
src/timeline.py          rejilla musical, planos y golpes (fuente única de tiempo)
src/music.py             composición y síntesis de la banda sonora
src/engine.py            motor: acumulación temporal, bloom, revelado, tipografía
src/shots.py             cámaras, luces y coreografía de los cinco planos
src/titles.py            animación tipográfica letra a letra
src/typography.py        pareja tipográfica y atlas de glifos
src/brand.py             logotipo oficial (SVG) o composición del nombre comercial
src/shaders/*.glsl       escenas: puertas, vidrio, líquido, revelación; post-proceso
tools/qc.py              control de calidad del MP4
tools/audio_report.py    análisis de la música (espectrograma, ataques)
fonts/                   Bodoni Moda y Jost (SIL Open Font License)
brand/LEEME.md           dónde colocar el SVG oficial
```
