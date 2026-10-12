#version 330 core
// ---------------------------------------------------------------------------
// Órelan · «Umbral» — utilidades compartidas por todos los planos.
// Render lineal HDR; el tonemapping se hace en post.glsl.
// ---------------------------------------------------------------------------
uniform vec2  uRes;      // resolución de salida en píxeles
uniform float uT;        // tiempo local del plano (s)
uniform float uG;        // tiempo global (s)
uniform vec2  uJit;      // jitter subpíxel (AA por acumulación)
uniform float uSeed;     // semilla por submuestra
uniform sampler3D uNoise;  // ruido fBm tileable 128^3

out vec4 fragColor;

const float PI = 3.14159265359;

// Paleta de marca (lineal)
const vec3 C_WHITE = vec3(0.93, 0.91, 0.86);
const vec3 C_OLIVE = vec3(0.235, 0.265, 0.105);   // ~ #848A55 en sRGB
const vec3 C_OLIVE_LIGHT = vec3(0.52, 0.56, 0.30);
const vec3 C_LIGHT = vec3(1.00, 0.955, 0.84);     // luz cálida de estudio

float sat(float x) { return clamp(x, 0.0, 1.0); }
vec3  sat(vec3 x)  { return clamp(x, 0.0, 1.0); }

float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * .1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
float hash13(vec3 p3) {
    p3 = fract(p3 * .1031);
    p3 += dot(p3, p3.zyx + 31.32);
    return fract((p3.x + p3.y) * p3.z);
}
vec2 hash23(vec3 p3) {
    p3 = fract(p3 * vec3(.1031, .1030, .0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}

float rnd(float k) { return hash13(vec3(gl_FragCoord.xy, uSeed * 17.31 + k * 3.7)); }

float smoother(float x) { x = sat(x); return x * x * x * (x * (x * 6.0 - 15.0) + 10.0); }
float easeOutCubic(float x) { x = sat(x); return 1.0 - pow(1.0 - x, 3.0); }
float easeInOutCubic(float x) { x = sat(x); return x < 0.5 ? 4.0 * x * x * x : 1.0 - pow(-2.0 * x + 2.0, 3.0) / 2.0; }

float noise3(vec3 p) { return texture(uNoise, p).r; }

// Cámara: devuelve la dirección del rayo para el píxel actual
vec3 cameraRay(vec3 ro, vec3 ta, float roll, float vfovDeg, out mat3 basis) {
    vec3 f = normalize(ta - ro);
    vec3 up = vec3(sin(roll), cos(roll), 0.0);
    vec3 r = normalize(cross(up, f));
    vec3 u = cross(f, r);
    basis = mat3(r, u, f);
    vec2 uv = (gl_FragCoord.xy + uJit - 0.5 * uRes) / uRes.y;
    float z = 0.5 / tan(radians(vfovDeg) * 0.5);
    return normalize(uv.x * r + uv.y * u + z * f);
}

float fresnel(float cosi, float f0) {
    return f0 + (1.0 - f0) * pow(1.0 - sat(cosi), 5.0);
}

// Luz de estudio rectangular (softbox) en el espacio de direcciones.
// c: dirección al centro; a: eje largo; hl/hw: semiejes en proyección gnomónica.
float softbox(vec3 d, vec3 c, vec3 a, float hl, float hw, float soft) {
    float cd = dot(d, c);
    if (cd <= 1e-3) return 0.0;
    vec3 b = normalize(cross(c, a));
    vec2 q = vec2(dot(d, a), dot(d, b)) / cd;
    vec2 e = vec2(hl, hw);
    vec2 m = 1.0 - smoothstep(e - soft, e + soft, abs(q));
    // ligera caída hacia los extremos, como un softbox real
    float fall = 0.75 + 0.25 * (1.0 - pow(abs(q.x) / (hl + soft), 4.0));
    return m.x * m.y * fall;
}

// Henyey–Greenstein
float phaseHG(float c, float g) {
    float g2 = g * g;
    return (1.0 - g2) / (4.0 * PI * pow(1.0 + g2 - 2.0 * g * c, 1.5));
}

// Caja redondeada (SDF)
float sdRoundBox(vec3 p, vec3 b, float r) {
    vec3 q = abs(p) - b + r;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
}
