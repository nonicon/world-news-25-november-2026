# World News in One Image — 25 November 2026

[![make.fun](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/nonicon/world-news-25-november-2026/rank.svg)](https://make.fun/bounty/news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/nonicon/world-news-25-november-2026/reward.svg)](https://make.fun/bounty/news-image-20261125)

A make.fun entry for the [news-image-20261125](https://make.fun/bounty/news-image-20261125) bounty: sum up 25 November's world news in one image.

`main.py` (Python 3, standard library only) draws the image procedurally — a
newspaper-style front page with six stories checked against news reported on
Wednesday 25 November 2026 — and writes it to `entry.png` (1024×1024, PNG).

## The six stories

1. **Ukraine** — Zelenskiy confirms Ukraine hit a Russian cargo ship in the
   Gulf of Finland and sank a Russian warship off Benghazi, Libya. Norway
   urges caution.
2. **Saudi Arabia** — A Houthi drone hits Riyadh's PIF Tower, the tallest
   tower in the capital, for the second time in a week; 11 people wounded.
3. **France** — Ex-president Sarkozy and his wife Carla Bruni are ordered to
   trial over alleged witness tampering in the Libya campaign-funding case.
4. **NATO** — The alliance plans early-warning aircraft over Poland after
   missiles landed there during an attack on Ukraine.
5. **Energy** — Iran says three oil tankers were hit by naval mines in the
   Strait of Hormuz.
6. **Sport** — Real Madrid beat PSV 5-1 (Bellingham, Mbappe brace); England
   level the T20 series in Australia.

A ticker along the foot adds the day's other headlines: Nvidia up 31.5% as
Huang returns as CEO, Trump pardons the Thanksgiving turkeys, Iraq orders
Kurdish oilfields seized, Senegal get their AFCON title back, and
Indonesia's vice-president resigns.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

The program reads no files and uses no network, so every run writes the exact
same bytes.

## License

MIT — see [LICENSE](LICENSE).
