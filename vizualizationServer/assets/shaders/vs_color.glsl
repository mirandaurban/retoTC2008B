#version 300 es
in vec4 a_position;
in vec4 a_color;

uniform mat4 u_transforms;
uniform vec4 u_color;  // ✅ Agregar uniform de color

out vec4 v_color;

void main() {
    gl_Position = u_transforms * a_position;
    v_color = u_color;  // ✅ Usar el color uniform en lugar del color del vértice
}