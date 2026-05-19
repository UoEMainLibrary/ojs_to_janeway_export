#  Open Journal Systems to Janeway export scripts

This repository contains various Python scripts for exporting data from OJS 3.4's REST API for import into Janeway. These scripts were designed against Edinburgh Diamond's OJS instances.

Edinburgh Diamond, situated within Edinburgh University Library, offers free publishing services to support Diamond Open Access books and journals created by University of Edinburgh academics and students. https://library.ed.ac.uk/research-support/edinburgh-diamond

Edinburgh University Library offers a journal and book hosting service to members of the Scottish Confederation of University & Research Libraries (SCURL), as well as external organisations. https://library.ed.ac.uk/research-support/open-hosting-service. 

## imports

All exports are formatted as CSVs suitable for import using the Janeway Imports plugin which is available at https://github.com/openlibhums/imports and documented at https://janeway-imports.readthedocs.io/en/latest/index.html. 

## .env

If using Docker Compose to run these scripts, first copy the .env.template file to .env and fill in the variables for the OJS instance from which you are exporting. 

## list_issues.py

list_issues.py reads the OJS REST API and returns a list of issues for a particular journal along with issue IDs and the context_id of the journal. 

### usage

`python3 list_issues.py --base-url https://your-ojs.org --journal-path JOURNAL_PATH --api-key YOUR_API_KEY`

or

`docker compose run --rm list_issues`

## export_issue.py

export_issue.py exports a single journal issue from OJS in the format required for upload via the Janeway Import plugin's Import / Export / Update function documented at https://janeway-imports.readthedocs.io/en/latest/import_export_update.html. It also produces a CSV of accompanying images for articles in the format documented at https://janeway-imports.readthedocs.io/en/latest/article_images.html. 

### usage

`python3 export_issue.py --base-url https://your-ojs.org --journal-path JOURNAL_PATH --api-key YOUR_API_KEY --issue-id ISSUE_ID --journal-code YOUR_JANEWAY_JOURNAL_CODE --output FILENAME.csv`

or

`docker compose run --rm export_issue`

## export_all_issues.py

export_all_issues.py exports all published articles from all issues of a journal in the format required for upload via the Janeway Import plugin's Import / Export / Update function documented at https://janeway-imports.readthedocs.io/en/latest/import_export_update.html. It also produces a CSV of accompanying images for articles in the format documented at https://janeway-imports.readthedocs.io/en/latest/article_images.html. 

This batches issues into multiple CSV files because of the Janeway Import plugin's timeout settings for large imports. The default is batches of twenty issues. 

### usage

`python3 export_all_issues.py --base-url https://your-ojs.org --journal-path JOURNAL_PATH --api-key YOUR_API_KEY --journal-code YOUR_JANEWAY_JOURNAL_CODE --output-dir ./output_directory`

or

`docker compose run --rm export_all_issues`

## export_editors.py

export_editors.py exports a list of editor users from OJS in the format required for upload via the Janeway Import plugin's Editors Import function documented at https://janeway-imports.readthedocs.io/en/latest/editor_import.html.

### usage

`python3 export_editors.py --base-url https://your-ojs.org --journal-path JOURNAL_PATH --api-key YOUR_API_KEY --output FILENAME.csv`

or

`docker compose run --rm export_editors`

## export_editorial.py

export_editorial.py exports a list of editor users from OJS in the format required for upload via the Janeway Import plugin's Editorial Team Import function documented at https://janeway-imports.readthedocs.io/en/latest/editorial_team_import.html. Editorial Team is the public-facing list of the editorial team in Janewy and I wouldn't have bothered to add this script but it's so similar to Editor Import.

### usage

`python3 export_editorial.py --base-url https://your-ojs.org --journal-path JOURNAL_PATH --api-key YOUR_API_KEY --output FILENAME.csv`

or

`docker compose run --rm export_editorial`

## export_reviewers.py

export_reviewers.py exports a list of reviewer users from OJS in the format required for upload via the Janeway Import plugin's Reviewer Import function documented at https://janeway-imports.readthedocs.io/en/latest/reviewer_import.html.

### usage

`python3 export_reviewers.py --base-url https://your-ojs.org --journal-path JOURNAL_PATH --api-key YOUR_API_KEY --output FILENAME.csv`

or

`docker compose run --rm export_reviewers`

## caveats / to-dos

- When there are no PDF galleys available, the export scripts instead use the HTML galleys. When these are imported into Janeway, the image src links point to the old OJS instance. This is fine as long as that instance remains up but for a full migration to Janeway, images would need to be migrated and these image links would need to be updated.
- The Editors Import and Reviewers Import import users but they're all marked as inactive. There is surely a way to bulk activate them all.