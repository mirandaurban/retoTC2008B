#version 300 es
in vec4 a_position;
in vec2 a_texCoord;

uniform mat4 u_transforms;

out vec2 v_texCoord;

void main() {
    v_texCoord = a_texCoord;
    gl_Position = u_transforms * a_position;
}
