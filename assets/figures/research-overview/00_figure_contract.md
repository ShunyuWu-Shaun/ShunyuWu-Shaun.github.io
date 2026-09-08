# Research overview figure: contract

Figure 1 of the homepage. Written before drawing, following the research-plan-figure
workflow: reader takeaway, research object, obstacle, dominant abstraction, branches,
color semantics, and what must not be drawn.

## Reader takeaway (one sentence)

Physical AI stands on the governing dynamics of physical systems; my work learns to
solve those dynamics with neural networks fast enough for design and control, measures
how the remaining model error reaches an operating decision, and tests both on a science
branch (materials processing) and an engineering branch (water-energy and industrial
processes).

## Research object and scene

The governing dynamics of a physical system (an ODE or PDE with initial and boundary
conditions and forcing), its learned solution, and the decision computed from that
solution: a schedule, a control action, or a process set-point.

## Unresolved difficulty

A learned solver is wrong by a small amount everywhere. Whether that error changes a
decision depends on where the system sits. Away from critical points the decision is
insensitive to model error; near a critical point (a bifurcation, a phase or regime
boundary, an active constraint) a small model error moves the decision by a lot. This
dependence, the model-to-decision gap, is not measured by prediction error.

## Dominant visual abstraction

A funnel. A wide top region names Physical AI. It narrows onto one substrate, the
governing dynamics. From the substrate two questions branch: solve the dynamics with
neural networks, and quantify the model-to-decision gap. Both questions are tested on the
same band of physical systems, split into a science branch and an engineering branch.

## Reading path

1. Physical AI (context, neutral) ->
2. Governing dynamics as the substrate (teal object) ->
3. Question A, learning to solve the dynamics (blue), with a computed solution rollout ->
   Question B, the model-to-decision gap (red), with a computed decision-error curve
   that peaks at the critical point; a return arrow from B to A carries the decision-level
   error back as the training and evaluation signal ->
4. Test beds (teal band): science branch and engineering branch, each with named objects.

## Evidence roles inside the figure

- Panel A is a real computation: an advection-diffusion field solved on a grid and shown
  at three times. It is illustrative of a solved field trajectory, not a result.
- Panel B is a real computation on a toy bistable system: the shift of the operating
  equilibrium caused by a fixed model error, plotted against distance to the fold. It is
  illustrative of the gap's dependence on the critical point, not a result.
- Everything else is framing. No box implies a completed result.

## Color semantics (nature-figure palette, three hues plus neutrals)

- blue_main #0F4D92, pale #DDE6F0: learned dynamics, neural solvers (Question A).
- red_strong #B64342, pale #F5E5E5: decisions and the model-to-decision gap (Question B).
- teal #42949E, dark line #317078, pale #E5F0F1: the physical system, the substrate, the
  two application branches.
- neutrals #272727 titles, #4D4D4D body, #767676 captions, #CFCECE rules, #F2F2F2 frame.

## Connector grammar

Straight arrows only, 2.5 pt with triangle heads: one from the Physical AI region into the
substrate, two from the substrate into the questions, two from the questions into the test
bed band, and one return arrow from Question B to Question A. No connector changes
direction, so no bent connector is needed.

## What must not be drawn

No network architecture inventory, no icons, no check marks, no green-good/red-bad coding,
no heatmap without a defined quantity and scale, no decorative bars, no more than one
enclosing frame.

## Final insertion

Canvas 10 in x 6.6 in, inserted on the homepage at about 780 px wide (1 in = 78 px).
Type floors on the canvas: 11 pt captions and axis ticks, 14 pt labels, 18 pt headline
labels, 22 pt for the top-level Physical AI label. All text Arial.
