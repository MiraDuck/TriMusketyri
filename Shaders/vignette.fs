#version 330

// Vignette: drawn as a full-screen rectangle over the 3D scene. Transparent in the middle, the rectangle's colour
// towards the edges. Its alpha is the strength, so the colour and strength can change every frame.

in vec4 fragColor;

uniform vec2 resolution;   // framebuffer size in pixels
uniform float radius;      // distance from the centre where darkening starts (0.5 = edge midpoints)
uniform float softness;    // how far beyond `radius` it takes to reach full strength

out vec4 finalColor;

void main()
{
    // -0.5..0.5 across the screen on both axes, so the vignette follows the screen's shape (an ellipse);
    // the corners are at about 0.71
    vec2 uv = gl_FragCoord.xy / resolution - 0.5;
    float amount = smoothstep(radius, radius + softness, length(uv));
    finalColor = vec4(fragColor.rgb, fragColor.a * amount);
}
