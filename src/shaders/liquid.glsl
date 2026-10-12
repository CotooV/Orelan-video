// ---------------------------------------------------------------------------
// Plano 3 («La gota»): una sola gota de esencia cae a cámara lenta sobre un
// líquido oscuro. Impacto, chorro de Worthington y trenes de ondas capilares.
// El nombre ÓRELAN existe en el espacio 3D: se refleja y se quiebra en las
// ondas del líquido.
// ---------------------------------------------------------------------------
uniform vec3  uCamPos;
uniform vec3  uCamTgt;
uniform float uRoll;
uniform float uFov;
uniform float uDropY;     // altura de la gota antes del impacto
uniform float uTau;       // tiempo desde el impacto (s); < 0 antes
uniform float uKeyI;
uniform sampler2DArray uTitle;   // capas: 0-2 ÓRELAN (nítido→difuso), 3-5 PERFUMERÍA
uniform vec4  uTitleRect;        // centro (x, y) y semiejes (hx, hy) en metros
uniform float uTitleZ;
uniform vec4  uTitleA;           // x: opacidad nombre, y: desenfoque nombre (0..2), z: radio de revelado, w: luminancia
uniform vec4  uTitleB;           // x: opacidad PERFUMERÍA, y: desenfoque, z,w: libres

const float DROP_R = 0.0105;

vec3 envLiquid(vec3 d, float rough, int mode) {
    vec3 c = vec3(0.0);
    // dos líneas horizontales al fondo: se rompen en las ondas
    c += vec3(1.0, 0.97, 0.88) * 1.1 * softbox(d, normalize(vec3(0.0, 0.045, 1.0)), vec3(1, 0, 0), 1.6, 0.0035, 0.002 + rough);
    c += vec3(0.86, 0.90, 0.62) * 0.9 * softbox(d, normalize(vec3(0.0, 0.13, 1.0)), vec3(1, 0, 0), 1.2, 0.004, 0.003 + rough);
    // cenital para el brillo de la gota
    c += vec3(1.0) * 3.0 * softbox(d, normalize(vec3(-0.15, 1.0, 0.25)), vec3(1, 0, 0), 0.3, 0.12, 0.05 + rough);
    // tira lateral izquierda (perfil de la gota)
    c += vec3(1.0, 0.97, 0.9) * 4.0 * softbox(d, normalize(vec3(-1.0, 0.25, 0.35)), vec3(0, 1, 0), 0.6, 0.06, 0.01 + rough);
    c += vec3(0.9, 0.95, 1.0) * 2.0 * softbox(d, normalize(vec3(1.0, 0.15, 0.6)), vec3(0, 1, 0), 0.6, 0.035, 0.01 + rough);
    c *= uKeyI;
    if (mode == 0) c *= 0.0;
    return c;
}

// --- superficie ------------------------------------------------------------
float ripple(vec2 xz) {
    float r = length(xz);
    float h = 0.00012 * (noise3(vec3(xz * 0.9, uG * 0.06)) - 0.5);
    if (uTau <= 0.0) return h;
    float tau = uTau;
    // tres paquetes de ondas capilares-gravitatorias
    for (int k = 0; k < 3; k++) {
        float fk = float(k);
        float v = 0.30 - 0.075 * fk;
        float kk = 160.0 - 38.0 * fk;
        float A = (0.0030 + 0.0010 * fk) * exp(-tau * (0.9 - 0.15 * fk));
        float c = v * tau;
        float sg = 0.010 + tau * (0.05 + 0.03 * fk);
        float e = exp(-pow((r - c) / sg, 2.0));
        h += A * e * cos(kk * (r - c)) / sqrt(1.0 + r * 14.0);
    }
    // cráter inicial que se recupera
    h -= 0.012 * exp(-r * r / 0.0003) * exp(-tau * 9.0) * smoothstep(0.0, 0.03, tau);
    return h;
}

vec3 rippleNormal(vec2 xz) {
    float e = 0.0006;
    float hx = ripple(xz + vec2(e, 0)) - ripple(xz - vec2(e, 0));
    float hz = ripple(xz + vec2(0, e)) - ripple(xz - vec2(0, e));
    return normalize(vec3(-hx, 2.0 * e, -hz));
}

// --- gota y chorro (SDF) -----------------------------------------------------
float jetH() {
    if (uTau <= 0.02 || uTau > 0.72) return 0.0;
    return 0.072 * pow(sin(PI * (uTau - 0.02) / 0.70), 0.8);
}

vec3 dropletPos() {
    float tp = 0.34;
    float s = uTau - tp;
    float y0 = 0.072 * pow(sin(PI * (tp - 0.02) / 0.70), 0.8) + 0.004;
    return vec3(0.0, y0 + 0.21 * s - 0.5 * 1.15 * s * s, 0.0);
}

float sdCapsule(vec3 p, vec3 a, vec3 b, float r) {
    vec3 pa = p - a, ba = b - a;
    float h = sat(dot(pa, ba) / dot(ba, ba));
    return length(pa - ba * h) - r;
}

float sdEllipsoid(vec3 p, vec3 r) {
    float k0 = length(p / r);
    float k1 = length(p / (r * r));
    return k0 * (k0 - 1.0) / k1;
}

float sdLiquidObj(vec3 p) {
    float d = 1e9;
    if (uTau < 0.0) {
        // gota en caída: ligeramente alargada por la velocidad
        d = sdEllipsoid(p - vec3(0.0, uDropY, 0.0), vec3(DROP_R * 0.94, DROP_R * 1.12, DROP_R * 0.94));
    } else {
        float hj = jetH();
        if (hj > 0.0) {
            float rj = mix(0.0065, 0.0042, sat(uTau / 0.6));
            d = sdCapsule(p, vec3(0, -0.01, 0), vec3(0, hj, 0), rj);
            // base ensanchada
            d = min(d, max(length(p.xz) - (rj + 0.0065 * exp(-max(p.y, 0.0) * 260.0)), p.y - 0.012));
            d = max(d, -p.y - 0.004);
        }
        if (uTau > 0.34) {
            vec3 dp = dropletPos();
            if (dp.y > -0.005) d = min(d, length(p - dp) - 0.0058);
        }
    }
    return d;
}

vec3 objNormal(vec3 p) {
    vec2 e = vec2(2e-4, 0);
    return normalize(vec3(sdLiquidObj(p + e.xyy) - sdLiquidObj(p - e.xyy),
                          sdLiquidObj(p + e.yxy) - sdLiquidObj(p - e.yxy),
                          sdLiquidObj(p + e.yyx) - sdLiquidObj(p - e.yyx)));
}

float marchObj(vec3 ro, vec3 rd, float tmax) {
    // volumen acotado alrededor del eje de impacto
    vec2 oc = ro.xz;
    float b = dot(oc, rd.xz), a = dot(rd.xz, rd.xz), c = dot(oc, oc) - 0.03 * 0.03;
    float disc = b * b - a * c;
    if (disc < 0.0) return -1.0;
    float sq = sqrt(disc);
    float t0 = max((-b - sq) / a, 0.0), t1 = min((-b + sq) / a, tmax);
    if (t0 > t1) return -1.0;
    float t = t0;
    for (int i = 0; i < 64; i++) {
        vec3 p = ro + rd * t;
        float d = sdLiquidObj(p);
        if (d < 1e-5) return t;
        t += d;
        if (t > t1) break;
    }
    return -1.0;
}

// --- título en el espacio ----------------------------------------------------
vec3 titleEmission(vec3 ro, vec3 rd, float tmax) {
    if (rd.z <= 1e-4) return vec3(0.0);
    float t = (uTitleZ - ro.z) / rd.z;
    if (t <= 0.0 || t > tmax) return vec3(0.0);
    vec3 q = ro + rd * t;
    vec2 uv = (q.xy - uTitleRect.xy) / uTitleRect.zw * 0.5 + 0.5;
    if (any(lessThan(uv, vec2(0.0))) || any(greaterThan(uv, vec2(1.0)))) return vec3(0.0);
    uv.y = 1.0 - uv.y;
    // nombre: se revela desde el centro, como una onda
    float bn = clamp(uTitleA.y, 0.0, 2.0);
    float l0 = floor(bn), fr = bn - l0;
    float a0 = texture(uTitle, vec3(uv, l0)).r;
    float a1 = texture(uTitle, vec3(uv, min(l0 + 1.0, 2.0))).r;
    float an = mix(a0, a1, fr);
    float rx = abs(uv.x - 0.5) * 2.0;
    float reveal = 1.0 - smoothstep(uTitleA.z - 0.18, uTitleA.z, rx);
    an *= uTitleA.x * reveal;
    float bp = clamp(uTitleB.y, 0.0, 2.0);
    float m0 = floor(bp), fp = bp - m0;
    float ap = mix(texture(uTitle, vec3(uv, 3.0 + m0)).r, texture(uTitle, vec3(uv, 3.0 + min(m0 + 1.0, 2.0))).r, fp);
    ap *= uTitleB.x;
    vec3 olive = vec3(0.60, 0.64, 0.38);
    return uTitleA.w * (C_WHITE * an + olive * ap * 0.85);
}

vec3 shadeObj(vec3 p, vec3 rd) {
    vec3 n = objNormal(p);
    float F = fresnel(dot(-rd, n), 0.03);
    vec3 col = F * envLiquid(reflect(rd, n), 0.0, 1);
    // transmisión: la esencia es un oro oliva translúcido
    vec3 tr = refract(rd, n, 1.0 / 1.36);
    vec3 env = envLiquid(normalize(tr * vec3(1.0, -1.0, 1.0) + vec3(0.0, 0.2, 0.0)), 0.06, 1);
    col += (1.0 - F) * env * vec3(0.78, 0.80, 0.42) * 0.55;
    col += (1.0 - F) * vec3(0.10, 0.11, 0.035) * uKeyI * sat(0.6 - n.y);
    return col;
}

void main() {
    mat3 B;
    vec3 rd = cameraRay(uCamPos, uCamTgt, uRoll, uFov, B);
    vec3 ro = uCamPos;
    vec3 col = vec3(0.0);

    // superficie: plano + refinamiento de la altura
    float ts = 1e9;
    if (rd.y < 0.0) {
        ts = -ro.y / rd.y;
        for (int i = 0; i < 4; i++) {
            vec3 p = ro + rd * ts;
            ts = (ripple(p.xz) - ro.y) / rd.y;
        }
    }
    float to = marchObj(ro, rd, min(ts, 50.0));
    if (to > 0.0) {
        col = shadeObj(ro + rd * to, rd);
    } else if (ts < 1e8) {
        vec3 p = ro + rd * ts;
        vec3 n = rippleNormal(p.xz);
        float F = fresnel(dot(-rd, n), 0.035);
        vec3 r = reflect(rd, n);
        if (r.y < 0.002) r.y = 0.002;
        float dist = length(p - ro);
        float rough = 0.0015 + dist * 0.00035;
        vec3 refl = envLiquid(r, rough, 1);
        float tobj = marchObj(p + n * 1e-4, r, 2.0);
        if (tobj > 0.0) refl = shadeObj(p + r * tobj, r);
        refl += titleEmission(p, r, 50.0);
        col = F * refl;
        // cuerpo del líquido: oliva profundo, casi negro
        col += (1.0 - F) * C_OLIVE * 0.010 * uKeyI * exp(-dist * 0.4);
        col = mix(col, vec3(0.0), smoothstep(2.5, 9.0, dist));
        col += titleEmission(ro, rd, ts);
    } else {
        col = envLiquid(rd, 0.0, 0) + titleEmission(ro, rd, 1e9);
    }
    fragColor = vec4(col, 1.0);
}
