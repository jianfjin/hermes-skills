# Spam Detection Patterns

Repos observed in trending/new-repo search results that exhibited spam/SEO characteristics (May 2026):

## Pattern Categories

### SEO Keyword Stuffing
Descriptions crammed with unrelated keywords, often pipe-delimited or comma-separated:
- `"download free PC windows 11, steam workshop downloader bypass, high CPU RAM usage fix, android apk mobile sync..."`
- `"hydralauncher download free PC library fontes links baixar, steam verde download..."`
- `"Stable Diffusion webui automatic1111 download free, comfyui setup guide, sdxl checkpoint safetensors, lora model civitai..."`

### Impersonation / Typosquatting
Repos with names mimicking popular projects:
- `BasZ4ll/Stable-Diffusion-WebUI` → impersonates AUTOMATIC1111/stable-diffusion-webui
- `arnabchoudhury404/hydra-launcher` → impersonates the real Hydra Launcher
- `Flizorules05/ROM-MGBA-Pokemon-Emulator-PC` → keyword-stuffed gaming repo

### Minimal / No Description
- `FoundZiGu/GuJumpgate` — 1,091 stars, zero description, cryptic name. High suspicion.
- `thananon/9arm-skills` — 994 stars, no description

### Fork Ratio Anomalies
Normal new repos: forks ≈ 2-10% of stars
- `FoundZiGu/GuJumpgate`: 378 forks / 1,091 stars = 35% (anomalous)

## Filter Keywords

When scanning descriptions for spam, check for these substrings (case-insensitive):

```
download free, crack, bypass, android apk, steam verde, rom emulator,
pokemon, hydra launcher, wallpaper engine, stable diffusion webui,
automatic1111, torrent, cheat code, game hack, keygen, activation,
serial key, fontes links, baixar, steam workshop downloader
```

A repo matching 2+ of these is almost certainly spam.
