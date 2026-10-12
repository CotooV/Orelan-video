// ---------------------------------------------------------------------------
// Planos 1 («Umbral») y 4 («Puertas»): un vano monumental en negro con dos
// hojas correderas. La luz de la sala posterior se filtra por la rendija,
// dibuja una franja sobre el suelo pulido y atraviesa una bruma tenue.
// Geometría analítica (sin raymarching) para máxima nitidez y velocidad.
// ---------------------------------------------------------------------------
uniform vec3  uCamPos;
uniform vec3  uCamTgt;
uniform float uRoll;
uniform float uFov;
uniform float uGap;      // semiancho de la rendija (m)
uniform float uLight;    // radiancia de la sala posterior
uniform float uReveal;   // 0..1 encendido vertical de la rendija
uniform float uHaze;     // densidad de bruma
uniform float uFill;     // relleno frontal muy tenue
uniform float uFlood;    // 0..1 la luz desborda (clímax)

const float DW = 0.92;   // semiancho del vano
const float DH = 3.40;   // altura del vano
const float ZP = 0.035;  // retranqueo de las hojas respecto al muro
const float DD = 0.14;   // grosor de las hojas

vec3 lightCol() {
    // blanco cálido con un velo oliva: el acento de marca vive en la luz
    return mix(C_LIGHT, vec3(0.80, 0.86, 0.52), 0.30);
}

float revealMask(float y) {
    float h = uReveal * (DH + 0.8) - 0.4;
    return 1.0 - smoothstep(h - 0.35, h + 0.35, y);
}

vec3 roomRadiance(vec3 p) {
    float grad = 0.80 + 0.45 * exp(-max(p.y, 0.0) * 0.9);
    // un núcleo más blanco hacia el eje, el oliva tiñe los bordes
    vec3 c = mix(lightCol(), vec3(1.0, 0.985, 0.94), 0.55 * exp(-abs(p.x) * 2.5));
    return uLight * c * grad * revealMask(p.y);
}

// Ventana horizontal visible de la rendija desde el punto q (z < ZP)
float slitWindow(vec3 q) {
    float r = max(ZP - q.z, 0.02);
    float s = DD / r;
    float a0 = max(-uGap, (-uGap + q.x * s) / (1.0 + s));
    float a1 = min( uGap, ( uGap + q.x * s) / (1.0 + s));
    return max(0.0, a1 - a0);
}

// mat: 0 vacío, 1 suelo, 2 muro, 3 hoja, 4 luz/rendija
float traceDoor(vec3 ro, vec3 rd, out int mat, out vec3 rad) {
    rad = vec3(0.0);
    mat = 0;
    float tf = rd.y < 0.0 ? -ro.y / rd.y : 1e9;
    if (rd.z <= 1e-5) { mat = tf < 1e9 ? 1 : 0; return tf; }
    float tw = (0.0 - ro.z) / rd.z;
    if (tf < tw) { mat = 1; return tf; }
    vec3 p = ro + rd * tw;
    if (abs(p.x) > DW || p.y > DH) { mat = 2; return tw; }
    float tp = (ZP - ro.z) / rd.z;
    if (tf < tp) { mat = 1; return tf; }
    vec3 pp = ro + rd * tp;
    if (abs(pp.x) > uGap) { mat = 3; return tp; }
    float tb = (ZP + DD - ro.z) / rd.z;
    vec3 pb = ro + rd * tb;
    if (abs(pb.x) <= uGap) {
        mat = 4;
        if (tf < tb) {
            vec3 pf = ro + rd * tf;
            rad = roomRadiance(pf) * mix(0.35, 1.0, sat((pf.z - ZP) / DD));
            return tf;
        }
        rad = pb.y > DH ? vec3(0.0) : roomRadiance(pb);
        return tb;
    }
    // cara interior de la hoja, rozada por la luz
    float side = sign(pb.x);
    float ts = (side * uGap - ro.x) / rd.x;
    vec3 ps = ro + rd * ts;
    float u = sat((ps.z - ZP) / DD);
    mat = 4;
    rad = roomRadiance(ps) * 0.28 * u * u;
    if (tf < ts) rad = roomRadiance(ro + rd * tf) * 0.3;
    return ts;
}

vec3 shadePanel(vec3 p) {
    float dx = abs(p.x) - uGap;
    float m = revealMask(p.y) * uLight;
    vec3 col = vec3(0.0020) * uFill * (0.6 + 0.4 * sat(p.y / DH));
    // bisel de la rendija y luz que lame la cara frontal
    col += lightCol() * m * (0.010 * exp(-dx / 0.05) + 0.060 * exp(-dx / 0.006) + 0.20 * exp(-dx / 0.0012));
    col += lightCol() * m * 0.10 * uHaze * min(uGap, 0.6) * exp(-dx / 0.7);
    // satinado vertical muy sutil
    float grain = noise3(vec3(p.x * 9.0, p.y * 0.08, 0.37));
    col *= 0.80 + 0.40 * grain;
    // junta de la hoja contra el marco
    float edge = DW - abs(p.x);
    col *= mix(0.25, 1.0, smoothstep(0.0, 0.006, edge));
    return col;
}

vec3 shadeWall(vec3 p) {
    vec3 col = vec3(0.0016) * uFill;
    float open = sat(uGap / DW);
    // distancia al contorno del vano (rectángulo |x|<DW, y<DH)
    vec2 dq = vec2(abs(p.x) - DW, p.y - DH);
    float dEdge = length(max(dq, 0.0)) + min(max(dq.x, dq.y), 0.0);
    col += lightCol() * uLight * (0.0015 + 0.02 * open) * exp(-max(dEdge, 0.0) / 0.003);
    col += lightCol() * uLight * uHaze * 0.5 * open * exp(-length(vec2(p.x, max(p.y - DH, 0.0))) * 1.5);
    float grain = noise3(vec3(p.x * 0.6, p.y * 0.6, 0.71));
    return col * (0.85 + 0.3 * grain);
}

vec3 shadeSecondary(vec3 ro, vec3 rd) {
    int mat; vec3 rad;
    float t = traceDoor(ro, rd, mat, rad);
    vec3 p = ro + rd * t;
    if (mat == 4) return rad;
    if (mat == 3) return shadePanel(p);
    if (mat == 2) return shadeWall(p);
    return vec3(0.0);
}

vec3 shadeFloor(vec3 ro, vec3 rd, vec3 p) {
    // irradiancia de la rendija (fuente lineal vertical)
    float r = max(ZP - p.z, 0.02);
    float w = slitWindow(p);
    float E = w * (0.5 / r) * (1.0 - r * r / (r * r + DH * DH));
    float floorReveal = revealMask(0.25);
    float vein = noise3(vec3(p.x * 0.25, 0.13, p.z * 0.25));
    float albedo = 0.030 * (0.85 + 0.3 * vein);
    vec3 col = lightCol() * uLight * E * albedo / PI * floorReveal;
    col += vec3(0.0012) * uFill;

    // reflexión especular: piedra negra pulida, rugosidad baja y variable
    float rough = mix(0.012, 0.035, vein);
    vec2 h = hash23(vec3(gl_FragCoord.xy, uSeed * 13.0 + 1.0));
    float a = 6.2831853 * h.x, rr = rough * sqrt(-2.0 * log(max(h.y, 1e-4)));
    vec3 n = normalize(vec3(cos(a) * rr, 1.0, sin(a) * rr));
    vec3 rd2 = reflect(rd, n);
    if (rd2.y < 0.0) rd2.y = -rd2.y;
    float F = fresnel(dot(-rd, n), 0.05);
    col += F * shadeSecondary(p + vec3(0.0, 1e-4, 0.0), rd2);
    return col;
}

vec3 hazeIntegral(vec3 ro, vec3 rd, float tmax) {
    if (uHaze <= 0.0) return vec3(0.0);
    const int N = 44;
    tmax = min(tmax, 22.0);
    float dt = tmax / float(N);
    float j = rnd(3.0);
    float acc = 0.0;
    for (int i = 0; i < N; i++) {
        float t = (float(i) + j) * dt;
        vec3 q = ro + rd * t;
        if (q.z > ZP || q.y < 0.0) continue;
        float w = slitWindow(q);
        if (w <= 0.0) continue;
        float r = max(ZP - q.z, 0.03);
        float yy = clamp(q.y, 0.0, DH);
        float vAng = atan((DH - yy) / r) + atan(yy / r);
        float fl = (w / r) * vAng * revealMask(q.y * 0.7);
        vec3 src = vec3(clamp(q.x, -uGap, uGap), yy, ZP);
        vec3 ldir = normalize(q - src);
        float ph = phaseHG(dot(ldir, -rd), 0.62);
        vec3 nq = q * 0.16 + vec3(0.013 * uG, -0.035 * uG, 0.02 * uG);
        float n = noise3(nq) * 0.65 + noise3(nq * 2.7 + 0.31) * 0.35;
        float dens = 0.15 + 3.2 * n * n * n;
        dens *= exp(-q.y * 0.12);
        acc += dens * fl * ph * dt;
    }
    return lightCol() * uLight * uHaze * acc;
}

void main() {
    mat3 B;
    vec3 rd = cameraRay(uCamPos, uCamTgt, uRoll, uFov, B);
    vec3 ro = uCamPos;
    int mat; vec3 rad;
    float t = traceDoor(ro, rd, mat, rad);
    vec3 p = ro + rd * t;
    vec3 col;
    if (mat == 4) col = rad;
    else if (mat == 3) col = shadePanel(p);
    else if (mat == 2) col = shadeWall(p);
    else if (mat == 1) col = shadeFloor(ro, rd, p);
    else col = vec3(0.0);
    col += hazeIntegral(ro, rd, min(t, 40.0));
    // desbordamiento final: la luz inunda la lente
    col += lightCol() * uLight * 0.02 * uFlood * uFlood;
    fragColor = vec4(col, 1.0);
}
