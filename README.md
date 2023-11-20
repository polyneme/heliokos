# heliokos
A knowledge organization system (KOS) service for Heliophysics.

## Use

Executable [functional tests](tests/test_functions.py) describe target use cases. Currently, the first two tests pass,
so you can follow their bodies as usage examples. The rest of the functional test suite can be considered a roadmap
for this tool.

You can `pip install heliokos` to get the last-released version,
or you can `git clone` this repository and `pip install .` to build the tool using the current `main`-branch head.

## Setup

`git clone` this repository, and in the root directory,
```bash
pip install -e .
```

### Bill of Materials (BOM)

|name|description|website|origin|
|----|-----------|-------|------|
|fastapi|API framework|https://github.com/tiangolo/fastapi | https://pypi.org/project/fastapi |
|rdflib|RDF graph library|https://github.com/RDFLib/rdflib | https://pypi.org/project/rdflib |
|toolz|utility functions library|https://github.com/pytoolz/toolz | https://pypi.org/project/toolz |


To start the Web server for development:
```bash
uvicorn heliokos.ui.main:app --reload
```

## Testing

```bash
# Example: run linting and tests for single module
tox run -e lint,py311 -- tests/test_units.py
# Example run single test by name
tox run -e py311 -- -k test_harmonizing_two_concept_schemes
# Example: run all tests
tox
```

## Front End Development

The front-end UI uses the [NASA Web Design System (NASAWDS)](https://github.com/bruffridge/nasawds), a rethemed version of the [US Web Design System (USWDS)](https://designsystem.digital.gov/). Use the USWDS site for documentation on how to style things.

HTML files for the various routes can be found in the `/ui/templates` directory. They use python for templating.

Client-side assets are located in the `/ui/static` directory. It includes subdirectories for `/css`, `/js`, and `/img` files. The NASAWDS files are located in a dedicated `/nasawds` subdirectory.

```
|- /ui
   |- /templates
   |- /static
      |- /css
      |- /img
      |- /js
      |- /nasawds
```

There is _no_ build step for front end assets.

### Philosophy

The entire app is server-rendered and progressively enhanced. 

All UI interactions are either links or `<form>` elements that submit to the server, which handles processing and redirects. Without JavaScript, the app works perfectly fine.

If JavaScript _is_ available, a custom `<hk-form>` Web Component adds Ajax support for `<form>` elements and provides a more modern experience (more details on how that works below).

### CSS

The HelioKOS app loads two stylesheets.

- **`/nasawds/css/styles.css`** - the main NASAWDS stylesheet.
- **`/css/app.css`** - customizations, overrides, and utility classes to extend the base stylesheet.

### JavaScript

The HelioKOS app loads two JavaScript files.

- **`/nasawds/js/uswds.min.js`** - the main NASAWDS component JavaScript.
- **`/js/app.js`** - the main app-specific JavaScript.

The `app.js` file loads and initiates the `<hk-form>` Web Component that adds Ajax capabilities to `<form>` elements.

### HTML

All UI interactions are either links (`<a href="...">`) or `<form>` elements that submit to the server.

Every `<form>` element should have a `method` attribute that defines the HTTP method, and an `action` attribute that defines the URL the `<form>` should submit to.

```html
<form method="post" action="/concept">
	<!-- Form fields... -->
</form>
```

Wrap `<form>` elements in the `<hk-form>` custom element to progressively add Ajax support.

By default, the `<hk-form>` element will add an accessible status notification element, show a `Submitting...` message, and prevent the user from submitting the form twice while waiting for a server response.

```html
<hk-form>
	<form method="post" action="/concept">
		<!-- Form fields... -->
	</form>
</hk-form>
```

The `<hk-form>` element can also be customized with a handful of attributes...

- **`prevent-default`** - Stop the form from redirecting/reloading the page. Use this if you want to keep the user on the current page after the form submits.
- **`msg-submitting`** - Customize the "submitting" message. 
- **`msg-success`** - Customize the "success" message.
- **`msg-error`** - Customize the "error" message.
- **`target`** - If you want to update the current UI after the form successfully submits, provide a selector string for the element to update. It should be identical on the current UI and the returned HTML from the server.

With the `msg-submitting`, `msg-success`, and `msg-error` attributes, you can include `${field_name}` in the attribute string to include the value of the matching field in your message.

```html
<!-- 
	This form includes some customizations.
	After submitting, it will update the [data-hk-list="concepts"] element with new HTML.
-->
<hk-form 
	prevent-default 
	msg-submitting='Creating the "${pref_label}" concept...' 
	msg-success='The "${pref_label}" concept was added.' 
	target='[data-hk-list="concepts"]'
>
	<form method="post" action="/concept">
		<label for="pref_label">Preferred Label</label>
		<input id="pref_label" name="pref_label" type="text" required>
		<button>
			Create Concept
		</button>
	</form>
</hk-form>

<!-- This gets updated after the form submits -->
<div data-hk-list="concepts">
	<h2>Your Concepts</h2>
	<p>You don't have any concepts yet.</p>
</div>
```

_**Note:** for readability, all of the required NASAWDS classes have been removed from this example._


## Release Process

1. bump `version` in [pyproject.toml](/pyproject.toml).
2. git commit
3. git tag v$(pyproject.toml.version) # e.g. `git tag v0.0.5`.
4. python -m build
5. python -m twine upload dist/*
6. rm -rf dist
