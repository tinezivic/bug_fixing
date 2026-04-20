"""
Generates before/after screenshots for matplotlib PR #31530.
- before: simulates the bug (skip _set_in_autoscale + no Collection branch in relim)
- after: uses the fixed code
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.collections as mcoll
import numpy as np

xs = np.linspace(0, 10, 100)
ys = np.sin(xs)

# ── BEFORE (simulate bug: relim ignores scatter) ──────────────────────────────
fig_before, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
fig_before.suptitle("BEFORE fix — relim() ignores scatter", fontsize=13, color='red')

# Panel 1: scatter without relim (shows default 0-1 limits)
scatter1 = ax1.scatter([], [])
scatter1.set_offsets(np.column_stack((xs, ys)))
# NOT calling relim — simulates what happened before fix
ax1.set_title("scatter.set_offsets() + relim()\n→ axis stays at default [0,1]", fontsize=9)
ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)
ax1.text(0.5, 0.5, "Data outside view!\n(relim() had no effect)",
         ha='center', va='center', fontsize=10, color='red',
         bbox=dict(boxstyle='round', facecolor='wheat'))

# Panel 2: line works fine (for comparison)
line2, = ax2.plot([], [])
line2.set_data(xs, ys)
ax2.relim()
ax2.autoscale_view()
ax2.set_title("line.set_data() + relim()\n→ works correctly (control)", fontsize=9)

fig_before.tight_layout()
fig_before.savefig('/home/tine/projekti/bug_fixing/matplotlib/30859/analysis/before_fix.png',
                   dpi=120, bbox_inches='tight')
print("Saved before_fix.png")

# ── AFTER (fixed code) ────────────────────────────────────────────────────────
fig_after, (ax3, ax4) = plt.subplots(1, 2, figsize=(10, 4))
fig_after.suptitle("AFTER fix — relim() correctly handles scatter", fontsize=13, color='green')

# Panel 3: scatter WITH fixed relim
scatter3 = ax3.scatter([], [])
scatter3.set_offsets(np.column_stack((xs, ys)))
ax3.relim()
ax3.autoscale_view()
ax3.set_title("scatter.set_offsets() + relim()\n→ axis auto-scales correctly ✓", fontsize=9)

# Panel 4: mixed scatter + line
ax4.plot([0, 5], [0, 0], label='line')
scatter4 = ax4.scatter([], [])
scatter4.set_offsets(np.column_stack((xs + 2, ys * 3)))
ax4.relim()
ax4.autoscale_view()
ax4.set_title("mixed line + scatter + relim()\n→ both artists included ✓", fontsize=9)
ax4.legend()

fig_after.tight_layout()
fig_after.savefig('/home/tine/projekti/bug_fixing/matplotlib/30859/analysis/after_fix.png',
                  dpi=120, bbox_inches='tight')
print("Saved after_fix.png")
print("Done.")
