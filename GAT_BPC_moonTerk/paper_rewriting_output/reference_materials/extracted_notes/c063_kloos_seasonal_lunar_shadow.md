# C063 Supporting Note

## Bibliographic record

Jacob L. Kloos, John E. Moores, Jasmeer Sangha, Tue Giang Nguyen, and Norbert
Schorghofer, “The temporal and geographic extent of seasonal cold trapping on
the Moon,” *Journal of Geophysical Research: Planets*, vol. 124,
pp. 1935–1944, 2019. DOI:
<https://doi.org/10.1029/2019JE006003>.

Primary article record:
<https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2019JE006003>.

Journal-indexing check:
<https://topj.lib.whu.edu.cn/show.asp?cat=zk&id=72>. The Wuhan University
Library journal guide records *Journal of Geophysical Research: Planets* as
SCIE-indexed and places it in JCR Q1 for Geochemistry & Geophysics using the
displayed 2024 JCR information. This check establishes the requested journal
quartile; it does not support any scientific sentence in the manuscript.

## Verified support

- The paper evaluates temporal and geographic variability of seasonal shadow
  in the lunar polar regions.
- The illumination survey covers 12 lunations with a one-hour time step.
- The illumination survey begins at a declared northern vernal equinox.
- The small lunar obliquity produces seasonal solar-insolation variation over
  the 346.6-Earth-day draconic year.
- The extent and distribution of seasonally shadowed regions depend on local
  topography and time of year, and the total shadowed area varies
  substantially across that cycle.
- The analysis explicitly uses equinoxes and summer/winter solstices to
  describe seasonal evolution; seasonally shadowed area is largest near the
  hemispheric winter solstice, while the modeled polar surface-water maximum
  occurs near the hemispheric vernal equinox rather than at the shadow-area
  maximum.
- The paper's one-hour step is an illumination-model resolution, and its
  12-lunation coverage is an environmental-study duration. Neither quantity
  prescribes the duration of a rover-routing instance.

## Allowed manuscript inference

The lunar solar and seasonal cycles motivate representing the environment
through declared mission epochs rather than importing an Earth-like rapid
diurnal traffic analogy. Significant polar-shadow variation across the lunar
year means that the long cycle does not justify one permanent illumination
fixed state. A defensible experiment may sample 12 anchors uniformly across the
346.6-Earth-day draconic year, use one-hour environmental samples inside each
much shorter mission window, and generate one frozen instance per anchor. The
12-anchor count and one-hour preprocessing resolution are adapted from the
source; the scale-dependent routing horizons come from the project manifest,
not from Kloos et al. Grouping the 12 anchors into four equinox-to-solstice
quarters is the paper's experimental stratification, not a phase ranking
reported by Kloos et al.

## Prohibited use

- Do not claim that every local shadow boundary changes slowly.
- Do not claim that a single environmental state is valid for all mission epochs.
- Do not treat one lunation or the 346.6-day draconic year as the required
  duration of one routing instance.
- Do not call the current optimizer departure-time dependent.
- Do not claim that the future multi-epoch experiment has been completed.
- Do not attribute a fastest routing phase to Kloos et al.
- Do not use this source to support solver performance or exactness.
