#version 330 core
// Revelado final: bloom, gradación, tonemapping fílmico, grano y dither.
uniform sampler2D uHDR;
uniform sampler2D uBloom;
uniform sampler2D uText;     // tipografía premultiplicada, espacio de pantalla
uniform vec2  uRes;
uniform float uExposure;
uniform float uBloomAmt;
uniform float uVignette;
uniform float uGrain;
uniform float uFrame;
uniform float uFade;       // 0 = negro, 1 = imagen
in vec2 vUV;
out vec4 fragColor;

float h12(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }

// Curva fílmica (ACES, ajuste de Narkowicz) con hombro suave
vec3 aces(vec3 x) { return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0); }
vec3 toSRGB(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }

void main() {
    vec3 hdr = texture(uHDR, vUV).rgb;
    vec3 bloom = texture(uBloom, vUV).rgb;
    vec3 c = (hdr + bloom * uBloomAmt) * uExposure;

    // viñeta óptica suave (más fuerte arriba y abajo en vertical)
    vec2 q = (vUV - 0.5) * vec2(uRes.x / uRes.y, 1.0);
    float v = 1.0 - uVignette * smoothstep(0.25, 0.85, length(q * vec2(1.25, 1.0)));
    c *= v;

    // gradación: sombras levemente oliva-neutras, altas luces cálidas
    float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
    c = mix(c, c * vec3(0.985, 1.0, 0.94), smoothstep(0.0, 0.15, l) * (1.0 - smoothstep(0.15, 1.0, l)) * 0.6);

    c = aces(c);
    c = toSRGB(c);
    vec4 tx = texture(uText, vUV);
    c = c * (1.0 - tx.a) + tx.rgb;
    c *= uFade;

    // grano fino de película, concentrado en medios tonos
    float L = dot(c, vec3(0.299, 0.587, 0.114));
    vec2 px = vUV * uRes;
    float g1 = h12(px + uFrame * 17.13), g2 = h12(px * 1.37 + uFrame * 7.31 + 11.1);
    float gauss = (g1 + g2 - 1.0);
    c += gauss * uGrain * (0.25 + 3.0 * L * (1.0 - L));
    // dither triangular de 1 LSB contra el banding de los negros
    float d = (h12(px + uFrame * 3.17 + 5.3) + h12(px * 0.91 + uFrame * 1.7) - 1.0) / 255.0;
    c += d;
    fragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
}
