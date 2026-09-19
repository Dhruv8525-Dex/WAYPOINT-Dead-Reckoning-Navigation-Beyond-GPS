# Waypoint reference review and redesign

## Layout Structure
Use an emerald terrain hero, a three-step workflow, a split tools section, and a wide closing invitation. Keep the application sidebar and existing content structure. Reference 4 supplies the feature-strip and card rhythm; references 3 and 5 supply editorial scale.

## Section Order
Navigation, hero, three principles, workflow, workspace tools, invitation, footer. This is a recommended Waypoint composition, not an exact observed sequence from one source.

## Navigation
Keep direct access to the workspace and guide. Preserve every application route, project selector, search, sidebar collapse, and mobile navigation control. Home links return to `/`.

## Typography
Oversized, tightly spaced sans-serif headings and a large footer wordmark echo references 3 and 5. Retain DM Sans and use smaller, readable application type. Exact reference font identities cannot be established from the supplied images.

## Color System
References 1 and 2 establish deep green, emerald and pale sage. Use dark green hero/sidebar, light sage workspace, cream panels, and restrained green controls. Preserve distinct scientific chart series rather than making all data green.

## Spacing and Layout Rhythm
Generous landing sections contrast with compact application controls. Three-column desktop groups become single-column phone layouts. Responsive behavior is a design recommendation because the references do not document browser breakpoints.

## Image Treatment
Use supplied reference 6 as subdued terrain relief and reference 7 as survey contour texture. Both are local static assets. The hero route is explicitly illustrative; real GPS maps remain in the data tools. Leaf photography and hills are mood references rather than literal navigation evidence.

## Cards and Content Blocks
Layered instrument cards and a document stack translate the video's translucent folder depth. Rounded, lightly bordered panels keep application data legible. Do not replace working data displays with decorative mockups.

## Buttons and CTAs
Pill buttons borrow reference 2's soft edges and subtle depth. Existing actions and links remain functional. Animation is restrained and respects reduced-motion preferences.

## Overall Design Feel
An emerald navigation field station: organic terrain, precise research controls, and evidence-focused language. The redesign changes presentation without changing estimators, data schemas, training, device capture, or export logic.

## Recording Coverage and Confidence
The supplied 13.59-second, 354-by-596 recording was sampled at every second from 0 through 13; see `artifacts/redesign/reference-timeline.jpg`. At 0-2 seconds the green folder opens and contents rise. At 3-7 seconds it settles beneath Spotify Glass Folder Effect text. At 8-9 seconds a blue After Effects variant appears. At 10-13 seconds the green sequence returns. This is motion-design evidence, not a demonstrated website interaction or responsive layout. Palette, layering, typography scale and texture observations have high confidence; exact fonts and hidden interactions remain unknown.

## Verification
- TypeScript check and production build passed.
- Existing automated suite: 13 tests passed.
- Browser inspected desktop workspace, existing result map, series toggle and advancing playback; restored the series afterward.
- Browser inspected mobile home, dashboard and model form at 390 pixels; home and dashboard had no horizontal page overflow.
- Import form retained its upload control. CSV, JSON and HTML result exports returned HTTP 200 with expected content types.
- Production terrain assets returned HTTP 200 as image/png.
- No new phone recording or model training was performed for this visual change.

Known pre-existing build note: the lazy map/chart bundle exceeds Vite's 500 kB warning threshold. This does not fail the build.
