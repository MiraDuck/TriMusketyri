#version 330

// Nausea: the scene, from a render texture. It bends in slow waves (less in the middle, so what you aim at stays put)
// and a second, fainter copy drifts away from it (double vision).

in vec2 fragTexCoord;

uniform sampler2D texture0;
uniform float time;
uniform float amount;   // 0..1, how sick you are
uniform float warp;     // how far it bends at full sickness, of the screen
uniform float ghosting; // how far the second image drifts apart at full sickness, of the screen

out vec4 finalColor;

void main()
{
    vec2 centre = fragTexCoord - 0.5;
    float edge = 0.3 + 0.7 * min(dot(centre, centre) * 2.0, 1.0);   // 0.3 in the middle, 1 in the corners
    vec2 bend = vec2(sin(fragTexCoord.y * 7.0 + time * 1.3), cos(fragTexCoord.x * 5.0 + time * 0.9));
    vec2 uv = fragTexCoord + bend * warp * amount * edge;
    vec2 apart = vec2(sin(time * 0.8), cos(time * 0.53)) * ghosting * amount;
    vec3 scene = texture(texture0, uv).rgb;
    vec3 ghost = texture(texture0, uv + apart).rgb;
    finalColor = vec4(mix(scene, ghost, 0.4 * min(amount * 2.0, 1.0)), 1.0);
}
