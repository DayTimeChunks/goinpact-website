Getting started
===============

The `main.py` and `models_v1.py` are the top files organising the app's functionality.

In the main file, the jinja environment is set as:

.. code-block:: python
   :emphasize-lines: 4

    template_dir = os.path.join(os.path.dirname(__file__), 'www')
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                                   extensions=['jinja2.ext.autoescape'],
                                   autoescape=True) # autoescape is important for security!!
