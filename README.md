# Heat Haze - ESPless version

This is a conversion of doodlum's [Heat Haze](https://www.nexusmods.com/newvegas/mods/76286) mod into an ESP-less version.

## Why?

Originally I was using this mod, but found the configuration options to be a bit lackluser. Also noted that someone in the discussions of the mod was talking about how it was "too close". So I wanted to work on an upgrade.

The main goal of this was following the `ESP-less` trend of this mod; since I'm all for FOSS. Plus i wanted to try my hand at New Vegas modding for the first time that wasn't just "resolve X to work with Y" in `FNVEdit`.

## So what's changed (so far)?

This has been converted to an ESP-less version for starters, so no need for the `.ESP` file in the main mod.

## Installation
- TBA

## Plans
Game plan is:
1. ~~Convert it to ESP-less version~~ ***Done***
2. ~~Set-up scripts to add variance to the `.nif`~~ ***Done***
3. Optimize the ccode a little bit
4. Make it a bit more configurable
5. Allow it to be controllable / togglable through MCM

## AI Disclosure:
I'm not going to deny the usage of AI for working on this; although I wouldn't consider the project to be "one-shot" / "Vibe Coded" by a long stretch. Collaborative, rather than acting as a Manager (I like to think).

AI isn't perfect, and i know that 100%; that's why I've used it more as a collaborative tool rather than a minion to do my bidding. Nothing committed here isn't anything I've blindly implemented or not understood.

Ai was used in the following ways:
- Helping me find resources to port the logic over / researching how NVSE plugins are implemented in this fashion.
- Correcting my mistakes in implementation (i.e. reference fixes, reviewing, looking for anything specifically GECK/NVSE related that I didn't necessarily realise)
- Generating the GitHub release scripts / `heat_hase_variance_generation.py`

Model used: `GPT-6.1 Sol`