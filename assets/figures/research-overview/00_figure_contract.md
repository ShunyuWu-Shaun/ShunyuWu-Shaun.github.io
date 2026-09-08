# Research architecture figure: contract

Written before drawing. It fixes what the figure says, in what order, and what it must not say.

## Reader takeaway (one sentence)

A physical system supplies its governing dynamics; a neural operator learns to solve them; a controller or an optimizer decides with the solution, and the decision error returns to train the solver.

## Backbone

One vertical path with three stages and one return.

1. **A. Physical systems in science and engineering.** Science: temperature and composition fields of a materials processing step. Engineering: urban water demand and network pressure, day-ahead electricity price, hot-strip rolling energy.
2. **B. Solving the dynamics with neural networks.** A neural operator maps initial conditions, boundary conditions, and forcing to the solution field in one forward pass.
3. **C. The model-to-decision gap.** A controller or an optimizer decides with the solution. The decision error is small over most of the state space and large near a critical point, measured as regret, closed-loop cost, and constraint violation.

Transfers: A to B carries the governing dynamics with their conditions; B to C carries the solution field and its sensitivities; the return path from C to B carries the decision error as the training signal.

## Panels

- A: one day of demand and price in a water system, illustrative.
- B: a two-dimensional advection-diffusion field solved with an explicit scheme, shown at three times, computed.
- C: equilibrium shift of the bistable system x' = r + x - x^3 under a fixed parameter error, against distance to the fold, computed.

Each panel illustrates one relation. None reports a result, and the caption says so.

## Colour

Three colours from the top-conference figure library, one per direction, used identically on every page of the site: purple #9467BD (A), teal #31859A (B), coral #EA7F6F (C). Ink #4D4D4D, rules #D9D9D9. No primary red, green, or blue.

## What must not be drawn

No network architecture, no icons, no check marks, no second enclosing frame, no heatmap without a defined quantity and scale, no text that repeats the caption.
