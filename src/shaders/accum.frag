#version 330 core
// Suma ponderada de una submuestra temporal al acumulador
uniform sampler2D uSrc;
uniform float uWeight;
in vec2 vUV;
out vec4 fragColor;
void main() { fragColor = vec4(texture(uSrc, vUV).rgb * uWeight, uWeight); }
