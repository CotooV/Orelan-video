#version 330 core
// Glifo instanciado: rectángulo en píxeles (origen arriba-izquierda)
in vec2 in_corner;
in vec4 i_rect;    // x, y, w, h
in vec4 i_uv;      // u0, v0, u1, v1
in vec4 i_par;     // opacidad, desenfoque, escala, línea de recorte (y px; <0 = sin recorte)
in vec4 i_col;     // rgb, pivote x
in float i_piv;    // pivote y
uniform vec2 uRes;
uniform vec2 uJit;
uniform float uScale;   // escala global (previsualizaciones a menor resolución)
out vec2 vUV;
out float vOp;
out float vBlur;
out vec3 vCol;
out float vY;
out float vClip;
void main() {
    vec2 piv = vec2(i_col.w, i_piv);
    vec2 pos = i_rect.xy + in_corner * i_rect.zw;
    pos = piv + (pos - piv) * i_par.z;
    vY = pos.y;
    vClip = i_par.w;
    pos *= uScale;
    pos += vec2(-uJit.x, uJit.y);
    gl_Position = vec4(pos.x / uRes.x * 2.0 - 1.0, 1.0 - pos.y / uRes.y * 2.0, 0.0, 1.0);
    vUV = mix(i_uv.xy, i_uv.zw, in_corner);
    vOp = i_par.x;
    vBlur = i_par.y;
    vCol = i_col.rgb;
}
