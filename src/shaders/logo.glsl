// ---------------------------------------------------------------------------
// Plano 5 («Revelación»): sobre negro absoluto, la misma rendija de luz del
// primer plano reaparece en el eje y se abre en horizontal, descubriendo el
// logotipo. Reflejo tenue sobre un plano invisible y un único destello final.
// ---------------------------------------------------------------------------
uniform sampler2DArray uLogo;   // 0 nítido, 1 difuso medio, 2 halo amplio
uniform vec4  uLogoRect;        // cx, cy (px, origen abajo), w, h (px)
uniform float uOpen;            // semiancho de la apertura (px)
uniform float uSlitI;           // intensidad de los bordes de luz
uniform float uSlitH;           // semialtura del haz (px)
uniform float uSheen;           // posición del destello diagonal (px)
uniform float uSheenI;
uniform float uLogoI;           // luminancia del logotipo
uniform float uGlow;
uniform float uPush;            // zoom lento de cámara
uniform float uReflect;

vec4 sampleLogo(vec2 p, float layer) {
    vec2 uv = vec2((p.x - (uLogoRect.x - uLogoRect.z * 0.5)) / uLogoRect.z,
                   ((uLogoRect.y + uLogoRect.w * 0.5) - p.y) / uLogoRect.w);
    if (any(lessThan(uv, vec2(0.0))) || any(greaterThan(uv, vec2(1.0)))) return vec4(0.0);
    return vec4(texture(uLogo, vec3(uv, layer)).r);
}

void main() {
    vec2 c = 0.5 * uRes;
    vec2 p = gl_FragCoord.xy + uJit;
    p = c + (p - c) / uPush;
    vec3 col = vec3(0.0);

    // profundidad: un velo oliva casi imperceptible detrás del logotipo
    vec2 q = (p - uLogoRect.xy) / uRes.x;
    col += C_OLIVE * 0.020 * exp(-dot(q, q) * 5.0) * uGlow;

    float dx = p.x - uLogoRect.x;
    float open = smoothstep(uOpen + 1.5, uOpen - 1.5, abs(dx));

    // logotipo
    float a = sampleLogo(p, 0.0).r;
    float halo = sampleLogo(p, 2.0).r;
    float vgrad = 0.93 + 0.07 * sat((p.y - (uLogoRect.y - uLogoRect.w * 0.5)) / uLogoRect.w);
    vec3 logo = C_WHITE * uLogoI * vgrad;
    // destello diagonal (brillo satinado que recorre las letras)
    float s = (p.x + 0.45 * p.y) - uSheen;
    float sheen = exp(-s * s / (2.0 * 90.0 * 90.0));
    logo += vec3(1.0, 0.98, 0.92) * uSheenI * sheen;
    col += logo * a * open;
    col += vec3(0.62, 0.66, 0.40) * halo * 0.10 * uGlow * open;

    // reflejo sobre el plano invisible bajo el logotipo
    float yb = uLogoRect.y - uLogoRect.w * 0.5;
    if (p.y < yb) {
        float dy = yb - p.y;
        vec2 pr = vec2(p.x, yb + dy + 6.0);
        float ar = mix(sampleLogo(pr, 1.0).r, sampleLogo(pr, 2.0).r, sat(dy / 260.0));
        col += C_WHITE * uLogoI * ar * open * uReflect * exp(-dy / 110.0);
    }

    // bordes de la rendija: luz blanca con alma oliva
    float vfall = exp(-pow(abs(p.y - uLogoRect.y) / uSlitH, 2.0));
    float edge = exp(-abs(abs(dx) - uOpen) / 1.6);
    float edgeHalo = exp(-abs(abs(dx) - uOpen) / 26.0);
    vec3 slitCol = mix(vec3(1.0, 0.98, 0.92), vec3(0.78, 0.84, 0.50), sat(abs(dx) / 220.0));
    col += slitCol * uSlitI * vfall * (edge * 6.0 + edgeHalo * 0.25);

    fragColor = vec4(col, 1.0);
}
