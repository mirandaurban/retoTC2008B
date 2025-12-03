#version 300 es
precision highp float;

in vec4 v_color;
in vec2 v_texCoord;
in vec3 v_normal;
in vec3 v_lightDir;

uniform sampler2D u_texture;
uniform vec3 u_lightColor;      // Color de la luz para semáforos
uniform float u_lightIntensity; // Intensidad de la luz

out vec4 outColor;

void main() {
    vec4 texColor = texture(u_texture, v_texCoord);
    
    // Calcular iluminación simple (difusa)
    vec3 normal = normalize(v_normal);
    float diff = max(dot(normal, v_lightDir), 0.0);
    vec3 diffuse = diff * u_lightColor * u_lightIntensity;
    
    // Combinar con color de textura
    outColor = texColor * vec4(diffuse, 1.0);
}