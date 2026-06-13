# Blower Fan Assembly (mechanical module)

The vacuum fan assembly provides air suction to the main brush and streams air into the dust bin.

The assembly consists of
- a high-speed blower motor and impeller
- a blower housing (volute)
- a blower exhaust gasket
- blower housing rubber pins

### Assembled vacuum, no top - back
![Teardown reference vacuum - no top, vacuum fan](https://github.com/makerspet/oomwoo/blob/main/assets/vacuum-no-top-vacuum-fan.webp)

# Request for Contribution - Instructions

- review the [teardown master assembly](https://github.com/remakeai/vacuum_cleaner_teardown/blob/main/step/MASTER-ASSM.stp)
- review the [teardown internals photo](https://github.com/remakeai/vacuum_cleaner_teardown/blob/main/assets/vacuum_top_removed.webp)
- review the [reference blower fan](https://github.com/remakeai/vacuum_cleaner_teardown/blob/main/assets/blower_fan.webp)
- start with the [teardown vacuum fan module reference](https://github.com/remakeai/vacuum_cleaner_teardown/blob/main/step/M04.stp)
  - post in [Project Discussions](https://github.com/makerspet/oomwoo/discussions?discussions_q=) to let everyone know you're working on it
  - post your progress as well
- find a high-speed blower motor and impeller
  - make sure it is easy-to-source, affordable
  - make sure it fits the teardown reference vacuum
  - the reference vacuum uses szebo.com EBO Innovation EBO-A65126 that runs DC 8.4V 1.4A, DC 12.6V 2.2A
  - if you cannot find a suitable off-the-shelf high-speed fan, try designing and 3D printing one
- pick blower housing material thickness to ensure sturdiness without excess weight
- redesign the housing the fan you've selected
  - make sure your redesigned assembly mates with the dust bin and the vacuum frame
  - try finding an off-the-shelf gasket
  - if an off-the-shelf gasket is unavailable, review [this post](https://makerspet.com/blog/3d-printable-omni-wheel/) for alternatives
  - consider printing one using TPU
- make your design 3D printable
  - assume PETG
  - make the part easy to 3D print - ideally no supports - and reproduced reliably
  - make the sliced part fit a 20cm by 25cm, 20 cm height. Split the part if necessary.
- test it well
  - 3D print it, assemble it, make sure it works, mates with the rest of the design
- submit a PR (pull request) to `contributions/vacuum-fan/<your-github-username>/`
  - design: 3D STEP files, 3D CAD source files (Fusion 360, Solidworks, etc.) and 3MF/STL files
  - make sure to submit the master STEP assembly file
  - submit BoM of all sub-components
  - instructions, documentation - how to use, assemble, 3D print, troubleshoot, test results
  - photos, videos
  - announce your submission in [Project Discussions](https://github.com/makerspet/oomwoo/discussions?discussions_q=)
- iterate with review
- TBD, expect the RFC to evolve

(*) if you have a strong reason to change the part's interface, material or something else of that sort,
please post your raionale in [discussions](https://github.com/makerspet/oomwoo/discussions?discussions_q=).

Teardown reference showing the vacuum fan assembly
![Teardown internals photo](https://github.com/remakeai/vacuum_cleaner_teardown/blob/main/assets/vacuum_top_removed.webp)

Teardown reference blower fan
![Reference blower fan](https://github.com/remakeai/vacuum_cleaner_teardown/blob/main/assets/blower_fan.webp)

## Acceptance criteria

Objective, measurable. Examples:
- Fits the reference chassis without modification to other modules
- Easy to source, affordable
- Performs its function
  - no air leaks
  - easy to empty
- Reasonable mass, size, cost budget
- Documented and reliably reproducible by someone else
- TBD, expect criteria to evolve

The maintainer selects among compliant candidates using these criteria. Multiple
attempts are welcome and useful even if not selected — modules are swappable, and
a non-selected design is still a valid learning exercise and a fallback.
