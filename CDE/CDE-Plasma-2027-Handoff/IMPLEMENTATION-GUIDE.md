# Implementation and test guide

## Phase 0 — safe working base

1. Document the target versions of Plasma, distribution and Qt.
2. Start development in a new user profile or a VM.
3. Before making changes, back up `~/.config`, `~/.local/share/plasma`, colour schemes and KWin configuration.
4. Set up a repository with component folders, licence information and screenshot comparison.

## Phase 1 — visual core prototype

Deliverables:

- colour scheme from `design-tokens.json`
- active/inactive window decoration
- static two-row panel prototype
- 12 core icons: CDE menu, home, file, folder, terminal, web, mail, editor, workspace, network, audio, trash
- sample view at 1920×1080 and 2560×1440

Acceptance:

- the target palette looks like `05-target-teal-copper-panel.png`.
- windows and panel read as Motif/CDE at first glance, not Breeze.
- active title bar, pressed button and focused field have three different, unambiguous states.

## Phase 2 — functional front panel

1. Build the segment component and two rows.
2. Hook up launchers, tasks and workspace switching.
3. Implement subpanel triggers and popups.
4. Offer visible/autohide/hotspot as configuration.
5. Test multi-monitor logic and panel position top/bottom.
6. Check pointer, keyboard and touch separately.

## Phase 3 — theme coverage

- Plasma widgets, notifications, calendar, system tray and tooltips
- Qt Widgets/Qt Quick Controls
- full core icon coverage and controlled fallback
- cursor, lock screen and optionally SDDM

## Phase 4 — packaging

- `install.sh`, `uninstall.sh`, version manifest and licence files
- dry run without root privileges
- installation on a fresh user profile
- complete removal with restoration of the previous selection

## Visual test matrix

| Check | Expectation | Failure example |
|---|---|---|
| 100 % scaling | edges exact, text not squashed | half pixels, blurry SVGs |
| 150 % scaling | bevel steps still clear | frames of varying thickness |
| 200 % scaling | icons have clean optical sizes | upscaled 16 px raster graphic |
| active/inactive window | distinguishable without hesitation | only a slightly different hue |
| keyboard focus | visible on every widget | focus only on text inputs |
| panel autohide | no focus trap, no flicker | panel closes on the way to the subpanel |
| multi-monitor | popup stays fully visible | subpanel off screen |
| dark terminal content | frame stays clearly legible | black area swallows the decoration |

## Functional acceptance criteria

- Plasma starts without QML or KWin errors.
- No component needs root privileges.
- The Wayland session is primarily functional.
- Autohide and subpanels can be fully operated by keyboard.
- Uninstalling removes only our own files.
- Fallback icons fall back in a controlled way to a documented theme; there are no style breaks in the visible core area.

## Screenshot comparison

Capture the same test desktop for every milestone:

- file manager on the left, terminal on the right
- active and inactive window titles visible at the same time
- open application menu and one subpanel
- four workspaces, system status and clock in the panel
- resolution and scale factor in the file name

For each screenshot the LLM should briefly list: deviation, suspected cause, affected component and next fix.
