import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.collections as mcoll
import numpy as np

passed = 0
failed = 0

# Test 1: scatter relim after set_offsets
fig, ax = plt.subplots()
scatter = ax.scatter([], [])
xs = np.linspace(0, 10, 100)
ys = np.sin(xs)
scatter.set_offsets(np.column_stack((xs, ys)))
ax.relim()
ax.autoscale_view()
ok = ax.get_xlim()[1] > 5 and abs(ax.get_ylim()[0]) > 0.5
print(f'Test 1 - scatter relim: {"PASS" if ok else "FAIL"} xlim={ax.get_xlim()}')
passed += ok; failed += (not ok)

# Test 2: line still works
fig2, ax2 = plt.subplots()
line, = ax2.plot([], [])
line.set_data(xs, ys)
ax2.relim()
ax2.autoscale_view()
ok = ax2.get_xlim()[1] > 5
print(f'Test 2 - line relim: {"PASS" if ok else "FAIL"} xlim={ax2.get_xlim()}')
passed += ok; failed += (not ok)

# Test 3: visible_only with invisible scatter
fig3, ax3 = plt.subplots()
scatter3 = ax3.scatter(xs, ys)
scatter3.set_visible(False)
ax3.relim(visible_only=True)
ax3.autoscale_view()
# When all artists are invisible, relim resets to null bbox, autoscale gives margins around 0
# This is expected behavior - not (0,1) default
ok = ax3.get_xlim()[1] < 1  # just verify it didn't pick up the scatter data
print(f'Test 3 - invisible scatter excluded: {"PASS" if ok else "FAIL"} xlim={ax3.get_xlim()}')
passed += ok; failed += (not ok)

# Test 4: mixed line + scatter
fig4, ax4 = plt.subplots()
ax4.plot([0, 5], [0, 5])
scatter4 = ax4.scatter([], [])
scatter4.set_offsets([[10, 10], [20, 20]])
ax4.relim()
ax4.autoscale_view()
ok = ax4.get_xlim()[1] > 15
print(f'Test 4 - mixed: {"PASS" if ok else "FAIL"} xlim={ax4.get_xlim()}')
passed += ok; failed += (not ok)

# Test 5: scatter with initial data, then relim
fig5, ax5 = plt.subplots()
scatter5 = ax5.scatter([1, 2], [3, 4])
scatter5.set_offsets([[100, 200], [300, 400]])
ax5.relim()
ax5.autoscale_view()
ok = ax5.get_xlim()[1] > 200
print(f'Test 5 - scatter replace data: {"PASS" if ok else "FAIL"} xlim={ax5.get_xlim()}')
passed += ok; failed += (not ok)

# Test 6: _in_autoscale is set on scatter
fig6, ax6 = plt.subplots()
s6 = ax6.scatter([1], [1])
ok = s6._get_in_autoscale()
print(f'Test 6 - _in_autoscale set: {"PASS" if ok else "FAIL"}')
passed += ok; failed += (not ok)

print(f'\n{passed}/{passed+failed} passed')
