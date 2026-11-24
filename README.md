# CV and Website

GitHub Pages serves the static site from the root of the main branch. [Sina Golara’s website](https://sinagolara.com/)

## Updating the site

1. Edit the shared records in `source/content.json` or the templates in `source/build_site.py`.
2. Edit styles, scripts, and site assets in `assets/`. Keep the headshot and legacy media images in `Images/`.
3. Run `python3 source/build_site.py` from the repository root to regenerate the four HTML pages.
4. Review the generated pages, then commit the source changes and their generated HTML together.

To build a separate preview folder, pass its path to `python3 source/build_site.py`. The preview build includes the local images, scripts, styles, and CV.
