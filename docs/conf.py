# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(os.path.abspath('.')).parents[0]))
print(str(pathlib.Path(os.path.abspath('.')).parents[0]))

project = 'stock-bot-gav'
copyright = '2022, barbarich vi, taranenko gs, tsoi as, burkina es'
author = 'barbarich vi, taranenko gs, tsoi as, burkina es'
release = '0.0.1'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinxcontrib.katex',
    'sphinx.ext.autosectionlabel',
    'sphinx_copybutton',
    'sphinx.ext.graphviz'
]
copybutton_prompt_text = r'>>> |\.\.\. |\$ |'
copybutton_prompt_is_regexp = True
latex_engine = 'xelatex'
# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'press'
html_static_path = ['_static']

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".


add_module_names = False
autodoc_typehints = "description"
autodoc_class_signature = "separated"
latex_elements = {'extraclassoptions': 'openany,oneside',
                  'extrapackages': r'\usepackage{tikz}'
                                   r'\usetikzlibrary{shapes,positioning}'
                                   r'\usepackage{amsmath}'}

math_number_all = True
math_numfig = False
latex_use_xindy = False

# -- GraphViz configuration ----------------------------------
graphviz_output_format = 'svg'

html_js_files = [
    "require.min.js",  # Add to your _static
    "custom.js"
]
