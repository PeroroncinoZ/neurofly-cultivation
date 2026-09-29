# Read-only FlyWire SWC viewer

The viewer reads the eight selected neurons directly from `brain/morphology/`.
The old JSON loader is removed. Each filename is `<FlyWire_root_id>.swc`;
`SELECTED_NEURONS` in `visualization_3d.py` assigns neuron type and side labels.
Add mapping entries and corresponding SWC exports to extend the selection.

```sh
# Live activity, separate viewer process:
.venv/bin/python main.py --visualize-3d
# Validate files and print per-neuron node/segment/skipped-row counts:
.venv/bin/python -m brain.visualization_3d --validate
# Standalone morphology inspection, no simulated activation:
.venv/bin/python -m brain.visualization_3d
# Override the directory with --skeleton-dir /path/to/swc in either command.
```

Left mouse drag rotates; mouse wheel zooms; R resets. Closing the viewer does not
stop the simulation. Activation changes line brightness and width. Colors and
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

## Isolation and performance

Only copied activation scalars cross a bounded, nonblocking queue into the spawned
viewer process (up to 20 Hz). No graph/state reference or control channel is given
to the viewer. All morphology file access is read-only. Pygame software rendering
uses orthographic 3D projection; it has no mesh/depth occlusion or atlas overlay.
The current exports contain roughly one million nodes, so viewer frame rate may
be substantially below its 30 Hz cap. All segments are retained. The simulation
never waits for rendering or activation delivery. No neural behavior is modified.

## Optional anatomical context

The viewer now supports a faint gray whole-brain wireframe from
`brain/morphology/context/brain.obj`. No mesh is bundled or synthesized. Missing
or malformed context is shown as unavailable/disabled; skeletons continue normally.
See [the context format contract](morphology/context/README.md) for OBJ records,
coordinate registration, and provenance requirements. B toggles context and L
 toggles neuron labels; rotation, zoom, reset, and activation rendering are unchanged.
Context shares the skeleton camera transform and is drawn behind the neurons.
