# Deploying your website to GitHub Pages

This guide is just for you. It is **not** part of the website folder, so it never
goes into the repository. (A GitHub Pages site on a free account must live in a
public repository, so anything inside the repo can be seen by anyone; that is why
this guide stays outside it.)

Your website files are in the `website/` folder (download `website.zip` from the
chat and unzip it). The final address will be **https://carloscoba.github.io**.

---

## 0. What you need

- A GitHub account: `CarlosCoba`.
- `git` installed on your computer (`git --version` to check).
- Optional, only for previewing locally: Ruby 3.x and Bundler (see step 6).

## 1. Back up your current website

Your old site lives in the repository `CarlosCoba/carloscoba.github.io`.

```bash
git clone https://github.com/CarlosCoba/carloscoba.github.io.git old-website-backup
```

Keep that folder somewhere safe; nothing below touches it.

## 2. Choose one of two ways

### Option A (recommended): replace the contents of the existing repository

This keeps the repository, its history and its address.

```bash
git clone https://github.com/CarlosCoba/carloscoba.github.io.git
cd carloscoba.github.io
git checkout -b main 2>/dev/null || git checkout main   # make sure you are on "main"

# remove the old site files (the .git folder is kept)
git rm -r -q .
# copy the new site in (adjust the path to where you unzipped website.zip)
cp -r /path/to/website/. .

git add -A
git commit -m "New website with Minimal Mistakes"
git push -u origin main
```

If your old repository uses `master` instead of `main`, either rename it on
GitHub (**Settings > General > Default branch**) or change `main` to `master`
in `.github/workflows/deploy.yml` (line `branches: [main]`).

### Option B: delete the old repository and start fresh

1. On GitHub open `carloscoba.github.io` > **Settings** > scroll to the bottom >
   **Delete this repository** (make sure you did the backup in step 1).
2. Create a new repository: **New repository**, name it exactly
   `carloscoba.github.io`, set it **Public**, and do **not** add a README.
3. Then upload the site:

```bash
cd /path/to/website
git init -b main
git add -A
git commit -m "New website with Minimal Mistakes"
git remote add origin https://github.com/CarlosCoba/carloscoba.github.io.git
git push -u origin main
```

(No git? You can also drag and drop the files on the repository page with
**Add file > Upload files**. Upload the *contents* of `website/`, including the
hidden `.github` folder; on macOS press `Cmd+Shift+.` in Finder to see it.)

## 3. Turn on GitHub Pages with GitHub Actions (one time)

1. In the repository go to **Settings > Pages**.
2. Under **Build and deployment > Source**, choose **GitHub Actions**.

That's all. Every push to `main` now runs the workflow in
`.github/workflows/deploy.yml`, which:

1. converts `_bibliography/publications.bib` into the publication list,
2. builds the site with Jekyll and the Minimal Mistakes theme,
3. publishes it.

Watch it run in the **Actions** tab. When it shows a green tick (1–3 minutes),
open https://carloscoba.github.io (you may need a hard refresh, `Ctrl+Shift+R`).

## 4. Updating your publications

1. In NASA ADS, search your papers (for example `orcid:0000-0003-1045-0702`),
   select all, then **Export > BibTeX**.
2. Save the file as `_bibliography/publications.bib`, replacing the old one.
3. Commit and push:

```bash
git add _bibliography/publications.bib
git commit -m "Update publications"
git push
```

Every entry links to its ADS page automatically (using the `adsurl` field, or the
bibcode, DOI or arXiv id). Your name is shown in bold; the spellings it looks for
are in `AUTHOR_SURNAMES` at the top of `scripts/bib2json.py`.

## 5. Editing other content

| To change | Edit |
|---|---|
| Home page text, research interests | `index.md` |
| CV page | `_pages/cv.md` |
| Code / XS3D tutorial | `_pages/code.md` |
| Sidebar (photo, bio, links), site title | `_config.yml` |
| Menu | `_data/navigation.yml` |
| Colours and styles | `assets/css/main.scss` |
| Photos and figures | `assets/images/` |
| CV PDF | `assets/files/CV.pdf` |

Pages are Markdown. After editing, commit and push; the site rebuilds itself.

## 6. Previewing on your computer (optional)

```bash
cd carloscoba.github.io
bundle config set --local path vendor/bundle
bundle install
python3 scripts/bib2json.py               # refresh the publication list
LANG=C.UTF-8 bundle exec jekyll serve     # open http://localhost:4000
```

## 7. Troubleshooting

- **Site still shows the old version**: check **Settings > Pages** says
  *GitHub Actions*, and that the latest run in **Actions** is green.
- **Workflow failed**: open the red run in **Actions** and read the step that
  failed. A malformed `.bib` entry makes the "Convert .bib" step fail; re-export
  it from ADS.
- **Workflow never runs**: the branch is not `main` (see Option A).
- **Sidebar icons missing**: they load from the internet; check your connection
  or ad blocker.
