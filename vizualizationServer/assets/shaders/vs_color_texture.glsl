#version 300 es
in vec4 a_position;
in vec4 a_color;
in vec2 a_texCoord;
in vec3 a_normal;

uniform mat4 u_transforms;
uniform mat4 u_world;  // Matriz del mundo
uniform vec3 u_lightDirection;  // Dirección de la luz

out vec2 v_texCoord;
out vec4 v_color;
out vec3 v_normal;
out vec3 v_lightDir;

void main() {
    v_texCoord = a_texCoord;
    gl_Position = u_transforms * a_position;
    v_color = a_color;
    
    // Transformar normales al espacio del mundo
    v_normal = mat3(u_world) * a_normal;
    v_lightDir = normalize(-u_lightDirection);
}