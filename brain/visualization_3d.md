# Read-only FlyWire SWC viewer

The viewer reads the eight selected neurons directly from `brain/morphology/`.
The old JSON loader is removed. Each filename is `<FlyWire_root_id>.swc`;
`SELECTED_NEURONS` in `visualization_3d.py` assigns neuron type and side labels.
Add mapping entries and corresponding SWC exports to extend the selection.

```sh
# Combined simulation and live brain panel (default):
.venv/bin/python main.py
# Simulation with disabled brain rendering:
.venv/bin/python main.py --no-brain
# Validate files and print per-neuron node/segment/skipped-row counts:
.venv/bin/python -m brain.visualization_3d --validate
# Standalone morphology inspection, no simulated activation:
.venv/bin/python -m brain.visualization_3d
# Override the directory with --skeleton-dir /path/to/swc in either command.
```

With the cursor over the brain panel, left mouse drag rotates, the mouse wheel
zooms, and R resets. B toggles context and L toggles labels. In standalone mode,
closing the viewer does not stop another simulation. Activation changes line brightness and width. Colors and
legend labels identify neuron type and side. No missing morphology is invented.

## SWC interpretation

Whitespace-delimited rows: `node_id type x y z radius parent_id`.
Blank lines and `#` comments are ignored. IDs/types/parent IDs are integers;
coordinates and radius are finite numbers. Node IDs are positive and unique;
radius is nonnegative. `parent_id = -1` marks a root. Every other parent creates
a node-to-parent line segment. Parent rows may appear later in the file.
Multiple roots/disconnected components are supported.

Coordinates are preserved exactly as parsed floating-point values. Radius and
node type are retained as metadata; line width represents activation rather
than anatomical radius. No resampling, invented positions, or inferred edges
are used. A shared display centering/scale transform preserves relative geometry.
SWC does not universally specify units or registration. The supplied export
headers say `1 nanometer`; additional files must use matching units and a common
coordinate frame. The viewer does not convert or register exports automatically.

Malformed rows (wrong field count, duplicate ID, invalid numbers, negative radius,
invalid/self parent) are skipped with line-number warnings. Nodes whose parents
are missing remain loaded but their unresolved segments are omitted and reported
separately. Missing, unreadable, or empty files do not prevent other neurons from
loading. The legend displays warning counts. `validate_morphology()` returns all
warnings as well as printing a bounded report. Filename selection supplies neuron
identity; the loader cannot authenticate the export's biological identity.

## Embedded rendering architecture

The main Pygame window is 1648×960: an unchanged 800×600 arena on the left,
an 800×600 brain panel on the right, with padded section headers, a compact
neuron legend, and a status bar below. Presentation mode is the default. Press
D to toggle grouped detailed metrics, or P to return to presentation mode.
`ui.py` owns layout and read-only text; embedded rendering omits its standalone
text overlays so scenes stay unobstructed. The standalone viewer keeps its labels.
Arena collision, spawning and wall avoidance still receive 800×600 dimensions.

`brain/embedded_viewer.py` starts a spawned off-screen rendering worker. The worker
loads the real SWCs/context and draws on a regular Pygame Surface, without calling
`display.set_mode` or opening a native window. It uses the same rendering code
as the standalone viewer. All segments and activation styling are retained.

The main loop sends copied activation scalars and absolute camera/toggle settings
through a bounded nonblocking queue at up to 25 Hz. Completed RGB frames cross a
shared-memory buffer. A nonblocking lock protects the buffer; the main loop skips
busy frames, converts completed bytes to a Pygame surface, and retains the last
frame while the renderer works. No graph or mutable neural state is shared. Camera
commands affect only presentation, never simulation. Shutdown joins/terminates
only the renderer owned by this application.

The worker targets 25 FPS, but roughly one million skeleton nodes plus the context
mesh can render much slower with software drawing. No 20–30 FPS guarantee is made
for these exports. Rendering and morphology loading never run in the simulation
loop; pixel copying/blitting still has a small main-thread cost and both processes
share machine resources. No synchronous render waits are introduced.

Startup failure, renderer exit, or worker rendering errors show an unavailable
message while simulation continues. `--no-brain` disables the worker entirely.
`--visualize-3d` remains a compatibility alias for the default embedded panel.
The standalone command remains `python -m brain.visualization_3d`.

## Optional anatomical context

The viewer now supports a faint gray whole-brain wireframe from
`brain/morphology/context/brain.obj`. No mesh is bundled or synthesized. Missing
or malformed context is shown as unavailable/disabled; skeletons continue normally.
See [the context format contract](morphology/context/README.md) for OBJ records,
coordinate registration, and provenance requirements. B toggles context and L
 toggles neuron labels; rotation, zoom, reset, and activation rendering are unchanged.
Context shares the skeleton camera transform and is drawn behind the neurons.
