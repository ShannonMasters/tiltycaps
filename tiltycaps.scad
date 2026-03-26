/* [Preset Selection] */

// SA-inspired row variant applied to the default low-profile shell.
row = "R3"; // [R1, R2, R3, R4, Thumb]

// Keycap outer footprint spacing, independent of the stem family.
outer_family = "mx"; // [mx, choc]

// Native Choc stem, or a replacement MX stem mount.
stem_family = "choc_v1"; // [choc_v1, mx]

// View the cap in its normal typing orientation or in the print pose.
render_mode = "print"; // [typing, print]

/* [Shape Tuning] */

// Match the compact low-profile height, or use the taller shell.
low_profile = true;

// Additive geometry tilt applied on top of the row preset.
overall_tilt_deg = 0; // [-10:1:10]

/* [Homing] */

// Optional homing marker added to the top saddle.
homing_type = "None"; // [None, Dot, 2 dots, 3 dots, Circle, Line]

// Front/back homing offset on the saddle. 0 keeps it centered on the key.
homing_offset_y_mm = 0; // [-4:0.1:4]

// Overall scale multiplier for the homing feature.
homing_scale = 1.0; // [0.5:0.05:2.0]

/* [Print Setup] */

// Intended print angle used by render_mode="print".
print_angle_deg = print_lip_angle_deg(row, low_profile, outer_family); // [30:1:60]

/* [Stem Fit] */

// MX stem clearance tolerance used only when stem_family="mx".
clearance_mm = default_clearance_mm(); // [0.05:0.01:0.4]


function clamp(v, lo, hi) = min(max(v, lo), hi);
function lerp(a, b, t) = a + (b - a) * t;
function v2_add(a, b) = [a[0] + b[0], a[1] + b[1]];
function v2_sub(a, b) = [a[0] - b[0], a[1] - b[1]];

module rounded_rect(size = [10, 10], radius = 1, center = true) {
    r = min(radius, min(size[0], size[1]) / 2 - 0.01);
    offset(r = r)
        offset(delta = -r)
            square(size, center = center);
}

module wafer(size = [10, 10], radius = 1, z = 0, thickness = 0.18) {
    translate([0, 0, z])
        linear_extrude(height = thickness, center = true)
            rounded_rect(size = size, radius = radius, center = true);
}

module slope_box(size = [10, 3, 1], angle_deg = 45) {
    rotate([-angle_deg, 0, 0])
        cube(size, center = false);
}

module ellipsoid(scale_xyz = [1, 1, 1]) {
    scale(scale_xyz)
        sphere(r = 1, $fn = 48);
}


function default_wall_mm() = 1.2;
function default_roof_mm() = 1.2;
function default_clearance_mm() = 0.18;

function row_base_tilt_deg(row) =
    row == "R1" ? -20 :
    row == "R2" ? -12 :
    row == "R3" ? 0 :
    row == "R4" ? 14 :
    row == "Thumb" ? -17 : 0;

function row_height_bias_mm(row) =
    row == "R1" ? 0.6 :
    row == "R2" ? 0.25 :
    row == "R3" ? 0 :
    row == "R4" ? 0.35 :
    row == "Thumb" ? 0.15 : 0;

function row_sculpt_bias(row) =
    row == "R1" ? 0.92 :
    row == "R2" ? 1.0 :
    row == "R3" ? 1.0 :
    row == "R4" ? 0.95 :
    row == "Thumb" ? 0.85 : 1.0;

function family_pitch_mm(family) = family == "choc" ? 18.0 : 19.05;
function family_base_width_1u_mm(family) = family == "choc" ? 17.5 : 18.0;
function family_base_depth_mm(family) = family == "choc" ? 16.5 : 18.0;
function family_top_width_trim_mm(family) = family == "choc" ? 1.3 : 1.6;
function family_top_depth_trim_mm(family) = family == "choc" ? 1.6 : 1.8;
function family_corner_radius_mm(family) = family == "choc" ? 2.1 : 2.4;
function family_bottom_chamfer_mm(stem_family) = stem_family == "choc_v1" ? 1.2 : 1.4;

function base_cap_width_mm(width_u, outer_family) =
    family_base_width_1u_mm(outer_family) + max(0, width_u - 1) * family_pitch_mm(outer_family);

function base_cap_depth_mm(outer_family) = family_base_depth_mm(outer_family);

function cap_height_mm(row, low_profile, outer_family) =
    (low_profile ? (outer_family == "choc" ? 5.2 : 5.0) : (outer_family == "choc" ? 6.3 : 6.0))
    + row_height_bias_mm(row);

function floor_height_mm(low_profile) = low_profile ? 0.95 : 1.15;
function boss_height_mm(low_profile) = low_profile ? 3.6 : 4.2;

function safe_dish_mm(row, low_profile, sculpt_amount, requested) =
    clamp(requested * clamp(sculpt_amount, 0, 1) * row_sculpt_bias(row), 0.05, low_profile ? 0.95 : 1.45);

function effective_tilt_deg(row, overall_tilt_deg) = row_base_tilt_deg(row) + overall_tilt_deg;

function wide_cap(width_u) = width_u > 1.01;

function mx_boss_size_mm() = 5.5;
function mx_cross_major_mm(clearance_mm) = 4.1 + clearance_mm;
function mx_cross_minor_mm(clearance_mm) = 1.20 + clearance_mm * 0.8;

function choc_slot_spacing_mm() = 5.70;
function choc_post_size_mm() = [1.15, 2.95];
function choc_post_tip_size_mm() = [0.74, 2.54];
function choc_post_corner_radius_mm() = 0.20;
function choc_post_tip_height_mm(low_profile) = low_profile ? 0.40 : 0.45;

function lip_height_mm() = 0.72;
function print_preview_lift_mm(print_angle_deg, width_u, outer_family, low_profile) =
    cap_height_mm("R3", low_profile, outer_family) + base_cap_depth_mm(outer_family) * sin(print_angle_deg) * 0.6 + width_u;


function shell_width_trim_mm(low_profile) = 0.00;
function shell_depth_trim_mm(low_profile) = 0.00;
function shell_width_mm(low_profile, outer_family) = base_cap_width_mm(1, outer_family) - shell_width_trim_mm(low_profile);
function shell_depth_mm(low_profile, outer_family) = base_cap_depth_mm(outer_family) - shell_depth_trim_mm(low_profile);
function shell_height_scale() = 1.656;
function shell_height_mm(row, low_profile) =
    (
        (low_profile ? 4.80 : 6.35)
        + (row == "R1" ? (low_profile ? 0.52 : 0.58) :
           row == "R2" ? (low_profile ? 0.24 : 0.30) :
           row == "R3" ? (low_profile ? 0.00 : 0.06) :
           row == "R4" ? (low_profile ? 0.36 : 0.42) :
           row == "Thumb" ? (low_profile ? -0.08 : 0.00) : 0.06)
    ) * shell_height_scale();

function saddle_depth_scale() = 1.42;
function saddle_depth_mm(row, low_profile) =
    (low_profile ? 1.42 : 1.18)
    * (row == "R1" ? 0.94 :
       row == "R2" ? 1.02 :
       row == "R3" ? 1.06 :
       row == "R4" ? 0.98 :
       row == "Thumb" ? 0.82 : 1.00)
    * saddle_depth_scale();

function shell_top_shift_mm(total_height, tilt_deg) = tan(tilt_deg) * total_height * 0.46;
function shell_row_depth_bias_mm(row, low_profile) =
    (low_profile ? 1.0 : 1.08)
    * (row == "R1" ? 0.58 :
       row == "R2" ? 0.26 :
       row == "R3" ? 0.00 :
       row == "R4" ? 0.34 :
       row == "Thumb" ? 0.16 : 0.00);

function section_z_t(idx, low_profile) =
    (low_profile
        ? [0.18, 0.34, 0.56, 0.78, 1.00]
        : [0.00, 0.16, 0.38, 0.68, 1.00])[idx];
function section_shift_t(idx) = [0.00, 0.08, 0.34, 0.74, 1.00][idx];
function section_width_trim_mm(idx, low_profile) =
    (low_profile
        ? [0.08, 0.10, 0.24, 0.72, 1.22]
        : [0.00, 0.10, 0.26, 0.86, 1.46])[idx];
function section_depth_trim_mm(idx, low_profile) =
    (low_profile
        ? [0.22, 0.36, 1.56, 2.92, 3.24]
        : [0.00, 0.18, 0.56, 1.36, 2.06])[idx];
function section_corner_radius_mm(idx) = [2.34, 2.58, 2.96, 3.36, 3.62][idx];
function section_thickness_mm(idx) = idx == 4 ? 0.18 : 0.22;

function section_z_mm(idx, total_height, low_profile) = 0.10 + section_z_t(idx, low_profile) * total_height;
function outer_section_size(idx, row, low_profile, outer_family) = [
    shell_width_mm(low_profile, outer_family) - section_width_trim_mm(idx, low_profile),
    shell_depth_mm(low_profile, outer_family) - section_depth_trim_mm(idx, low_profile) - shell_row_depth_bias_mm(row, low_profile) * section_z_t(idx, low_profile)
];

function inner_section_size(idx, row, low_profile, outer_family, wall_mm) =
    let(sz = outer_section_size(idx, row, low_profile, outer_family))
    [max(4.8, sz[0] - wall_mm * 2), max(4.8, sz[1] - wall_mm * 2)];

function section_shift_mm(idx, top_shift) = top_shift * section_shift_t(idx);
function cavity_opening_size(row, low_profile, outer_family, wall_mm) = [
    max(5.6, shell_width_mm(low_profile, outer_family) - wall_mm * (low_profile ? 2.45 : 2.3)),
    max(5.4, shell_depth_mm(low_profile, outer_family) - wall_mm * (low_profile ? 2.55 : 2.3) - shell_row_depth_bias_mm(row, low_profile) * 0.18)
];
function bottom_lip_inset_mm(low_profile) = low_profile ? [0.00, 1.06] : [0.00, 0.82];
function bottom_lip_radius_trim_mm(low_profile) = low_profile ? 0.54 : 0.44;

function roof_budget_mm(row, low_profile, roof_mm) = roof_mm + saddle_depth_mm(row, low_profile) * 0.82 + (low_profile ? 0.12 : 0.24);
function choc_stem_extension_mm() = 0.50;
function stem_attach_z_mm(low_profile, stem_family = "choc_v1") =
    (low_profile ? -1.05 : -1.12) - (stem_family == "choc_v1" ? choc_stem_extension_mm() : 0);
function support_anchor_z(total_height, row, low_profile, roof_mm) = total_height - roof_budget_mm(row, low_profile, roof_mm) - 0.08;
function cavity_top_z_mm(row, low_profile, stem_family, roof_mm) =
    let(total_height = shell_height_mm(row, low_profile))
    min(
        support_anchor_z(total_height, row, low_profile, roof_mm),
        roof_drop_bottom_z(low_profile, stem_family) - stem_shell_overlap_mm(low_profile)
    );
function stem_body_height_mm(low_profile, stem_family) =
    low_profile
    ? (stem_family == "mx" ? 3.25 : 3.38 + choc_stem_extension_mm())
    : (stem_family == "mx" ? 2.35 : 2.55 + choc_stem_extension_mm());
function roof_drop_bottom_z(low_profile, stem_family) = stem_attach_z_mm(low_profile, stem_family) + stem_body_height_mm(low_profile, stem_family);
function stem_shell_overlap_mm(low_profile) = low_profile ? 0.42 : 0.34;
function stem_front_y_mm(low_profile, stem_family, clearance_mm) =
    stem_family == "mx"
    ? ((mx_cross_major_mm(clearance_mm) + (low_profile ? 0.70 : 0.82)) / 2 + (low_profile ? 0.34 : 0.38))
    : (3.18 + clearance_mm * 0.20) / 2;
function bottom_lip_low_z_mm() = -0.05;
function rotated_z_mm(y, z, angle_deg) = y * sin(angle_deg) + z * cos(angle_deg);
function print_contact_depth_mm(row, low_profile, outer_family) = outer_section_size(0, row, low_profile, outer_family)[1] - bottom_lip_inset_mm(low_profile)[1] * 2;
function print_lip_anchor_idx(low_profile) = low_profile ? 0 : 1;
function print_lip_angle_deg(row, low_profile, outer_family) =
    let(
        total_height = shell_height_mm(row, low_profile),
        anchor_idx = print_lip_anchor_idx(low_profile),
        lip_y = -print_contact_depth_mm(row, low_profile, outer_family) / 2,
        anchor_y = -outer_section_size(anchor_idx, row, low_profile, outer_family)[1] / 2,
        lip_z = bottom_lip_low_z_mm(),
        anchor_low_z = section_z_mm(anchor_idx, total_height, low_profile) - section_thickness_mm(anchor_idx) / 2
    )
    low_profile ? atan2(abs(anchor_low_z - lip_z), abs(anchor_y - lip_y)) : 45;
function saddle_rim_mm(row, low_profile) =
    (low_profile ? 0.72 : 0.88)
    * (row == "R3" ? 1.0 :
       row == "Thumb" ? 0.72 : 0.84);
function row_mark_text(row) = row == "Thumb" ? "T" : row;
function row_mark_depth_mm(low_profile) = low_profile ? 0.20 : 0.23;
function row_mark_size_mm(row, low_profile, outer_family, wall_mm) =
    min(low_profile ? 2.30 : 2.70, cavity_opening_size(row, low_profile, outer_family, wall_mm)[0] * 0.190);
function row_mark_offset_y_mm(row, low_profile, outer_family, wall_mm) =
    -cavity_opening_size(row, low_profile, outer_family, wall_mm)[1] * 0.28;
function homing_enabled(homing_type) = homing_type != "None";
function homing_anchor_z_mm(row, low_profile) =
    shell_height_mm(row, low_profile) - saddle_depth_mm(row, low_profile) * 1.23;
function homing_dot_radius_mm(low_profile, homing_scale) =
    (low_profile ? 0.34 : 0.40) * clamp(homing_scale, 0.5, 2.0);
function homing_dot_height_mm(low_profile, homing_scale) =
    (low_profile ? 0.24 : 0.28) * clamp(homing_scale, 0.5, 2.0);
function homing_dot_spacing_mm(low_profile, homing_scale) =
    (low_profile ? 1.10 : 1.30) * clamp(homing_scale, 0.5, 2.0);
function homing_ring_major_mm(low_profile, homing_scale) =
    (low_profile ? 1.16 : 1.34) * clamp(homing_scale, 0.5, 2.0);
function homing_ring_tube_mm(low_profile, homing_scale) =
    (low_profile ? 0.18 : 0.22) * clamp(homing_scale, 0.5, 2.0);
function homing_line_size_mm(low_profile, homing_scale) = [
    (low_profile ? 2.80 : 3.30) * clamp(homing_scale, 0.5, 2.0),
    (low_profile ? 0.44 : 0.52) * clamp(homing_scale, 0.5, 2.0),
    (low_profile ? 0.22 : 0.26) * clamp(homing_scale, 0.5, 2.0)
];
function print_contact_lift_mm(print_angle_deg, row, low_profile, outer_family, stem_family, clearance_mm) =
    let(
        total_height = shell_height_mm(row, low_profile),
        anchor_idx = print_lip_anchor_idx(low_profile),
        anchor_z = section_z_mm(anchor_idx, total_height, low_profile),
        lip_y = -print_contact_depth_mm(row, low_profile, outer_family) / 2,
        anchor_y = -outer_section_size(anchor_idx, row, low_profile, outer_family)[1] / 2,
        lip_z = bottom_lip_low_z_mm(),
        anchor_low_z = anchor_z - section_thickness_mm(anchor_idx) / 2,
        stem_low_z = stem_attach_z_mm(low_profile, stem_family),
        stem_front_y = low_profile ? -stem_front_y_mm(low_profile, stem_family, clearance_mm) : 0,
        contact_z = min(
            rotated_z_mm(lip_y, lip_z, print_angle_deg),
            rotated_z_mm(anchor_y, anchor_low_z, print_angle_deg),
            rotated_z_mm(0, stem_low_z, print_angle_deg),
            rotated_z_mm(stem_front_y, stem_low_z, print_angle_deg)
        )
    )
    -contact_z;

module section_wafer(size, radius, z, shift_y = 0, thickness = 0.20) {
    translate([0, shift_y, z])
        wafer(size = size, radius = radius, thickness = thickness);
}

module outer_shell(row, overall_tilt_deg, low_profile, outer_family) {
    total_height = shell_height_mm(row, low_profile);
    top_shift = shell_top_shift_mm(total_height, effective_tilt_deg(row, overall_tilt_deg));
    base_size = outer_section_size(0, row, low_profile, outer_family);
    lip_inset = bottom_lip_inset_mm(low_profile);

    hull() {
        section_wafer(
            size = [
                max(4.0, base_size[0] - lip_inset[0] * 2),
                max(4.0, base_size[1] - lip_inset[1] * 2)
            ],
            radius = max(0.40, section_corner_radius_mm(0) - bottom_lip_radius_trim_mm(low_profile)),
            z = -0.02,
            shift_y = 0,
            thickness = 0.06
        );

        for (idx = [0 : 4]) {
            section_wafer(
                size = outer_section_size(idx, row, low_profile, outer_family),
                radius = section_corner_radius_mm(idx),
                z = section_z_mm(idx, total_height, low_profile),
                shift_y = section_shift_mm(idx, top_shift),
                thickness = section_thickness_mm(idx)
            );
        }
    }
}

module inner_cavity(row, overall_tilt_deg, low_profile, outer_family, stem_family, wall_mm, roof_mm) {
    total_height = shell_height_mm(row, low_profile);
    top_shift = shell_top_shift_mm(total_height, effective_tilt_deg(row, overall_tilt_deg));
    cavity_top_z = cavity_top_z_mm(row, low_profile, stem_family, roof_mm);

    hull() {
        section_wafer(
            size = cavity_opening_size(row, low_profile, outer_family, wall_mm),
            radius = 1.30,
            z = -0.02,
            shift_y = 0,
            thickness = 0.20
        );

        for (idx = [1 : 3]) {
            section_wafer(
                size = inner_section_size(idx, row, low_profile, outer_family, wall_mm),
                radius = max(0.95, section_corner_radius_mm(idx) - wall_mm * 0.68),
                z = min(section_z_mm(idx, total_height, low_profile), cavity_top_z - 0.24),
                shift_y = section_shift_mm(idx, top_shift),
                thickness = 0.18
            );
        }

        section_wafer(
            size = inner_section_size(4, row, low_profile, outer_family, wall_mm),
            radius = max(0.90, section_corner_radius_mm(4) - wall_mm * 0.72),
            z = cavity_top_z,
            shift_y = top_shift * 0.76,
            thickness = 0.18
        );
    }
}

module row_mark_cut(row, low_profile, outer_family, stem_family, wall_mm, roof_mm) {
    mark_depth = row_mark_depth_mm(low_profile);
    mark_size = row_mark_size_mm(row, low_profile, outer_family, wall_mm);
    mark_y = row_mark_offset_y_mm(row, low_profile, outer_family, wall_mm);
    mark_z = cavity_top_z_mm(row, low_profile, stem_family, roof_mm) - 0.02;

    translate([0, mark_y, mark_z])
        linear_extrude(height = mark_depth + 0.04)
            offset(r = 0.06)
                mirror([1, 0, 0])
                    rotate(180)
                        text(row_mark_text(row), size = mark_size, halign = "center", valign = "center", spacing = 0.92);
}

module homing_dot_bump(dot_radius, dot_height) {
    translate([0, 0, dot_height * 0.18])
        scale([dot_radius, dot_radius, dot_height])
            sphere(r = 1, $fn = 40);
}

module homing_line_bump(length_mm, width_mm, height_mm) {
    hull() {
        for (x = [-max(0, length_mm / 2 - width_mm / 2), max(0, length_mm / 2 - width_mm / 2)]) {
            translate([x, 0, height_mm * 0.18])
                scale([width_mm / 2, width_mm / 2, height_mm])
                    sphere(r = 1, $fn = 40);
        }
    }
}

module homing_ring_bump(major_radius_mm, tube_radius_mm) {
    translate([0, 0, tube_radius_mm * 0.12])
        rotate_extrude($fn = 72)
            translate([major_radius_mm, 0, 0])
                circle(r = tube_radius_mm, $fn = 36);
}

module saddle_cut(row, overall_tilt_deg, low_profile, outer_family) {
    total_height = shell_height_mm(row, low_profile);
    tilt_deg = effective_tilt_deg(row, overall_tilt_deg);
    top_shift = shell_top_shift_mm(total_height, tilt_deg);
    saddle_mm = saddle_depth_mm(row, low_profile);
    top_size = outer_section_size(4, row, low_profile, outer_family);
    saddle_rim = saddle_rim_mm(row, low_profile);
    bowl_size = [
        max(4.4, top_size[0] - saddle_rim * 2),
        max(4.4, top_size[1] - saddle_rim * 2)
    ];
    thumb_bowl_scale = row == "Thumb" ? [1.02, 1.08, 1.02] : [1.00, 1.00, 1.00];
    front_sweep_y = -top_size[1] * (row == "Thumb" ? 0.14 : row == "R3" ? 0.18 : 0.20);
    front_sweep_z = -saddle_mm * (row == "Thumb" ? 0.12 : 0.18);
    front_sweep_scale = [
        bowl_size[0] * (row == "Thumb" ? 0.90 : 0.96),
        bowl_size[1] * (row == "Thumb" ? 0.42 : row == "R3" ? 0.52 : 0.46),
        saddle_mm * (row == "Thumb" ? 0.90 : row == "R3" ? 1.10 : 1.00)
    ];
    rear_sweep_y = top_size[1] * 0.18;
    rear_sweep_z = -saddle_mm * 0.16;
    rear_sweep_scale = [bowl_size[0] * 0.94, bowl_size[1] * 0.50, saddle_mm * 1.00];

    translate([0, top_shift * 0.98, total_height + saddle_mm * 0.01])
        rotate([tilt_deg * 0.44, 0, 0])
            union() {
                scale([bowl_size[0] * 0.84 * thumb_bowl_scale[0], bowl_size[1] * 1.08 * thumb_bowl_scale[1], saddle_mm * 1.52 * thumb_bowl_scale[2]])
                    sphere(r = 1, $fn = 72);

                translate([0, 0, -saddle_mm * 0.14])
                    scale([bowl_size[0] * 1.18 * thumb_bowl_scale[0], bowl_size[1] * 0.70 * thumb_bowl_scale[1], saddle_mm * 0.92 * thumb_bowl_scale[2]])
                        sphere(r = 1, $fn = 72);

                translate([0, top_size[1] * 0.02, -saddle_mm * 0.08])
                    scale([bowl_size[0] * 0.90 * thumb_bowl_scale[0], bowl_size[1] * 1.18 * thumb_bowl_scale[1], saddle_mm * 0.56 * thumb_bowl_scale[2]])
                        sphere(r = 1, $fn = 72);

                translate([0, 0, saddle_mm * 0.02])
                    scale([bowl_size[0] * 1.08 * thumb_bowl_scale[0], bowl_size[1] * 0.88 * thumb_bowl_scale[1], saddle_mm * 0.42 * thumb_bowl_scale[2]])
                        sphere(r = 1, $fn = 72);

                translate([0, front_sweep_y, front_sweep_z])
                    scale(front_sweep_scale)
                        sphere(r = 1, $fn = 72);

                if (row == "R3") {
                    translate([0, rear_sweep_y, rear_sweep_z])
                        scale(rear_sweep_scale)
                            sphere(r = 1, $fn = 72);
                }
            }
}

module homing_feature(row, overall_tilt_deg, low_profile, outer_family, homing_type, homing_offset_y_mm, homing_scale) {
    total_height = shell_height_mm(row, low_profile);
    tilt_deg = effective_tilt_deg(row, overall_tilt_deg);
    top_shift = shell_top_shift_mm(total_height, tilt_deg);
    saddle_mm = saddle_depth_mm(row, low_profile);
    top_size = outer_section_size(4, row, low_profile, outer_family);
    saddle_rim = saddle_rim_mm(row, low_profile);
    dot_radius = homing_dot_radius_mm(low_profile, homing_scale);
    dot_height = homing_dot_height_mm(low_profile, homing_scale);
    dot_spacing = homing_dot_spacing_mm(low_profile, homing_scale);
    ring_major = min(homing_ring_major_mm(low_profile, homing_scale), max(0.70, min(top_size[0], top_size[1]) * 0.24 - saddle_rim));
    ring_tube = min(homing_ring_tube_mm(low_profile, homing_scale), ring_major * 0.38);
    line_size = homing_line_size_mm(low_profile, homing_scale);
    line_length = min(line_size[0], max(line_size[1] * 1.5, top_size[0] - saddle_rim * 3.8));

    if (homing_enabled(homing_type)) {
        translate([0, top_shift * 0.98, homing_anchor_z_mm(row, low_profile)])
            rotate([tilt_deg * 0.44, 0, 0])
                translate([0, homing_offset_y_mm, 0])
                    if (homing_type == "Dot") {
                        homing_dot_bump(dot_radius, dot_height);
                    } else if (homing_type == "2 dots") {
                        for (x = [-dot_spacing / 2, dot_spacing / 2]) {
                            translate([x, 0, 0])
                                homing_dot_bump(dot_radius, dot_height);
                        }
                    } else if (homing_type == "3 dots") {
                        for (x = [-dot_spacing, 0, dot_spacing]) {
                            translate([x, 0, 0])
                                homing_dot_bump(dot_radius, dot_height);
                        }
                    } else if (homing_type == "Circle") {
                        homing_ring_bump(ring_major, ring_tube);
                    } else if (homing_type == "Line") {
                        homing_line_bump(line_length, line_size[1], line_size[2]);
                    }
    }
}

module mx_cross_outline(major, minor, pad = 0) {
    union() {
        square([major + pad, minor + pad], center = true);
        square([minor + pad, major + pad], center = true);
    }
}

module mx_stem_boss(clearance_mm, low_profile) {
    boss_h = stem_body_height_mm(low_profile, "mx");
    major = mx_cross_major_mm(clearance_mm);
    minor = mx_cross_minor_mm(clearance_mm);
    shell_pad = low_profile ? 0.70 : 0.82;
    shell_round = low_profile ? 0.34 : 0.38;

    difference() {
        linear_extrude(height = boss_h)
            offset(r = shell_round)
                mx_cross_outline(major, minor, shell_pad);

        translate([0, 0, -0.10])
            linear_extrude(height = boss_h + 0.20)
                union() {
                    square([major, minor], center = true);
                    square([minor, major], center = true);
                }
    }
}

module choc_stem_boss(clearance_mm, low_profile) {
    boss_h = stem_body_height_mm(low_profile, "choc_v1");
    spacing = choc_slot_spacing_mm();
    post = choc_post_size_mm();
    tip = choc_post_tip_size_mm();
    corner_r = choc_post_corner_radius_mm();
    tip_h = min(choc_post_tip_height_mm(low_profile), boss_h - 0.02);
    wafer_h = 0.04;

    for (x = [-spacing / 2, spacing / 2]) {
        translate([x, 0, 0]) {
            hull() {
                linear_extrude(height = wafer_h)
                    rounded_rect(size = tip, radius = corner_r, center = true);

                translate([0, 0, tip_h])
                    linear_extrude(height = wafer_h)
                        rounded_rect(size = post, radius = corner_r, center = true);
            }

            if (boss_h > tip_h) {
                translate([0, 0, tip_h])
                    linear_extrude(height = boss_h - tip_h)
                        rounded_rect(size = post, radius = corner_r, center = true);
            }
        }
    }
}

module stem_support(low_profile, stem_family, clearance_mm) {
    attach_z = stem_attach_z_mm(low_profile, stem_family);

    translate([0, 0, attach_z])
        if (stem_family == "mx") {
            mx_stem_boss(clearance_mm, low_profile);
        } else {
            choc_stem_boss(clearance_mm, low_profile);
        }
}

module keycap(row = "R3", outer_family = "mx", stem_family = "choc_v1", low_profile = true,
              overall_tilt_deg = 0, clearance_mm = default_clearance_mm(),
              homing_type = "None", homing_offset_y_mm = 0, homing_scale = 1.0) {
    wall_mm = default_wall_mm();
    roof_mm = default_roof_mm();

    union() {
        difference() {
            outer_shell(row, overall_tilt_deg, low_profile, outer_family);
            inner_cavity(row, overall_tilt_deg, low_profile, outer_family, stem_family, wall_mm, roof_mm);
            row_mark_cut(row, low_profile, outer_family, stem_family, wall_mm, roof_mm);
            saddle_cut(row, overall_tilt_deg, low_profile, outer_family);
        }

        homing_feature(row, overall_tilt_deg, low_profile, outer_family, homing_type, homing_offset_y_mm, homing_scale);
        stem_support(low_profile, stem_family, clearance_mm);
    }
}

module print_pose(print_angle_deg = 45, row = "R3", outer_family = "mx", stem_family = "choc_v1", low_profile = true,
                  overall_tilt_deg = 0, clearance_mm = default_clearance_mm(),
                  homing_type = "None", homing_offset_y_mm = 0, homing_scale = 1.0) {
    translate([0, 0, print_contact_lift_mm(print_angle_deg, row, low_profile, outer_family, stem_family, clearance_mm)])
        rotate([print_angle_deg, 0, 0])
            children();
}


if (render_mode == "print") {
    print_pose(print_angle_deg, row, outer_family, stem_family, low_profile, overall_tilt_deg, clearance_mm,
               homing_type, homing_offset_y_mm, homing_scale)
        keycap(row, outer_family, stem_family, low_profile, overall_tilt_deg, clearance_mm,
               homing_type, homing_offset_y_mm, homing_scale);
} else {
    keycap(row, outer_family, stem_family, low_profile, overall_tilt_deg, clearance_mm,
           homing_type, homing_offset_y_mm, homing_scale);
}
