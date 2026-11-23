import pygame
import math

WIDTH, HEIGHT = 1000, 750
SAFE_MATH = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
SAFE_MATH["abs"] = abs


def project_4d(x, y, z, w, ang, zoom=1.0):
    planes = [(0, 1, ang[0]), (0, 2, ang[1]), (0, 3, ang[2]), (1, 3, ang[3]), (2, 3, ang[4])]
    v = [x, y, z, w]
    for a, b, theta in planes:
        c, s = math.cos(theta), math.sin(theta)
        v[a], v[b] = v[a] * c - v[b] * s, v[a] * s + v[b] * c
    f4 = 2.2 / max(0.2, 3.5 - v[3])
    x3, y3, z3 = v[0] * f4, v[1] * f4, v[2] * f4
    f3 = (220.0 * zoom) / max(0.2, 5.0 - z3)
    return (WIDTH // 2 + x3 * f3, HEIGHT // 2 - y3 * f3, w)


def w_color(w):
    t = max(0.0, min(1.0, (w + 1.5) / 3.0))
    return (int(40 + 215 * t), int(220 - 150 * abs(t - 0.5) * 2), int(255 - 215 * t))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("4D Graphing Calculator | w = f(x, y, z)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 16)

    presets = [
        "sin(x*2 + z) * cos(y*2 - z)",
        "cos(sqrt(x*x + y*y + z*z) * 3)",
        "(x*x - y*y) * cos(z)",
        "exp(-(x*x + y*y + z*z)) * 1.5",
    ]
    p_idx, expr = 0, presets[0]
    fn, err = None, ""

    def compile_fn(txt):
        nonlocal fn, err
        try:
            code = compile(txt, "<expr>", "eval")
            float(eval(code, {"__builtins__": {}}, {**SAFE_MATH, "x": 0.1, "y": 0.1, "z": 0.1}))
            fn, err = code, ""
        except Exception as e:
            err = f"Error: {str(e)[:45]}"

    compile_fn(expr)
    angles, z_slice, z_time, anim_z = [0.4, 0.5, 0.3, 0.2, 0.0], 0.0, 0.0, True
    dragging, typing, last_m = False, False, (0, 0)
    res, dom, zoom = 18, 1.5, 1.0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.MOUSEWHEEL:
                if ev.y > 0:
                    zoom = min(5.0, zoom * (1.1 ** ev.y))
                elif ev.y < 0:
                    zoom = max(0.2, zoom / (1.1 ** abs(ev.y)))
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                typing = 20 <= ev.pos[0] <= 620 and 15 <= ev.pos[1] <= 50
                dragging = not typing
                last_m = ev.pos
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                dragging = False
            elif ev.type == pygame.MOUSEMOTION and dragging:
                dx, dy = ev.pos[0] - last_m[0], ev.pos[1] - last_m[1]
                last_m = ev.pos
                shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
                angles[2 if shift else 0] += dx * 0.008
                angles[3 if shift else 1] += dy * 0.008
            elif ev.type == pygame.KEYDOWN:
                if typing:
                    if ev.key == pygame.K_RETURN:
                        compile_fn(expr)
                        typing = False
                    elif ev.key == pygame.K_BACKSPACE:
                        expr = expr[:-1]
                    elif ev.unicode.isprintable():
                        expr += ev.unicode
                else:
                    if ev.key == pygame.K_SPACE:
                        anim_z = not anim_z
                    elif ev.key == pygame.K_TAB:
                        p_idx = (p_idx + 1) % len(presets)
                        expr = presets[p_idx]
                        compile_fn(expr)
                    elif ev.key == pygame.K_r:
                        angles, z_slice, zoom = [0.4, 0.5, 0.3, 0.2, 0.0], 0.0, 1.0

        keys = pygame.key.get_pressed()
        if not typing:
            if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
                anim_z = False
                z_slice = max(-dom, min(dom, z_slice + (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 1.2 * dt))
            if keys[pygame.K_EQUALS] or keys[pygame.K_KP_PLUS]:
                zoom = min(5.0, zoom * (1.0 + 1.5 * dt))
            if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
                zoom = max(0.2, zoom / (1.0 + 1.5 * dt))
            angles[2] += (keys[pygame.K_e] - keys[pygame.K_q]) * 1.2 * dt
            angles[3] += (keys[pygame.K_d] - keys[pygame.K_a]) * 1.2 * dt

        if anim_z:
            z_time += dt * 1.4
            z_slice = math.sin(z_time) * dom

        screen.fill((15, 18, 25))
        if fn:
            step = (2 * dom) / (res - 1)
            env = {**SAFE_MATH, "z": z_slice}
            grid = []
            for i in range(res):
                row = []
                env["x"] = -dom + i * step
                for j in range(res):
                    env["y"] = -dom + j * step
                    try:
                        w = max(-3.0, min(3.0, float(eval(fn, {"__builtins__": {}}, env))))
                    except Exception:
                        w = 0.0
                    row.append(project_4d(env["x"], env["y"], z_slice, w, angles, zoom))
                grid.append(row)

            for i in range(res):
                for j in range(res):
                    p = grid[i][j]
                    col = w_color(p[2])
                    if i + 1 < res:
                        pygame.draw.line(screen, col, p[:2], grid[i + 1][j][:2], 2)
                    if j + 1 < res:
                        pygame.draw.line(screen, col, p[:2], grid[i][j + 1][:2], 2)

        axes = [((1.6, 0, 0, 0), (255, 90, 90), "X"), ((0, 1.6, 0, 0), (90, 255, 120), "Y"),
                ((0, 0, 1.6, 0), (90, 160, 255), "Z"), ((0, 0, 0, 1.6), (255, 220, 80), "W")]
        origin = project_4d(0, 0, 0, 0, angles, zoom)[:2]
        for vec, col, lbl in axes:
            end = project_4d(*vec, angles, zoom)[:2]
            pygame.draw.line(screen, col, origin, end, 2)
            screen.blit(font.render(lbl, True, col), (end[0] + 5, end[1] - 5))

        pygame.draw.rect(screen, (25, 30, 42), (20, 15, 600, 35), border_radius=5)
        pygame.draw.rect(screen, (100, 200, 255) if typing else (80, 90, 115), (20, 15, 600, 35), 2, border_radius=5)
        screen.blit(font.render(f"w = {expr}" + ("|" if typing else ""), True, (230, 235, 245)), (28, 24))
        if err:
            screen.blit(font.render(err, True, (255, 100, 100)), (25, 56))

        hud = [
            f"Z-Slice: {z_slice:+.2f} ({'Anim' if anim_z else 'Manual'}) | Zoom: {zoom:.2f}x | XW:{angles[2]:.2f} YW:{angles[3]:.2f}",
            "[Click Box] Edit w=f(x,y,z) + ENTER | [TAB] Presets | [SPACE] Toggle Z-Anim",
            "[Drag] 3D Rotate | [Shift+Drag / Q,E,A,D] 4D Rotate | [Scroll / +,-] Zoom | [Left/Right] Z-Slice | [R] Reset",
        ]
        for idx, line in enumerate(hud):
            screen.blit(font.render(line, True, (175, 185, 205)), (20, HEIGHT - 75 + idx * 22))

        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()