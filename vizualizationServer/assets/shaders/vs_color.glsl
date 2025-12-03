#version 300 es
in vec4 a_position;
in vec4 a_color;
in vec3 a_normal;

uniform mat4 u_transforms;
uniform mat4 u_world;           // Matriz del mundo
uniform vec3 u_lightDirection;  // Dirección de la luz
uniform vec4 u_color;           // Color uniforme del objeto

out vec4 v_color;
out vec3 v_normal;
out vec3 v_lightDir;

void main() {
    gl_Position = u_transforms * a_position;
    v_color = u_color;
    
    // Transformar normales al espacio del mundo
    v_normal = mat3(u_world) * a_normal;
    v_lightDir = normalize(-u_lightDirection);
}