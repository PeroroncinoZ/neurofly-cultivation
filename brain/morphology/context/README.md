# Optional whole-brain context

Place a real, registered mesh or outline at `brain.obj` in this directory.
No anatomical context asset is currently supplied; nothing is generated in its absence.

Supported format: UTF-8 Wavefront OBJ, with `v x y z` vertices and polygon `f`
faces or polyline `l` records. Faces become wireframe perimeter edges; shared
edges are drawn once. Positive 1-based and negative relative vertex indices are
supported, including `v/vt/vn` face references. Declare vertices before using them.
Materials, normals, texture coordinates, groups and other records are ignored.
No textures or external material files are read. Homogeneous/color vertex
extensions are unsupported. Malformed geometry disables the optional layer.

Coordinates must already use the SAME units, origin, orientation and registration
as the SWCs (current exports: nanometers). The viewer applies their shared camera
transform only; it does not infer alignment or convert units. Record your actual
export source/version and any transforms alongside the mesh. A filename alone
cannot establish anatomical provenance. A modest-resolution mesh is recommended
for this software wireframe renderer.

B toggles context; L toggles neuron labels. Context is gray at alpha 40/255 and
is composited BEFORE neurons, keeping activity colors prominent. Configure color
and alpha using CONTEXT_COLOR in brain/visualization_context.py.

If --skeleton-dir is overridden, context is loaded from that directory's
context/brain.obj. Restart the viewer after adding/replacing the file.
