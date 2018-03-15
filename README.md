# HelpScout Docs to Markdown Export Tool

Simple Python utility to export HelpScout docs to Markdown/Frontmatter files.

## Usage

Install dependencies with `pipenv`:

```
$ pipenv install
```

Create a `.env` file with your HelpScout API Key:

```
$ echo 'HELPSCOUT_API_KEY=...' > .env
```

Run the utility:

```
$ pipenv run python export.py
```

It will create a directory named `articles` with sub-directory for each collection you have in HelpScout docs. It will also create two files: `categories.json` and `collections.json` with your categories and collections.
