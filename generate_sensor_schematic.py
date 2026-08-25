#!/usr/bin/env python3
"""Generate clean 2D schematic of two sensors on a conveyor belt."""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Publication-quality style
plt.rcParams.update({
    'figure.figsize': (12, 4.5),
    'font.size': 13,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans'],
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
})

fig, ax = plt.subplots(figsize=(12, 4.5))

# ============================================================
# Conveyor belt - clean 2D
# ============================================================
belt_x = 0.5
belt_y = 0.3
belt_w = 10.0
belt_h = 0.6

# Belt top surface
ax.add_patch(patches.Rectangle((belt_x, belt_y + belt_h/2), belt_w, belt_h/2,
                                facecolor='#2c3e50', edgecolor='#1a252f', linewidth=1.5, zorder=1))

# Belt side (thickness)
ax.add_patch(patches.Rectangle((belt_x, belt_y), belt_w, belt_h/2,
                                facecolor='#34495e', edgecolor='#1a252f', linewidth=1.5, zorder=1))

# Belt rollers
roller_y = belt_y
for rx in [belt_x + 0.3, belt_x + belt_w - 0.3]:
    roller = patches.Circle((rx, roller_y + belt_h/4), 0.12,
                            facecolor='#7f8c8d', edgecolor='#5d6d7e', linewidth=1.5, zorder=2)
    ax.add_patch(roller)
    # Roller axle
    ax.add_patch(patches.Circle((rx, roller_y + belt_h/4), 0.03,
                                facecolor='#2c3e50', edgecolor='none', zorder=3))

# Belt direction arrows
for ax_pos in [belt_x + 1.5, belt_x + 4.0, belt_x + 6.5, belt_x + 9.0]:
    ax.annotate('', xy=(ax_pos + 0.5, belt_y + 0.6), xytext=(ax_pos, belt_y + 0.6),
                arrowprops=dict(arrowstyle='->', lw=3, color='#2ecc71', alpha=1.0), zorder=4)

ax.text(belt_x + belt_w/2, belt_y + 0.75, 'Belt direction  $\\bar{v}$',
        ha='center', va='bottom', fontsize=14, color='#2ecc71', fontweight='bold', zorder=5,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#555555', edgecolor='none', alpha=0.9))

# ============================================================
# Sensor A (upstream) - overhead mounting
# ============================================================
sensor_a_x = 2.5
sensor_mount_y = belt_y + belt_h + 0.15
sensor_head_h = 0.35
sensor_head_w = 0.5

# Mounting post
ax.add_patch(patches.Rectangle((sensor_a_x - 0.04, belt_y + belt_h), 0.08, 0.8,
                                facecolor='#7f8c8d', edgecolor='#5d6d7e', linewidth=1, zorder=3))

# Cross beam
ax.add_patch(patches.Rectangle((sensor_a_x - 0.6, sensor_mount_y + 0.7), 1.2, 0.06,
                                facecolor='#7f8c8d', edgecolor='#5d6d7e', linewidth=1, zorder=3))

# Sensor head housing
sensor_head_y = sensor_mount_y + 0.7
head_rect = patches.FancyBboxPatch((sensor_a_x - sensor_head_w/2, sensor_head_y),
                                    sensor_head_w, sensor_head_h,
                                    boxstyle="round,pad=0.02",
                                    facecolor='#2980b9', edgecolor='#1a5276', linewidth=1.5, zorder=5)
ax.add_patch(head_rect)

# Sensor lens/emitter
ax.add_patch(patches.Ellipse((sensor_a_x, sensor_head_y + sensor_head_h/2), 0.25, 0.12,
                              facecolor='#1a5276', edgecolor='#154360', linewidth=1, zorder=6))

# Sensor A label
ax.text(sensor_a_x, sensor_head_y + sensor_head_h + 0.15, 'Sensor A',
        ha='center', va='bottom', fontsize=14, fontweight='bold', color='#1a5276', zorder=10)

# Measurement beam (dashed lines to belt)
beam_y_start = sensor_head_y
beam_y_end = belt_y + belt_h/2
# Beam edges
ax.plot([sensor_a_x - 0.12, sensor_a_x - 0.25], [beam_y_start, beam_y_end],
        'k--', alpha=0.4, linewidth=1.2, zorder=2)
ax.plot([sensor_a_x + 0.12, sensor_a_x + 0.25], [beam_y_start, beam_y_end],
        'k--', alpha=0.4, linewidth=1.2, zorder=2)
# Beam center
ax.plot([sensor_a_x, sensor_a_x], [beam_y_start, beam_y_end],
        'k:', alpha=0.3, linewidth=0.8, zorder=2)

# Measurement spot on belt
spot = patches.Ellipse((sensor_a_x, belt_y + belt_h/2 + 0.02), 0.2, 0.08,
                        facecolor='#3498db', edgecolor='#2980b9', linewidth=1.5, alpha=0.9, zorder=4)
ax.add_patch(spot)

# ============================================================
# Sensor B (downstream)
# ============================================================
sensor_b_x = 8.0
sensor_mount_y_b = belt_y + belt_h + 0.15

# Mounting post
ax.add_patch(patches.Rectangle((sensor_b_x - 0.04, belt_y + belt_h), 0.08, 0.8,
                                facecolor='#7f8c8d', edgecolor='#5d6d7e', linewidth=1, zorder=3))

# Cross beam
ax.add_patch(patches.Rectangle((sensor_b_x - 0.6, sensor_mount_y_b + 0.7), 1.2, 0.06,
                                facecolor='#7f8c8d', edgecolor='#5d6d7e', linewidth=1, zorder=3))

# Sensor head housing
sensor_head_y_b = sensor_mount_y_b + 0.7
head_rect_b = patches.FancyBboxPatch((sensor_b_x - sensor_head_w/2, sensor_head_y_b),
                                      sensor_head_w, sensor_head_h,
                                      boxstyle="round,pad=0.02",
                                      facecolor='#c0392b', edgecolor='#7b241c', linewidth=1.5, zorder=5)
ax.add_patch(head_rect_b)

# Sensor lens/emitter
ax.add_patch(patches.Ellipse((sensor_b_x, sensor_head_y_b + sensor_head_h/2), 0.25, 0.12,
                              facecolor='#7b241c', edgecolor='#4a140c', linewidth=1, zorder=6))

# Sensor B label
ax.text(sensor_b_x, sensor_head_y_b + sensor_head_h + 0.15, 'Sensor B',
        ha='center', va='bottom', fontsize=14, fontweight='bold', color='#7b241c', zorder=10)

# Measurement beam
ax.plot([sensor_b_x - 0.12, sensor_b_x - 0.25], [sensor_head_y_b, beam_y_end],
        'k--', alpha=0.4, linewidth=1.2, zorder=2)
ax.plot([sensor_b_x + 0.12, sensor_b_x + 0.25], [sensor_head_y_b, beam_y_end],
        'k--', alpha=0.4, linewidth=1.2, zorder=2)
ax.plot([sensor_b_x, sensor_b_x], [sensor_head_y_b, beam_y_end],
        'k:', alpha=0.3, linewidth=0.8, zorder=2)

# Measurement spot on belt
spot_b = patches.Ellipse((sensor_b_x, belt_y + belt_h/2 + 0.02), 0.2, 0.08,
                          facecolor='#e74c3c', edgecolor='#c0392b', linewidth=1.5, alpha=0.9, zorder=4)
ax.add_patch(spot_b)

# ============================================================
# Distance L between sensors - clear dimension line with arrows (FOREGROUND)
# ============================================================
# Position dimension line well within axis limits (y < 2.2)
arrow_y_top = sensor_head_y + sensor_head_h - 0.15

# Extension lines (vertical lines from sensors up to dimension line)
ext_line_x_a = sensor_a_x
ext_line_x_b = sensor_b_x
ext_bottom = sensor_head_y + sensor_head_h + 0.08
ext_top = arrow_y_top

# Extension line for Sensor A - HIGH ZORDER
ax.plot([ext_line_x_a, ext_line_x_a], [ext_bottom, ext_top],
        'k-', linewidth=2.5, zorder=100)
# Extension line for Sensor B - HIGH ZORDER
ax.plot([ext_line_x_b, ext_line_x_b], [ext_bottom, ext_top],
        'k-', linewidth=2.5, zorder=100)

# Dimension line (horizontal) - solid black line - HIGHEST ZORDER
ax.plot([ext_line_x_a, ext_line_x_b], [arrow_y_top, arrow_y_top],
        'k-', linewidth=2, zorder=101)

# Arrowheads - filled black triangles for maximum visibility - HIGHEST ZORDER
arrow_size = 0.18
arrow_thickness = 0.07

# Left arrowhead (pointing right) - filled polygon
left_arrow = np.array([
    [ext_line_x_a, arrow_y_top],
    [ext_line_x_a + arrow_size, arrow_y_top + arrow_thickness],
    [ext_line_x_a + arrow_size, arrow_y_top - arrow_thickness]
])
ax.fill(left_arrow[:, 0], left_arrow[:, 1], 'k', zorder=102)

# Right arrowhead (pointing left) - filled polygon
right_arrow = np.array([
    [ext_line_x_b, arrow_y_top],
    [ext_line_x_b - arrow_size, arrow_y_top + arrow_thickness],
    [ext_line_x_b - arrow_size, arrow_y_top - arrow_thickness]
])
ax.fill(right_arrow[:, 0], right_arrow[:, 1], 'k', zorder=102)

# Dimension value
ax.text((sensor_a_x + sensor_b_x)/2, arrow_y_top + 0.08, '$L$',
        ha='center', va='bottom', fontsize=18, fontweight='bold', zorder=103)

# Small ticks at ends of dimension line
tick_h = 0.05
ax.plot([ext_line_x_a, ext_line_x_a], [arrow_y_top - tick_h, arrow_y_top + tick_h],
        'k-', linewidth=2.5, zorder=101)
ax.plot([ext_line_x_b, ext_line_x_b], [arrow_y_top - tick_h, arrow_y_top + tick_h],
        'k-', linewidth=2.5, zorder=101)

# ============================================================
# Material on belt
# ============================================================
np.random.seed(42)
for i in range(8):
    mx = belt_x + 0.6 + i * 1.15 + np.random.uniform(-0.08, 0.08)
    my = belt_y + belt_h/2 + 0.05 + np.random.uniform(-0.03, 0.03)
    mw, mh = 0.45, 0.12
    # Material piece with slight 3D look
    ax.add_patch(patches.Rectangle((mx - mw/2, my), mw, mh,
                                    facecolor='#8b7355', edgecolor='#5d4e37', linewidth=1, zorder=2))
    ax.add_patch(patches.Rectangle((mx - mw/2, my + mh), mw, 0.03,
                                    facecolor='#a08a6a', edgecolor='#5d4e37', linewidth=0.5, zorder=2))

# ============================================================
# Formula box
# ============================================================
ax.text(0.3, -0.15,
        '$\\tau_{\\mathrm{phys}} = \\dfrac{L}{\\bar{v}}$',
        fontsize=15, ha='left', va='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8f9fa', edgecolor='#dee2e6', linewidth=1.2),
        zorder=10)

# ============================================================
# Frame around conveyor
# ============================================================
frame = patches.Rectangle((belt_x - 0.1, belt_y - 0.05), belt_w + 0.2, belt_h + 0.1,
                           fill=False, edgecolor='#95a5a6', linewidth=1.5, linestyle='--', zorder=0)
ax.add_patch(frame)

# ============================================================
# Clean up
# ============================================================
ax.set_xlim(0, 10.8)
ax.set_ylim(-0.5, 2.2)
ax.set_aspect('equal')
ax.axis('off')

plt.tight_layout()
plt.savefig('/Users/david/Documents/CESGA/synch_paper/figures/sensor_schematic.png',
            dpi=300, bbox_inches='tight', pad_inches=0.1, facecolor='white')
plt.close()
print('Saved: sensor_schematic.png')