from __future__ import annotations

from dataclasses import dataclass
from collections import deque


@dataclass
class RendererConfig:
    width: int = 1000
    height: int = 700
    fps: int = 60
    animation_seconds: float = 2.0
    score_history_max_points: int = 240


class ContainerDepotPygameRenderer:
    def __init__(self, title: str, config: RendererConfig | None = None):
        try:
            import pygame
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Missing dependency 'pygame'. Install with: pip install pygame"
            ) from exc

        self.pygame = pygame
        self.config = config or RendererConfig()
        self.pygame.init()
        self.screen = self.pygame.display.set_mode((self.config.width, self.config.height))
        self.pygame.display.set_caption(title)
        self.clock = self.pygame.time.Clock()
        self.running = True
        self._pending_keys: list[int] = []
        self.score_history = deque(maxlen=self.config.score_history_max_points)
        self._last_score_key = None
        # Waypoints of the current action: list of (start, end, carrying)
        self._action_segments: list[tuple[tuple[float, float], tuple[float, float], bool]] = []
        # Last placed/moved container: (container_id, cell) — highlighted on board
        self._last_placed: tuple[int, tuple[int, int]] | None = None

        self.font = self.pygame.font.SysFont("consolas", 18)
        self.small_font = self.pygame.font.SysFont("consolas", 14)
        self.tiny_font = self.pygame.font.SysFont("consolas", 12)

        self.bg_color = (18, 18, 24)
        self.bg_color_2 = (28, 28, 38)
        self.grid_color = (75, 75, 90)
        self.text_color = (235, 235, 245)
        self.pending_color = (250, 210, 90)
        self.crane_color = (220, 70, 70)
        self.crane_path_color = (160, 190, 255)
        self.crane_carry_color = (255, 180, 60)
        self.highlight_source = (100, 190, 255)
        self.highlight_target = (120, 255, 150)
        self.hud_panel = (32, 34, 48)
        self.board_panel = (22, 24, 35)
        self.pending_outline = (255, 220, 110)
        self.last_placed_glow = (255, 100, 220)

    def close(self) -> None:
        if self.running:
            self.running = False
            self.pygame.quit()

    def _color_for_container(self, container_id: int) -> tuple[int, int, int]:
        if container_id <= 0:
            return (45, 45, 52)
        r = 70 + (container_id * 53) % 160
        g = 70 + (container_id * 97) % 160
        b = 70 + (container_id * 131) % 160
        return (r, g, b)

    def _pump_events(self) -> bool:
        for event in self.pygame.event.get():
            if event.type == self.pygame.QUIT:
                self.close()
                return False
            if event.type == self.pygame.KEYDOWN:
                self._pending_keys.append(event.key)
        return self.running

    def poll_interaction_command(self, timeout_ms: int = 0) -> str | None:
        pygame = self.pygame
        start_ticks = pygame.time.get_ticks()
        while self.running:
            if not self._pump_events():
                return "quit"

            if self._pending_keys:
                key = self._pending_keys.pop(0)
                if key in (pygame.K_ESCAPE, pygame.K_q):
                    return "quit"
                if key in (pygame.K_SPACE, pygame.K_n, pygame.K_RIGHT):
                    return "step"
                if key in (pygame.K_LEFT, pygame.K_b):
                    return "back"
                if key == pygame.K_a:
                    return "toggle_auto"
                if key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    return "faster"
                if key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    return "slower"
                if key == pygame.K_HOME:
                    return "first"
                if key == pygame.K_END:
                    return "last"

            if timeout_ms <= 0:
                return None
            if pygame.time.get_ticks() - start_ticks >= timeout_ms:
                return None
            self.clock.tick(max(30, min(120, self.config.fps)))

        return "quit"

    def _draw_wrapped_text(
        self,
        text: str,
        *,
        x: int,
        y: int,
        max_width: int,
        max_lines: int,
        color: tuple[int, int, int],
        font,
        line_spacing: int = 2,
    ) -> int:
        words = text.split()
        if not words:
            return y

        lines = []
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if font.size(trial)[0] <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)

        if len(lines) > max_lines:
            lines = lines[:max_lines]
            last = lines[-1]
            ellipsis = "..."
            while last and font.size(last + ellipsis)[0] > max_width:
                last = last[:-1]
            lines[-1] = (last + ellipsis) if last else ellipsis

        line_h = font.get_linesize() + line_spacing
        for index, line in enumerate(lines):
            self.screen.blit(font.render(line, True, color), (x, y + index * line_h))

        return y + len(lines) * line_h

    def _cell_rect(self, simulation, row: int, col: int):
        board_h = simulation.board_height
        board_w = simulation.board_width

        margin_x = 30
        margin_y = 100
        side_panel = 240
        grid_w = self.config.width - 2 * margin_x - side_panel
        grid_h = self.config.height - margin_y - 40

        cell_w = max(20, grid_w // max(1, board_w))
        cell_h = max(20, grid_h // max(1, board_h))

        x = margin_x + col * cell_w
        y = margin_y + row * cell_h
        return self.pygame.Rect(x, y, cell_w, cell_h)

    def _cell_center(self, simulation, cell: tuple[int, int]) -> tuple[float, float]:
        row, col = cell
        rect = self._cell_rect(simulation, row, col)
        return (rect.centerx, rect.centery)

    @staticmethod
    def _ease_in_out(t: float) -> float:
        if t <= 0.0:
            return 0.0
        if t >= 1.0:
            return 1.0
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def _interpolate(p0: tuple[float, float], p1: tuple[float, float], t: float):
        return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)

    def _draw_background(self):
        pygame = self.pygame
        h = self.config.height
        w = self.config.width
        for y in range(h):
            blend = y / max(1, h - 1)
            color = (
                int(self.bg_color[0] + (self.bg_color_2[0] - self.bg_color[0]) * blend),
                int(self.bg_color[1] + (self.bg_color_2[1] - self.bg_color[1]) * blend),
                int(self.bg_color[2] + (self.bg_color_2[2] - self.bg_color[2]) * blend),
            )
            pygame.draw.line(self.screen, color, (0, y), (w, y))

    def _draw_hud(self, simulation, status_text: str, last_action: dict | None):
        pygame = self.pygame
        top_rect = pygame.Rect(15, 10, self.config.width - 30, 98)
        pygame.draw.rect(self.screen, self.hud_panel, top_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.grid_color, top_rect, 1, border_radius=8)

        header = (
            f"crane={simulation.crane_position} pending={simulation.containers_to_extract_id} "
            f"time={simulation.time} epochs={simulation.epochs}"
        )
        self._draw_wrapped_text(
            header,
            x=28,
            y=18,
            max_width=top_rect.width - 26,
            max_lines=1,
            color=self.text_color,
            font=self.font,
        )
        current_y = self._draw_wrapped_text(
            status_text,
            x=28,
            y=42,
            max_width=top_rect.width - 26,
            max_lines=2,
            color=self.pending_color,
            font=self.small_font,
        )
        if last_action is not None:
            self._draw_wrapped_text(
                f"last_action={last_action}",
                x=28,
                y=current_y,
                max_width=top_rect.width - 26,
                max_lines=1,
                color=self.text_color,
                font=self.tiny_font,
            )

    def _draw_side_panel(self, simulation):
        pygame = self.pygame
        panel_w = 220
        panel_rect = pygame.Rect(self.config.width - panel_w - 20, 100, panel_w, self.config.height - 140)
        pygame.draw.rect(self.screen, self.hud_panel, panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.grid_color, panel_rect, 1, border_radius=8)

        lines = [
            "Legend",
            "",
            "Blue border: source",
            "Green border: target",
            "Gold border: pending",
            "Pink glow: last moved",
            "Blue line: crane empty",
            "Orange line: carrying",
            "",
            f"Board: {simulation.board_height}x{simulation.board_width}x{simulation.board_length}",
            f"Crane: {simulation.crane_position}",
            f"Pending count: {len(simulation.containers_to_extract_id)}",
        ]
        y = panel_rect.top + 12
        for text in lines:
            font = self.small_font if text != "Legend" else self.font
            color = self.pending_color if text == "Legend" else self.text_color
            self.screen.blit(font.render(text, True, color), (panel_rect.left + 10, y))
            y += 20

        graph_rect = pygame.Rect(panel_rect.left + 10, panel_rect.bottom - 130, panel_rect.width - 20, 110)
        pygame.draw.rect(self.screen, (25, 27, 38), graph_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.grid_color, graph_rect, 1, border_radius=6)
        self.screen.blit(self.small_font.render("Score timeline", True, self.pending_color), (graph_rect.left + 8, graph_rect.top + 6))
        self._draw_score_graph(graph_rect)

    def _register_score(self, simulation):
        key = (simulation.time, simulation.epochs)
        if key == self._last_score_key:
            return
        self._last_score_key = key
        self.score_history.append(simulation.time + simulation.epochs)

    def _draw_score_graph(self, graph_rect):
        pygame = self.pygame
        if len(self.score_history) < 2:
            hint = self.tiny_font.render("Need more steps...", True, (160, 165, 178))
            self.screen.blit(hint, (graph_rect.left + 8, graph_rect.top + 45))
            return

        min_score = min(self.score_history)
        max_score = max(self.score_history)
        span = max(1.0, float(max_score - min_score))

        left = graph_rect.left + 8
        right = graph_rect.right - 8
        top = graph_rect.top + 26
        bottom = graph_rect.bottom - 10
        width = max(1, right - left)
        height = max(1, bottom - top)

        points = []
        count = len(self.score_history)
        for index, score in enumerate(self.score_history):
            x = left + (index / max(1, count - 1)) * width
            y_norm = (float(score) - min_score) / span
            y = bottom - y_norm * height
            points.append((int(x), int(y)))

        pygame.draw.line(self.screen, (70, 78, 98), (left, bottom), (right, bottom), 1)
        pygame.draw.lines(self.screen, (118, 228, 255), False, points, 2)
        pygame.draw.circle(self.screen, (245, 245, 255), points[-1], 3)

        current = self.score_history[-1]
        label = self.tiny_font.render(f"min={min_score} max={max_score} now={current}", True, self.text_color)
        self.screen.blit(label, (left, graph_rect.top + 10))

    def _draw_action_path(self):
        """Draw segments of the current action path.

        Empty-crane segments: thin blue line.
        Carrying segments: thick orange line.
        """
        pygame = self.pygame
        segments = self._action_segments
        if not segments:
            return
        for start, end, carrying in segments:
            color = self.crane_carry_color if carrying else self.crane_path_color
            thickness = 3 if carrying else 2
            pygame.draw.line(
                self.screen,
                color,
                (int(start[0]), int(start[1])),
                (int(end[0]), int(end[1])),
                thickness,
            )
            # Dot at start
            pygame.draw.circle(self.screen, color, (int(start[0]), int(start[1])), 4)
        # Dot at final end
        if segments:
            last_end = segments[-1][1]
            last_color = self.crane_carry_color if segments[-1][2] else self.crane_path_color
            pygame.draw.circle(self.screen, last_color, (int(last_end[0]), int(last_end[1])), 4)

    def _draw_crane(
        self,
        simulation,
        crane_cell: tuple[float, float] | tuple[int, int],
        carried_container_id: int | None = None,
    ):
        pygame = self.pygame
        if isinstance(crane_cell[0], float):
            crane_x, crane_y = crane_cell
        else:
            crane_x, crane_y = self._cell_center(simulation, crane_cell)

        self._draw_action_path()

        # Draw only the moving crane head (no rail, no red top marker).
        hook_rect = pygame.Rect(int(crane_x) - 8, int(crane_y) - 8, 16, 16)
        hook_shadow = hook_rect.move(1, 1)
        pygame.draw.rect(self.screen, (20, 20, 26), hook_shadow, border_radius=4)
        pygame.draw.rect(self.screen, (230, 230, 240), hook_rect, border_radius=4)
        pygame.draw.rect(self.screen, self.crane_path_color, hook_rect, 2, border_radius=4)

        # Draw carried container attached to the hook — larger & more visible
        if carried_container_id is not None and carried_container_id > 0:
            cw, ch = 44, 20
            container_rect = pygame.Rect(
                int(crane_x) - cw // 2,
                int(crane_y) + 6,
                cw,
                ch,
            )
            # Glow behind
            glow_rect = container_rect.inflate(6, 6)
            pygame.draw.rect(self.screen, (255, 255, 255, 80), glow_rect, border_radius=5)
            shadow = container_rect.move(2, 2)
            pygame.draw.rect(self.screen, (10, 10, 14), shadow, border_radius=4)
            pygame.draw.rect(
                self.screen,
                self._color_for_container(carried_container_id),
                container_rect,
                border_radius=4,
            )
            pygame.draw.rect(self.screen, (255, 255, 255), container_rect, 2, border_radius=4)
            label = self.small_font.render(str(carried_container_id), True, (255, 255, 255))
            lx = container_rect.centerx - label.get_width() // 2
            ly = container_rect.centery - label.get_height() // 2
            self.screen.blit(label, (lx, ly))

    def _draw_board(
        self,
        simulation,
        crane_cell: tuple[float, float] | tuple[int, int],
        status_text: str,
        last_action: dict | None,
        source_cell: tuple[int, int] | None = None,
        target_cell: tuple[int, int] | None = None,
        carried_container_id: int | None = None,
        hide_top_at: tuple[int, int] | None = None,
    ) -> bool:
        if not self._pump_events():
            return False

        pygame = self.pygame
        self._register_score(simulation)
        self._draw_background()
        self._draw_hud(simulation, status_text, last_action)
        self._draw_side_panel(simulation)

        board_frame = pygame.Rect(20, 95, self.config.width - 280, self.config.height - 130)
        pygame.draw.rect(self.screen, self.board_panel, board_frame, border_radius=8)
        pygame.draw.rect(self.screen, self.grid_color, board_frame, 1, border_radius=8)

        pending_set = set(simulation.containers_to_extract_id)
        top_pending = simulation.containers_to_extract_id[0] if simulation.containers_to_extract_id else None

        for row in range(simulation.board_height):
            for col in range(simulation.board_width):
                rect = self._cell_rect(simulation, row, col)
                border_color = self.grid_color
                if source_cell == (row, col):
                    border_color = self.highlight_source
                if target_cell == (row, col):
                    border_color = self.highlight_target
                pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=6)
                self.screen.blit(
                    self.tiny_font.render(f"{row},{col}", True, (150, 155, 170)),
                    (rect.left + 4, rect.top + 2),
                )

                stack_size = simulation.board_size_cell[row][col]
                max_levels = simulation.board_length
                level_h = max(6, rect.height // max(1, max_levels + 1))

                # If hide_top_at matches this cell, skip the top container
                # (it's visually "on the crane")
                draw_count = stack_size
                if hide_top_at == (row, col) and stack_size > 0:
                    draw_count = stack_size - 1

                for level in range(draw_count):
                    container_id = simulation.board[row][col][level]
                    level_rect = pygame.Rect(
                        rect.left + 5,
                        rect.bottom - (level + 1) * level_h - 4,
                        rect.width - 10,
                        level_h - 3,
                    )
                    shadow_rect = level_rect.move(1, 1)
                    pygame.draw.rect(self.screen, (20, 20, 24), shadow_rect, border_radius=3)
                    pygame.draw.rect(
                        self.screen,
                        self._color_for_container(container_id),
                        level_rect,
                        border_radius=3,
                    )
                    if container_id in pending_set:
                        outline = self.pending_outline if container_id == top_pending else self.pending_color
                        pygame.draw.rect(self.screen, outline, level_rect, 1, border_radius=3)

                    # Highlight last placed/moved container with a glow
                    if (
                        self._last_placed is not None
                        and self._last_placed == (container_id, (row, col))
                    ):
                        glow = level_rect.inflate(4, 4)
                        pygame.draw.rect(self.screen, self.last_placed_glow, glow, 2, border_radius=4)

                    label = self.tiny_font.render(str(container_id), True, (8, 8, 10))
                    self.screen.blit(label, (level_rect.left + 3, level_rect.top + 1))

        self._draw_crane(simulation, crane_cell, carried_container_id=carried_container_id)

        pygame.display.flip()
        self.clock.tick(self.config.fps)
        return True

    def render(
        self,
        simulation,
        *,
        status_text: str = "",
        last_action: dict | None = None,
    ) -> bool:
        # Clear action path so old segments don't persist
        self._action_segments = []
        return self._draw_board(
            simulation,
            simulation.crane_position,
            status_text=status_text,
            last_action=last_action,
        )

    @staticmethod
    def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _top_container_id(self, simulation, cell: tuple[int, int]) -> int:
        """Return the id of the top container in *cell*, or 0 if empty."""
        row, col = cell
        size = simulation.board_size_cell[row][col]
        if size <= 0:
            return 0
        return simulation.board[row][col][size - 1]

    def animate_action(self, simulation, action: dict | None, *, status_text: str) -> bool:
        if action is None:
            self._action_segments = []
            return self.render(simulation, status_text=status_text, last_action=None)

        action_type = action.get("type")
        source_cell = action.get("source_cell")
        target_cell = action.get("target_cell")
        start_cell = simulation.crane_position

        if action_type == 1 and source_cell is not None and target_cell is not None:
            # Distribute frames proportionally to manhattan distance of each leg
            dist_to_source = max(1, self._manhattan(start_cell, source_cell))
            dist_source_target = max(1, self._manhattan(source_cell, target_cell))
            total_dist = dist_to_source + dist_source_target
            total_frames = max(12, int(self.config.animation_seconds * self.config.fps))
            first = max(4, int(total_frames * dist_to_source / total_dist))
            second = max(4, total_frames - first)

            start_xy = self._cell_center(simulation, start_cell)
            source_xy = self._cell_center(simulation, source_cell)
            target_xy = self._cell_center(simulation, target_cell)

            container_id = self._top_container_id(simulation, source_cell)

            # Set segments for the action path:
            #  leg 1: crane → source (empty), leg 2: source → target (carrying)
            self._action_segments = [
                (start_xy, source_xy, False),
                (source_xy, target_xy, True),
            ]

            # Phase 1: crane moves to source (no container yet)
            for frame in range(first):
                t = self._ease_in_out((frame + 1) / first)
                pos = self._interpolate(start_xy, source_xy, t)
                if not self._draw_board(
                    simulation,
                    pos,
                    status_text=f"{status_text} [crane → source {source_cell}]",
                    last_action=action,
                    source_cell=source_cell,
                    target_cell=target_cell,
                ):
                    return False

            # Phase 2: crane carries container from source to target
            for frame in range(second):
                t = self._ease_in_out((frame + 1) / second)
                pos = self._interpolate(source_xy, target_xy, t)
                if not self._draw_board(
                    simulation,
                    pos,
                    status_text=f"{status_text} [carrying #{container_id} → {target_cell}]",
                    last_action=action,
                    source_cell=source_cell,
                    target_cell=target_cell,
                    carried_container_id=container_id,
                    hide_top_at=source_cell,
                ):
                    return False

            # Remember the last placed container for highlight
            self._last_placed = (container_id, target_cell)
            return True

        if action_type == 2 and source_cell is not None:
            total_frames = max(8, int(self.config.animation_seconds * self.config.fps))
            travel_frames = max(6, total_frames)
            pickup_frames = max(4, total_frames // 4)

            container_id = self._top_container_id(simulation, source_cell)

            start_xy = self._cell_center(simulation, start_cell)
            source_xy = self._cell_center(simulation, source_cell)

            # Set segments for the action path: crane → source (empty)
            self._action_segments = [
                (start_xy, source_xy, False),
            ]

            # Phase 1: crane moves to source
            for frame in range(travel_frames):
                t = self._ease_in_out((frame + 1) / travel_frames)
                pos = self._interpolate(start_xy, source_xy, t)
                if not self._draw_board(
                    simulation,
                    pos,
                    status_text=f"{status_text} [crane → extract {source_cell}]",
                    last_action=action,
                    source_cell=source_cell,
                ):
                    return False

            # Phase 2: crane lifts container from source (visual pickup)
            lift_top = source_xy[1]
            lift_end = source_xy[1] - 30
            for frame in range(pickup_frames):
                t = self._ease_in_out((frame + 1) / pickup_frames)
                pos = (source_xy[0], lift_top + (lift_end - lift_top) * t)
                if not self._draw_board(
                    simulation,
                    pos,
                    status_text=f"{status_text} [extracting #{container_id}]",
                    last_action=action,
                    source_cell=source_cell,
                    carried_container_id=container_id,
                    hide_top_at=source_cell,
                ):
                    return False

            # Extracted container is gone — clear last-placed
            self._last_placed = None
            return True

        self._action_segments = []
        return self.render(simulation, status_text=status_text, last_action=action)
