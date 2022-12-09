# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'LaTeXBuddy'
copyright = '2022, LaTeXBuddy team'
author = 'LaTeXBuddy team'
release = '0.3.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser"
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_title = f"{project} documentation"
html_static_path = ['_static']
html_theme = "furo"
html_theme_options = {
    "light_logo": "logotype-light@2x.png",
    "dark_logo": "logotype-dark@2x.png",
    "sidebar_hide_name": True,
    "source_repository": "https://gitlab.com/LaTeXBuddy/LaTeXBuddy",
    "source_branch": "master",
    "source_directory": "docs/",

    "light_css_variables": {
        "color-brand-primary": "#008281",
    },

    "footer_icons": [
        {
            "name": "GitLab",
            "url": "https://gitlab.com/LaTeXBuddy/LaTeXBuddy",
            "html": """
                <svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>GitLab</title><path d="m23.6004 9.5927-.0337-.0862L20.3.9814a.851.851 0 0 0-.3362-.405.8748.8748 0 0 0-.9997.0539.8748.8748 0 0 0-.29.4399l-2.2055 6.748H7.5375l-2.2057-6.748a.8573.8573 0 0 0-.29-.4412.8748.8748 0 0 0-.9997-.0537.8585.8585 0 0 0-.3362.4049L.4332 9.5015l-.0325.0862a6.0657 6.0657 0 0 0 2.0119 7.0105l.0113.0087.03.0213 4.976 3.7264 2.462 1.8633 1.4995 1.1321a1.0085 1.0085 0 0 0 1.2197 0l1.4995-1.1321 2.4619-1.8633 5.006-3.7489.0125-.01a6.0682 6.0682 0 0 0 2.0094-7.003z"/></svg>
            """,
            "class": "",
        },
    ],
}
