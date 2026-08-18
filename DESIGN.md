# GP Access Planner design system

## Direction

Service Timetable. Interface behaves like a calm public-service planning board:
time runs horizontally, service channels occupy separate lanes, and synthetic
capacity appears as a distinct planning overlay. It must not resemble an NHS
website, a generic KPI dashboard, or a theatrical command centre.

## Visual system

- Daylight palette: paper `#f4f1e8`, white `#fffdf8`, ink `#14231f`, muted ink
  `#52625d`, rule `#cbd2ca`, observed blue `#156b8a`, forecast violet `#6558a6`,
  synthetic amber `#9a3f00`, positive green `#267052`, and warning red `#a84032`.
- Source Sans 3 carries interface text. IBM Plex Mono is restricted to dates,
  measures, identifiers, and technical metadata. Both fonts are self-hosted.
- Rules, lanes, aligned columns, tabular figures, and timetable cells form the
  component language. Avoid same-size card grids, decorative gradients, glass,
  neon, and soft dashboard tiles.
- Use 1px rules for hierarchy. Elevation is reserved for focused floating
  controls and uses a downward offset with soft blur.
- Corners are 12px for major panels, 8px for controls, and pill shapes only for
  compact status or selection controls.

## Behaviour

- Plan, Data, Capacity Lab, and Methods use one navigation and control grammar.
- Observed values use solid lines or fills. Forecasts use a central line and
  translucent uncertainty band. Synthetic capacity uses amber stepped lines
  and hatch marks. Labels accompany every visual encoding.
- Horizon changes scrub the same timetable instead of replacing the page.
- Motion lasts 150 to 220ms, communicates selection or layer changes, starts
  from visible content, and is removed under reduced-motion preference.
- Controls expose hover, focus, active, disabled, loading, error, and empty
  states. Focus rings use ink plus paper separation and remain visible.
- Desktop uses a left rail plus planning canvas. Small screens collapse to a
  top navigation and vertically stacked lanes without hiding source metadata.

## Copy

- Use recorded activity, access pressure, forecast, source row, and hypothetical
  capacity. Never use actual capacity, utilisation, total demand, or NHS-backed.
- Put source cutoff, coverage, grain, and limitation next to the number or chart
  they qualify. Synthetic examples always say illustrative or hypothetical.
- Use sentence case. No em dashes. Controls name the action and errors explain
  recovery.
