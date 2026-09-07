// Side Brush Clearance Jig
// Verifies the 5-arm side brush clears the chassis and bumper.
// Prints a thin profile of the brush sweep area.

brush_radius = 105/2;  // mm (estimate)
hub_radius   =  28/2;  // mm (estimate)
thickness    =   1;     // mm — thin template

$fn = 48;

module jig() {
    // Outer sweep ring (thin disc)
    difference() {
        circle(r=brush_radius);
        circle(r=hub_radius);
    }
}

// Extrude to thin template
linear_extrude(height=thickness)
    jig();
