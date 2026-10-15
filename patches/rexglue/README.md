# ReXGlue patch series

Base: `rexglue-sdk` tag `nightly-20260904-0c7b01a0`
(`0c7b01a0ac0479801757507d80533f662fa0815d`).

Apply these patches in numeric order with
`python tools/apply_rexglue_patches.py` from the project root:

1. Runtime compatibility fixes used by the game.
2. D3D12 draw-outcome diagnostics.
3. Guest PPC context on access violations.
4. Windowed Windows title bar and frame.
5. Backend selection, explicit Vulkan FSI capability checks and GPU selection,
   descriptor reuse, persistent per-thread driver pipeline caches, and a
   pregenerated-code build guard that survives code generation.

The patch series produces the project SDK base at `55a85aec17bf5c7f6b15db4df2c05a0c9f0340e2`.
The submodule pin also includes the PPC dispatch and memory-hook fixes, ROV
shader specialization, VMX leaf localization, opt-in late depth and fused
resolve paths, and indirect-call crash context. Its current revision is
`a345857b6d76f93c4bb79e0af1da32188e45aaf9`; the patch helper recognizes both
the patch-series base and this maintained revision.

The patches are project source changes, not generated game code. Keep the SDK
base pinned; the patch tool refuses a different revision or a partially patched
checkout.
