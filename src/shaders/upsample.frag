#version 330 core
// Upsample con filtro tienda 3x3 (se suma sobre el nivel superior)
uniform sampler2D uSrc;
uniform vec2 uTexel;
uniform float uRadius;
in vec2 vUV;
out vec4 fragColor;
void main() {
    vec2 o = uTexel * uRadius;
    vec3 c = texture(uSrc, vUV).rgb * 4.0;
    c += (texture(uSrc, vUV + vec2(-o.x, 0)).rgb + texture(uSrc, vUV + vec2(o.x, 0)).rgb
        + texture(uSrc, vUV + vec2(0, -o.y)).rgb + texture(uSrc, vUV + vec2(0, o.y)).rgb) * 2.0;
    c += texture(uSrc, vUV + vec2(-o.x, -o.y)).rgb + texture(uSrc, vUV + vec2(o.x, -o.y)).rgb
       + texture(uSrc, vUV + vec2(-o.x, o.y)).rgb + texture(uSrc, vUV + vec2(o.x, o.y)).rgb;
    fragColor = vec4(c / 16.0, 1.0);
}
