#version 330 core
uniform sampler2DArray uAtlas;
in vec2 vUV;
in float vOp;
in float vBlur;
in vec3 vCol;
in float vY;
in float vClip;
out vec4 fragColor;
void main() {
    float b = clamp(vBlur, 0.0, 4.999);
    float l0 = floor(b);
    float a = mix(texture(uAtlas, vec3(vUV, l0)).r, texture(uAtlas, vec3(vUV, l0 + 1.0)).r, b - l0);
    if (vClip >= 0.0) a *= smoothstep(vClip + 0.8, vClip - 0.8, vY);
    a = clamp(a, 0.0, 1.0) * vOp;
    fragColor = vec4(vCol * a, a);
}
