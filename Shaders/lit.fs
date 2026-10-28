#version 330

// Cel-shaded point lights (from shader_test.py). Each light fades to nothing at its range.
// No shadows, so each light only lights its own car: the z range in lightZone (z from .x up to .y).
// A lamp also brightens its whole car by lightFill, so a car whose lamp is off drops to `ambient` (dark).

#define MAX_LIGHTS 8   // keep in sync with lighting.MAX_LIGHTS

in vec3 fragPosition;
in vec3 fragNormal;
in vec2 fragTexCoord;
in vec4 fragColor;

uniform sampler2D texture0;
uniform vec4 colDiffuse;

uniform int lightCount;
uniform vec3 lightPos[MAX_LIGHTS];
uniform vec3 lightColor[MAX_LIGHTS];   // colour * intensity; 0 = off (or the dark half of a blink)
uniform float lightRange[MAX_LIGHTS];
uniform vec2 lightZone[MAX_LIGHTS];    // z range the light reaches (its car)
uniform vec3 lightFill[MAX_LIGHTS];    // added to the whole zone while the light is on (0 = none; red in an alarm)
uniform float ambient;                 // brightness where no light reaches: a car with its lamp off
uniform float bands;                   // cel-shading steps

out vec4 finalColor;

void main()
{
    vec3 normal = normalize(fragNormal);
    vec3 light = vec3(ambient);

    for (int i = 0; i < lightCount; i++)
    {
        if (fragPosition.z < lightZone[i].x || fragPosition.z >= lightZone[i].y) continue;   // another car
        light += lightFill[i];
        vec3 toLight = lightPos[i] - fragPosition;
        float dist = length(toLight);
        float diffuse = max(dot(normal, toLight / dist), 0.0);
        float falloff = clamp(1.0 - dist / lightRange[i], 0.0, 1.0);
        float amount = diffuse * falloff * falloff;
        amount = floor(amount * bands + 0.5) / bands;   // hard steps instead of a smooth gradient
        light += lightColor[i] * amount;
    }

    vec4 base = texture(texture0, fragTexCoord) * colDiffuse * fragColor;
    finalColor = vec4(base.rgb * light, base.a);
}
