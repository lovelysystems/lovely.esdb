# Shared Source Software
# Copyright (c) 2015, Lovely Systems GmbH

# -*- coding: utf-8 -*-

import os

# inject the VERSION constant used below
# This can be used because the build script updates the version number before
# building the RPM.
here = os.path.dirname(__file__)
project_root = os.path.dirname(here)

VERSION = '?'
execfile(os.path.join(project_root, 'lovely/esdb/__init__.py'))
docs_version = VERSION

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

nitpicky = True

extensions = ['sphinx.ext.doctest']

# load doctest extension to be able to setup testdata in the documentation that
# is hidden in the generated html (by using .. doctest:: :hide:)
extensions.append('sphinx.ext.doctest')

# General information about the project.
project = u'lovely.esdb'
from datetime import date
copyright = u'{year}, Lovely Systems GmbH'.format(year=date.today().year)

version = release = docs_version
exclude_patterns = ['service.egg-info', 'parts', 'checkouts']

html_theme = "default"
