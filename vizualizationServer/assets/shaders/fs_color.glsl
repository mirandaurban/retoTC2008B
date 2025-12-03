#version 300 es
precision highp float;

in vec4 v_color;
in vec3 v_normal;
in vec3 v_lightDir;

uniform vec3 u_lightColor;      // Color de la luz
uniform float u_lightIntensity; // Intensidad de la luz
uniform vec4 u_objectColor;     // Color para semáforos

out vec4 outColor;

void main() {
    // Para semáforos, usar el color uniforme
    vec4 baseColor = length(u_objectColor) > 0.0 ? u_objectColor : v_color;
    
    // Calcular iluminación simple (difusa)
    vec3 normal = normalize(v_normal);
    float diff = max(dot(normal, v_lightDir), 0.0);
    vec3 diffuse = diff * u_lightColor * u_lightIntensity;
    
    // Aplicar iluminación al color base
    outColor = baseColor * vec4(diffuse, 1.0);
}