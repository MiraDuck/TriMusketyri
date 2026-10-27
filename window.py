import pyray as pr

screenWidth = 800
screenHeight = 450

pr.init_window(screenWidth, screenHeight, "raylib [core] example - basic window")
pr.set_target_fps(60)

while not pr.window_should_close():
    pr.begin_drawing()
    pr.clear_background(pr.RAYWHITE)
    pr.draw_text("Congrats! You created your first window!", 190, 200, 20, pr.LIGHTGRAY)
    pr.end_drawing()

pr.close_window()