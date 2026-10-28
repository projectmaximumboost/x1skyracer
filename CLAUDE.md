# Instructions for Claude: work from GitHub, not from loose local files

The single source of truth for the X1 SkyRacer design is this GitHub repository:

- Repo: https://github.com/projectmaximumboost/x1skyracer (public, read-only for everyone except invited collaborators)
- Working branch: `alpha`
- Owner account: `x1racing` (org `projectmaximumboost`)

From now on, start every session by syncing with GitHub, do your work on a branch, and finish every session by pushing to GitHub. Do not keep the only copy of anything on the local disk.

## 1. One-time: use a fresh copy of the GitHub repo

On 27 Oct 2026 the repo was cleaned up and its history was rewritten, so every old local copy is out of date. Do not push from an old copy of the folder, because that would put the deleted files back on GitHub.

The working copy is `/Users/johnmcalpine/X1_Racer_github`, a fresh clone with a remote named `skyracer`. The old folder `/Users/johnmcalpine/X1_Racer` is an untouched archive. Read it if you need something old, but never push from it.

If the working copy is missing, make it:

```bash
export GIT_SSH_COMMAND="ssh -i ~/.ssh/x1skyracer_deploy2 -o IdentitiesOnly=yes"
git clone -o skyracer -b alpha git@github.com:projectmaximumboost/x1skyracer.git /Users/johnmcalpine/X1_Racer_github
cd /Users/johnmcalpine/X1_Racer_github
git status -sb           # should say: alpha...skyracer/alpha with no changes
```

## 2. Folder layout on GitHub (keep it exactly)

`alpha` holds only the latest X1 SkyRacer design and the OPFPLG power plant. Do not reorganize, rename, or create parallel copies of folders.

- `README.md`: the public front page. Edit only when the project description changes.
- `assets/`: the logo used by the README.
- `rule-book/`: a copy of the X1 Racing Rule Book. The live version at https://x1racing.com/rule-book wins if they differ.
- `x1_skyracer_blender.py`: the procedural Blender script that builds the latest SkyRacer. Edit it in place.
- `X1_SkyRacer_FanTilt/`: the current design outputs (viewer, GLB, reports, helper scripts).
- `x1_opfplg_blender.py`, `OPFPLG/`, `X1_OPFPLG.glb`: the power plant models.
- Files with `.blend` or `.blend1` extensions are ignored by `.gitignore`. Rebuild them from the scripts.

Do not add games, website files, storyboards, articles, zips, older design variants, or anything from outside services. Those stay out of this repo. New design work updates the existing scripts in place, or adds a clearly named top-level folder such as `X1_SkyRacer_<Variant>/` after Mac OKs it. No `_v2`, `_final`, or `_copy` file names. History lives in git commits, not in file names.

## 3. Every session

```bash
cd /Users/johnmcalpine/X1_Racer_github
export GIT_SSH_COMMAND="ssh -i ~/.ssh/x1skyracer_deploy2 -o IdentitiesOnly=yes"
git fetch skyracer
git checkout alpha && git pull --ff-only skyracer alpha   # start from what is on GitHub
git checkout -b <short-topic>                              # e.g. fan-tilt-2, cockpit-fit
# ... do the work, commit small and often with clear messages ...
git push skyracer <short-topic>                            # push the topic branch
```

When the work is good, Mac says "merge" and it goes into `alpha`:

```bash
git checkout alpha
git pull --ff-only skyracer alpha
git merge --no-edit <short-topic>
git push skyracer alpha
```

Rules for commits:
- One idea per commit. Message format: `Area: what changed and why`, like `Fan-tilt: rear folding panel back to full thickness`.
- Never commit large binaries that the scripts can rebuild. GLB files and viewer HTML outputs are fine.
- Never commit passwords, tokens, or private keys.
- Never force-push (`--force`) and never rewrite history that is already on GitHub.
- If a push is rejected, `git pull --rebase skyracer alpha`, resolve conflicts, and push again. If it is not obvious, stop and ask Mac.

## 4. Canon wording (keep consistent in all text, commits, and docs)

- The aircraft is the **X1 SkyRacer** (renamed from "X1 Racer" in Oct 2026). Say "SkyRacer(s)", never "SkyCar(s)".
- The series is **X1 Racing**. "X1 Cup" is only the trophy race. The program is **Project MAXIMUM BOOST**.
- Say **SI**, never "AI".
- Racing is always unmanned and remotely piloted. The design itself is a **two-seat aircraft with a 500 lb passenger payload** intended for human transport. In race rules and sims, say "ballast" for the 500 lb carried in the seats.
- The SkyRacer folds to fit a race-car hauler and, unfolded, fits a standard two-car garage.
- Don't claim a built or flown vehicle. The project is at the concept and design stage.
- Do not mention NASCAR, hydrogen, or "grant".

## 5. If something does not match

Stop and tell Mac exactly what differs (file names, branch names, or the output of `git status -sb` and `git log --oneline -5`) rather than guessing. Do not delete local files or branches to make things match.
