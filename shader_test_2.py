import math
import pyray as pr


# =========================================================
# SHADER 1: BAKE CEL-SHADED LIGHTING
# =========================================================

# This shader renders the model into UV space instead of
# rendering it from the camera's perspective.
#
# Each texel stores the lighting for a part of the model.

BAKE_VERTEX_SHADER = """
#version 330

in vec3 vertexPosition;
in vec2 vertexTexCoord;
in vec3 vertexNormal;

uniform mat4 matModel;
uniform mat4 matNormal;

out vec3 fragPosition;
out vec3 fragNormal;

void main()
{
    // Position and normal in world space
    fragPosition = (matModel * vec4(vertexPosition, 1.0)).xyz;

    fragNormal = normalize(
        (matNormal * vec4(vertexNormal, 0.0)).xyz
    );

    // Render the triangle in UV space
    gl_Position = vec4(
        vertexTexCoord.x * 2.0 - 1.0,
        vertexTexCoord.y * 2.0 - 1.0,
        0.0,
        1.0
    );
}
"""


BAKE_FRAGMENT_SHADER = """
#version 330

in vec3 fragPosition;
in vec3 fragNormal;

uniform vec3 lightPos;
uniform float numBands;

out vec4 finalColor;

void main()
{
    vec3 normal = normalize(fragNormal);

    // Direction toward the stationary light
    vec3 lightDirection = normalize(lightPos - fragPosition);

    // Calculate diffuse brightness
    float diffuse = max(dot(normal, lightDirection), 0.0);

    // Convert brightness into discrete cel-shading bands
    float bands = max(numBands, 2.0);

    float toon = floor(
        diffuse * (bands - 1.0) + 0.0001
    ) / (bands - 1.0);

    // Include ambient lighting in the baked result
    float lighting = 0.30 + 0.70 * toon;

    // Store lighting in RGB
    finalColor = vec4(
        lighting,
        lighting,
        lighting,
        1.0
    );
}
"""


# =========================================================
# SHADER 2: NORMAL RENDERING WITH BAKED LIGHTING
# =========================================================

CEL_VERTEX_SHADER = """
#version 330

in vec3 vertexPosition;
in vec2 vertexTexCoord;
in vec3 vertexNormal;
in vec4 vertexColor;

uniform mat4 mvp;
uniform mat4 matModel;
uniform mat4 matNormal;

out vec2 fragTexCoord;
out vec4 fragColor;

void main()
{
    fragTexCoord = vertexTexCoord;
    fragColor = vertexColor;

    gl_Position = mvp * vec4(vertexPosition, 1.0);
}
"""


CEL_FRAGMENT_SHADER = """
#version 330

in vec2 fragTexCoord;
in vec4 fragColor;

uniform sampler2D texture0;
uniform sampler2D lightmap;
uniform vec4 colDiffuse;

out vec4 finalColor;

void main()
{
    // Original material texture
    vec4 texel = texture(texture0, fragTexCoord);
    vec4 baseColor = texel * colDiffuse * fragColor;

    // Lighting calculated once during startup
    vec3 bakedLighting = texture(
        lightmap,
        fragTexCoord
    ).rgb;

    // Apply the baked lighting to the original texture
    finalColor = vec4(
        baseColor.rgb * bakedLighting,
        baseColor.a
    );
}
"""


# =========================================================
# SHADER 3: BLACK OUTLINE
# =========================================================

OUTLINE_VERTEX_SHADER = """
#version 330

in vec3 vertexPosition;
in vec3 vertexNormal;

uniform mat4 mvp;
uniform float outlineThickness;

void main()
{
    vec3 expandedPosition =
        vertexPosition + vertexNormal * outlineThickness;

    gl_Position = mvp * vec4(expandedPosition, 1.0);
}
"""


OUTLINE_FRAGMENT_SHADER = """
#version 330

out vec4 finalColor;

void main()
{
    finalColor = vec4(0.02, 0.02, 0.02, 1.0);
}
"""


# =========================================================
# INITIALIZATION
# =========================================================

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700

pr.init_window(
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    "Baked Cel Shading"
)

pr.set_target_fps(60)

camera = pr.Camera3D(
    pr.Vector3(7.0, 5.0, 7.0),
    pr.Vector3(0.0, 2.0, 0.0),
    pr.Vector3(0.0, 1.0, 0.0),
    45.0,
    pr.CAMERA_PERSPECTIVE
)


# =========================================================
# MODEL
# =========================================================

model = pr.load_model("Models/Bed.obj")

MODEL_POSITION = pr.Vector3(0.0, 1.0, 0.0)

if not pr.is_model_valid(model):
    raise RuntimeError("Failed to load Models/Bed.obj")


# =========================================================
# STATIONARY LIGHT
# =========================================================

LIGHT_POSITION = pr.Vector3(5.0, 5.0, 5.0)

NUM_BANDS = 5.0

# The lightmap resolution
LIGHTMAP_SIZE = 1024


# =========================================================
# LOAD SHADERS
# =========================================================

bake_shader = pr.load_shader_from_memory(
    BAKE_VERTEX_SHADER,
    BAKE_FRAGMENT_SHADER
)

cel_shader = pr.load_shader_from_memory(
    CEL_VERTEX_SHADER,
    CEL_FRAGMENT_SHADER
)

outline_shader = pr.load_shader_from_memory(
    OUTLINE_VERTEX_SHADER,
    OUTLINE_FRAGMENT_SHADER
)


# Check that shaders compiled successfully
if bake_shader.id == 0:
    raise RuntimeError("Failed to load bake shader")

if cel_shader.id == 0:
    raise RuntimeError("Failed to load cel shader")

if outline_shader.id == 0:
    raise RuntimeError("Failed to load outline shader")


# =========================================================
# SAVE ORIGINAL MATERIAL SHADERS
# =========================================================

default_shaders = [
    model.materials[i].shader
    for i in range(model.materialCount)
]


# =========================================================
# CREATE LIGHTMAP
# =========================================================

lightmap_target = pr.load_render_texture(
    LIGHTMAP_SIZE,
    LIGHTMAP_SIZE
)

if lightmap_target.id == 0:
    raise RuntimeError("Failed to create lightmap render texture")


# Uniform locations
bake_light_loc = pr.get_shader_location(
    bake_shader,
    "lightPos"
)

bake_bands_loc = pr.get_shader_location(
    bake_shader,
    "numBands"
)


# Send the stationary light position
light_data = pr.ffi.new(
    "float[3]",
    [
        LIGHT_POSITION.x,
        LIGHT_POSITION.y,
        LIGHT_POSITION.z
    ]
)

pr.set_shader_value(
    bake_shader,
    bake_light_loc,
    light_data,
    pr.ShaderUniformDataType.SHADER_UNIFORM_VEC3
)


# Send the number of bands
bands_data = pr.ffi.new(
    "float *",
    NUM_BANDS
)

pr.set_shader_value(
    bake_shader,
    bake_bands_loc,
    bands_data,
    pr.ShaderUniformDataType.SHADER_UNIFORM_FLOAT
)


# ---------------------------------------------------------
# Bake lighting ONCE
# ---------------------------------------------------------

print("Baking lighting...")

# Assign the bake shader to every material
for i in range(model.materialCount):
    model.materials[i].shader = bake_shader


pr.begin_texture_mode(lightmap_target)

pr.clear_background(pr.BLACK)

# Disable depth testing because the triangles are rendered
# into UV space, where all triangles have the same depth.
pr.rl_disable_depth_test()

pr.draw_model(
    model,
    MODEL_POSITION,
    1.0,
    pr.WHITE
)

pr.rl_enable_depth_test()

pr.end_texture_mode()


# Restore the original shaders
for i in range(model.materialCount):
    model.materials[i].shader = default_shaders[i]

print("Lighting bake complete!")


# =========================================================
# CONNECT LIGHTMAP TO CEL SHADER
# =========================================================

lightmap_loc = pr.get_shader_location(
    cel_shader,
    "lightmap"
)

# Assign the baked texture to the shader's sampler.
# It is not the same as the model's original texture0.
pr.set_shader_value_texture(
    cel_shader,
    lightmap_loc,
    lightmap_target.texture
)


# =========================================================
# OUTLINE SETTINGS
# =========================================================

outline_thickness = 0.025

outline_thickness_loc = pr.get_shader_location(
    outline_shader,
    "outlineThickness"
)

thickness_data = pr.ffi.new(
    "float *",
    outline_thickness
)

pr.set_shader_value(
    outline_shader,
    outline_thickness_loc,
    thickness_data,
    pr.ShaderUniformDataType.SHADER_UNIFORM_FLOAT
)


# =========================================================
# SETTINGS
# =========================================================

cel_enabled = True
outline_enabled = True


# =========================================================
# MAIN LOOP
# =========================================================

while not pr.window_should_close():

    # -----------------------------------------------------
    # CAMERA
    # -----------------------------------------------------

    pr.update_camera(
        camera,
        pr.CAMERA_ORBITAL
    )


    # -----------------------------------------------------
    # CONTROLS
    # -----------------------------------------------------

    if pr.is_key_pressed(pr.KeyboardKey.KEY_Z):
        cel_enabled = not cel_enabled

    if pr.is_key_pressed(pr.KeyboardKey.KEY_C):
        outline_enabled = not outline_enabled


    # -----------------------------------------------------
    # DRAWING
    # -----------------------------------------------------

    pr.begin_drawing()

    pr.clear_background(pr.RAYWHITE)

    pr.begin_mode_3d(camera)


    # Draw outline
    if outline_enabled:

        pr.rl_set_cull_face(pr.RL_CULL_FACE_FRONT)

        for i in range(model.materialCount):
            model.materials[i].shader = outline_shader

        pr.draw_model(
            model,
            MODEL_POSITION,
            1.0,
            pr.WHITE
        )

        pr.rl_set_cull_face(pr.RL_CULL_FACE_BACK)


    # Draw model with baked lighting or original shaders
    for i in range(model.materialCount):

        if cel_enabled:
            model.materials[i].shader = cel_shader
        else:
            model.materials[i].shader = default_shaders[i]


    pr.draw_model(
        model,
        MODEL_POSITION,
        1.0,
        pr.WHITE
    )


    # Stationary light indicator
    pr.draw_sphere(
        LIGHT_POSITION,
        0.15,
        pr.YELLOW
    )

    pr.draw_grid(20, 1.0)

    pr.end_mode_3d()


    # -----------------------------------------------------
    # UI
    # -----------------------------------------------------

    pr.draw_fps(10, 10)

    pr.draw_text(
        f"Baked cel shading: {'ON' if cel_enabled else 'OFF'} [Z]",
        10, 40, 20, pr.DARKGRAY
    )

    pr.draw_text(
        f"Outline: {'ON' if outline_enabled else 'OFF'} [C]",
        10, 70, 20, pr.DARKGRAY
    )

    pr.draw_text(
        "Lighting is baked at startup",
        10, 100, 20, pr.DARKGRAY
    )

    pr.end_drawing()


# =========================================================
# CLEANUP
# =========================================================

pr.unload_render_texture(lightmap_target)

pr.unload_model(model)

pr.unload_shader(bake_shader)
pr.unload_shader(cel_shader)
pr.unload_shader(outline_shader)

pr.close_window()