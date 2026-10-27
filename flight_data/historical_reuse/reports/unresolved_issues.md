# Unresolved historical-data issues

Generated after public-source retrieval on 2026-10-22.

- NOAA Kp coverage from the checked product begins on 2026-10-15, leaving
  11,127 trajectory rows unmatched. Missing Kp values were not zero-filled.
- The requested SWiPS object for 2026-10-15 returned `NoSuchKey`; five daily
  files for 2026-10-10 through 2026-10-14 were inspected.
- The SWiPS combined velocity vector variables do not expose a unit attribute.
  They were preserved for review but not used as a velocity-derived hazard
  indicator. `spacecraft_velocity` explicitly reports km/s.
- Open-Meteo weather was retrieved for one documented Pakistan reference grid
  point. It was not joined to all trajectory points because that would not be
  a defensible spatial match.
- No legitimate accessible historical NOTAM/airspace archive was identified.
- The notebook still contains external `/content` and Google Drive paths, but
  the local workflow no longer depends on them.
- Recovery-route simulation, aircraft performance, fuel, delay, and certified
  aviation thresholds remain intentionally out of scope.

The validation reports distinguish failures from warnings and preserve
unmatched observations rather than treating missing coverage as validation.
