import math
import pyray as pr


# =========================================================
# Vertex shader: CEL SHADING
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

out vec3 fragPosition;
out vec3 fragNormal;
out vec2 fragTexCoord;
out vec4 fragColor;

void main()
{
    vec4 worldPosition = matModel * vec4(vertexPosition, 1.0);

    fragPosition = worldPosition.xyz;
    fragNormal = normalize(
        (matNormal * vec4(vertexNormal, 0.0)).xyz
    );

    fragTexCoord = vertexTexCoord;
    fragColor = vertexColor;

    gl_Position = mvp * vec4(vertexPosition, 1.0);
}
"""


# =========================================================
# Fragment shader: CEL SHADING
# =========================================================

CEL_FRAGMENT_SHADER = """
#version 330

in vec3 fragPosition;
in vec3 fragNormal;
in vec2 fragTexCoord;
in vec4 fragColor;

uniform sampler2D texture0;
uniform vec4 colDiffuse;

uniform vec3 lightPos;
uniform float numBands;

out vec4 finalColor;

void main()
{
    // Surface normal
    vec3 normal = normalize(fragNormal);

    // Direction from surface to light
    vec3 lightDirection = normalize(lightPos - fragPosition);

    // Diffuse lighting
    float diffuse = max(dot(normal, lightDirection), 0.1);

    // Convert smooth lighting into distinct bands
    float bands = max(numBands, 2.0);
    float toon = floor(diffuse * bands) / (bands - 1.0);

    // Ambient light prevents the shadows from becoming completely black
    float lighting = 0.30 + 0.80 * toon;

    // Model texture and color
    vec4 texel = texture(texture0, fragTexCoord);
    vec4 baseColor = texel * colDiffuse * fragColor;

    finalColor = vec4(baseColor.rgb * lighting, baseColor.a);
}
"""


# =========================================================
# Vertex shader: BLACK OUTLINE
# =========================================================

OUTLINE_VERTEX_SHADER = """
#version 330

in vec3 vertexPosition;
in vec3 vertexNormal;

uniform mat4 mvp;
uniform float outlineThickness;

void main()
{
    // Expand the model along its normals
    vec3 expandedPosition =
        vertexPosition + vertexNormal * outlineThickness;

    gl_Position = mvp * vec4(expandedPosition, 1.0);
}
"""


# =========================================================
# Fragment shader: BLACK OUTLINE
# =========================================================

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
    "Cel Shading - Pyray"
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

# Built-in sphere, so no external model is needed
# model = pr.load_model_from_mesh(
#     pr.gen_mesh_cone(1.5, 3, 32)
# )

model = pr.load_model("Models/Bed.obj")

# Move the sphere upward slightly
MODEL_POSITION = pr.Vector3(0.0, 1, 0.0)


# =========================================================
# LOAD SHADERS
# =========================================================

cel_shader = pr.load_shader_from_memory(
    CEL_VERTEX_SHADER,
    CEL_FRAGMENT_SHADER
)

outline_shader = pr.load_shader_from_memory(
    OUTLINE_VERTEX_SHADER,
    OUTLINE_FRAGMENT_SHADER
)

# Save the original shader for every material
default_shaders = [
    model.materials[i].shader
    for i in range(model.materialCount)
]

# Apply cel shader to every material
for i in range(model.materialCount):
    model.materials[i].shader = cel_shader


# Shader uniform locations
light_pos_loc = pr.get_shader_location(
    cel_shader, "lightPos"
)

num_bands_loc = pr.get_shader_location(
    cel_shader, "numBands"
)

outline_thickness_loc = pr.get_shader_location(
    outline_shader, "outlineThickness"
)


# =========================================================
# SETTINGS
# =========================================================

cel_enabled = True
outline_enabled = True

num_bands = 5.0
outline_thickness = 0.025

LIGHT_HEIGHT = 5.0
LIGHT_RADIUS = 5.0
LIGHT_SPEED = 2


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

    # Toggle cel shading
    if pr.is_key_pressed(pr.KeyboardKey.KEY_Z):
        cel_enabled = not cel_enabled

    # Toggle outline
    if pr.is_key_pressed(pr.KeyboardKey.KEY_C):
        outline_enabled = not outline_enabled

    # Change number of shading bands
    if pr.is_key_pressed(pr.KeyboardKey.KEY_Q):
        num_bands = max(2.0, num_bands - 1.0)

    if pr.is_key_pressed(pr.KeyboardKey.KEY_E):
        num_bands = min(20.0, num_bands + 1.0)

    if cel_enabled:
        for i in range(model.materialCount):
            model.materials[i].shader = cel_shader
    else:
        for i in range(model.materialCount):
            model.materials[i].shader = default_shaders[i]

    # -----------------------------------------------------
    # MOVING LIGHT
    # -----------------------------------------------------

    t = pr.get_time()

    light_x = math.sin(t * LIGHT_SPEED) * LIGHT_RADIUS
    light_z = math.cos(t * LIGHT_SPEED) * LIGHT_RADIUS

    light_position = pr.Vector3(
        light_x,
        LIGHT_HEIGHT,
        light_z
    )

    # Send light position to the shader
    light_pos_data = pr.ffi.new(
        "float[3]",
        [light_x, LIGHT_HEIGHT, light_z]
    )

    pr.set_shader_value(
        cel_shader,
        light_pos_loc,
        light_pos_data,
        pr.ShaderUniformDataType.SHADER_UNIFORM_VEC3
    )

    # Send number of bands to the shader
    num_bands_data = pr.ffi.new("float *", num_bands)

    pr.set_shader_value(
        cel_shader,
        num_bands_loc,
        num_bands_data,
        pr.ShaderUniformDataType.SHADER_UNIFORM_FLOAT
    )

    # Set outline thickness
    thickness_data = pr.ffi.new("float *", outline_thickness)

    pr.set_shader_value(
        outline_shader,
        outline_thickness_loc,
        thickness_data,
        pr.ShaderUniformDataType.SHADER_UNIFORM_FLOAT
    )

    # -----------------------------------------------------
    # DRAWING
    # -----------------------------------------------------

    pr.begin_drawing()
    pr.clear_background(pr.RAYWHITE)

    pr.begin_mode_3d(camera)

    # Draw outline
    if outline_enabled:
        pr.rl_set_cull_face(pr.RL_CULL_FACE_FRONT)

        # Apply outline shader to every material
        for i in range(model.materialCount):
            model.materials[i].shader = outline_shader

        pr.draw_model(
            model,
            MODEL_POSITION,
            1.0,
            pr.WHITE
        )

        # Restore the appropriate shader for each material
        for i in range(model.materialCount):
            if cel_enabled:
                model.materials[i].shader = cel_shader
            else:
                model.materials[i].shader = default_shaders[i]

        pr.rl_set_cull_face(pr.RL_CULL_FACE_BACK)

    # Draw the actual model
    pr.draw_model(
        model,
        MODEL_POSITION,
        1.0,
        pr.WHITE
    )

    # Draw the light indicator
    pr.draw_sphere(
        light_position,
        0.15,
        pr.YELLOW
    )

    # Draw ground grid
    pr.draw_grid(20, 1.0)

    pr.end_mode_3d()

    # -----------------------------------------------------
    # UI
    # -----------------------------------------------------

    pr.draw_fps(10, 10)

    cel_text = "ON" if cel_enabled else "OFF"
    outline_text = "ON" if outline_enabled else "OFF"

    pr.draw_text(
        f"Cel shading: {cel_text} [Z]",
        10, 40, 20, pr.DARKGRAY
    )

    pr.draw_text(
        f"Outline: {outline_text} [C]",
        10, 70, 20, pr.DARKGRAY
    )

    pr.draw_text(
        f"Bands: {int(num_bands)} [Q/E]",
        10, 100, 20, pr.DARKGRAY
    )

    pr.end_drawing()


# =========================================================
# CLEANUP
# =========================================================

pr.unload_model(model)
pr.unload_shader(cel_shader)
pr.unload_shader(outline_shader)

pr.close_window()