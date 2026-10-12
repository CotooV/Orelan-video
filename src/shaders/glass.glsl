// ---------------------------------------------------------------------------
// Plano 2 («Vidrio»): un monolito conceptual de vidrio grueso, teñido de
// oliva por absorción (Beer–Lambert), sobre piedra negra pulida. Estudio con
// softboxes en tiras; un barrido de luz cruza por detrás al ritmo de la música.
// Refracción con dispersión espectral muestreada por submuestra temporal.
// ---------------------------------------------------------------------------
uniform vec3  uCamPos;
uniform vec3  uCamTgt;
uniform float uRoll;
uniform float uFov;
uniform float uSweep;     // azimut del barrido (rad); fuera de rango = apagado
uniform float uSweepI;    // intensidad del barrido
uniform float uKeyI;      // intensidad general del estudio
uniform int   uSample;

const vec3  BOX_C = vec3(0.0, 0.95, 0.0);
const vec3  BOX_B = vec3(0.30, 0.95, 0.105);
const float BOX_R = 0.022;
const vec3  SIGMA = vec3(2.75, 2.35, 5.4);   // absorción → oliva profundo

vec3 envStudio(vec3 d, float rough, int mode) {
    // mode 0: visión directa (negro), 1: reflejo en el vidrio, 2: a través del vidrio, 3: reflejo en el suelo
    vec3 c = vec3(0.0);
    // tira vertical principal, detrás a la izquierda
    c += vec3(1.0, 0.97, 0.90) * 4.0 * softbox(d, normalize(vec3(-0.75, 0.25, 0.62)), vec3(0, 1, 0), 0.9, 0.07, 0.01 + rough);
    // contra tira a la derecha
    c += vec3(0.95, 0.97, 1.0) * 6.0 * softbox(d, normalize(vec3(0.85, 0.20, 0.50)), vec3(0, 1, 0), 0.8, 0.045, 0.01 + rough);
    // cenital muy suave
    c += vec3(1.0) * 1.4 * softbox(d, normalize(vec3(0.0, 1.0, 0.15)), vec3(1, 0, 0), 0.35, 0.35, 0.08 + rough);
    // gran softbox trasero con degradado: hace brillar el volumen en oliva
    float g = sat(0.55 + d.y * 1.1);
    if (mode == 2 || mode == 3) c += vec3(1.0, 0.98, 0.92) * (mode == 3 ? 0.06 : 1.0) * (0.10 + 3.6 * g * g * g) * softbox(d, normalize(vec3(0.10, 0.12, 1.0)), normalize(vec3(0.0, 1.0, -0.12)), 4.0, 0.09, 0.14 + rough);
    c *= uKeyI;
    if (mode == 3) c *= 0.35;
    // barrido: tira vertical que recorre el fondo (solo la ve el vidrio)
    vec3 sd = normalize(vec3(sin(uSweep), 0.15, cos(uSweep)));
    if (mode == 1 || mode == 2) c += vec3(1.0, 0.98, 0.93) * uSweepI * softbox(d, sd, vec3(0, 1, 0), 3.0, 0.10, 0.03 + rough);
    if (mode == 0) c *= 0.0;  // el fondo directo permanece negro: solo vemos reflejos
    c += vec3(0.0009, 0.0010, 0.0007) * (0.4 + 0.6 * sat(d.y + 0.3));
    return c;
}

vec2 boxHit(vec3 ro, vec3 rd, vec3 b) {
    vec3 m = 1.0 / rd;
    vec3 n = m * (ro - BOX_C);
    vec3 k = abs(m) * b;
    vec3 t1 = -n - k, t2 = -n + k;
    float tN = max(max(t1.x, t1.y), t1.z);
    float tF = min(min(t2.x, t2.y), t2.z);
    if (tN > tF || tF < 0.0) return vec2(-1.0);
    return vec2(tN, tF);
}

// Normal biselada: caja exacta con aristas redondeadas en el sombreado
vec3 nGlass(vec3 p) {
    vec3 q = p - BOX_C;
    vec3 a = abs(q) - (BOX_B - BOX_R);
    vec3 pos = max(a, 0.0);
    int cnt = int(a.x > 0.0) + int(a.y > 0.0) + int(a.z > 0.0);
    if (cnt >= 2) return normalize(sign(q) * pos);
    vec3 r = abs(q) / BOX_B;
    if (r.x > r.y && r.x > r.z) return vec3(sign(q.x), 0, 0);
    if (r.y > r.z) return vec3(0, sign(q.y), 0);
    return vec3(0, 0, sign(q.z));
}

// fondo sin vidrio: suelo pulido + estudio
vec3 background(vec3 ro, vec3 rd, int mode) {
    if (rd.y < 0.0) {
        float t = -ro.y / rd.y;
        vec3 p = ro + rd * t;
        float vein = noise3(vec3(p.x * 0.05, 0.21, p.z * 0.05));
        float rough = mix(0.010, 0.022, vein);
        vec3 n = vec3(0, 1, 0);
        vec3 r = reflect(rd, n);
        float F = fresnel(dot(-rd, n), 0.05);
        vec3 c = F * envStudio(r, rough, 3);
        // poza de luz oliva transmitida por el vidrio
        vec2 q = p.xz - vec2(0.42, -0.30);
        float pool = exp(-dot(q * vec2(2.2, 3.4), q * vec2(2.2, 3.4)) * 6.0);
        c += C_OLIVE * 0.30 * pool * uKeyI;
        // oclusión de contacto
        vec2 bq = abs(p.xz - BOX_C.xz) - BOX_B.xz;
        float db = length(max(bq, 0.0));
        c *= mix(0.35, 1.0, smoothstep(0.0, 0.06, db));
        // la piedra se disuelve en la oscuridad: sin horizonte visible
        c *= 1.0 - smoothstep(2.0, 7.0, length(p.xz));
        return c;
    }
    return envStudio(rd, 0.0, mode);
}

// trazado del vidrio con hasta 5 rebotes internos
vec3 traceGlass(vec3 ro, vec3 rd, int mode, out bool hit) {
    hit = false;
    vec2 bb = boxHit(ro, rd, BOX_B);
    if (bb.x < 0.0 && bb.y < 0.0) return background(ro, rd, mode);
    if (bb.x < 0.0) return background(ro, rd, mode);
    float t = bb.x;
    hit = true;
    // índice por submuestra: dispersión espectral (R, G, B rotan)
    int k = uSample - 3 * (uSample / 3);
    float ior = 1.505 + (float(k) - 1.0) * 0.016;
    vec3 wk = k == 0 ? vec3(3, 0, 0) : (k == 1 ? vec3(0, 3, 0) : vec3(0, 0, 3));

    vec3 p = ro + rd * t;
    vec3 n = nGlass(p);
    float cosi = dot(-rd, n);
    float F = fresnel(cosi, 0.04);
    vec3 col = F * envStudio(reflect(rd, n), 0.002, 1);

    vec3 dir = refract(rd, n, 1.0 / ior);
    vec3 pos = p - n * 3e-4;
    vec3 thr = vec3(1.0 - F);
    for (int b = 0; b < 5; b++) {
        vec2 bi = boxHit(pos - dir * 1e-3, dir, BOX_B);
        float s = max(bi.y - 1e-3, 0.0);
        thr *= exp(-SIGMA * s);
        vec3 q = pos + dir * s;
        vec3 nn = -nGlass(q);
        vec3 out_ = refract(dir, nn, ior);
        float c2 = abs(dot(dir, nn));
        if (dot(out_, out_) < 1e-6) {
            dir = reflect(dir, nn);  // reflexión total interna
        } else {
            float Fi = fresnel(dot(out_, -nn), 0.04);
            col += thr * (1.0 - Fi) * wk * background(q - nn * 3e-4, out_, 2);
            thr *= Fi;
            dir = reflect(dir, nn);
        }
        pos = q + nn * 3e-4;
        if (max(thr.r, max(thr.g, thr.b)) < 0.004) break;
    }
    // brillo interno muy tenue (el “alma” oliva del volumen)
    col += C_OLIVE * 0.006 * uKeyI;
    return col;
}

void main() {
    mat3 B;
    vec3 rd = cameraRay(uCamPos, uCamTgt, uRoll, uFov, B);
    vec3 ro = uCamPos;
    bool hit;
    vec3 col = traceGlass(ro, rd, 0, hit);
    if (!hit && rd.y < 0.0) {
        // reflejo del monolito en la piedra pulida
        float t = -ro.y / rd.y;
        vec3 p = ro + rd * t;
        vec3 r = reflect(rd, vec3(0, 1, 0));
        if (boxHit(p, r, BOX_B).x > 0.0) {
            bool h2;
            vec3 rc = traceGlass(p + vec3(0, 1e-4, 0), r, 1, h2);
            float F = fresnel(dot(-rd, vec3(0, 1, 0)), 0.05);
            col += F * (rc - envStudio(r, 0.012, 3));
        }
    }
    fragColor = vec4(col, 1.0);
}
