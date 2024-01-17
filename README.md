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
# in a python 3.11 env
pip install -e '.[dev,tests,linting]'
```

Ensure you configure access to an accessible MongoDB instance.
To quickly achieve this with Docker ([link to install](https://docs.docker.com/engine/install/)),
```bash
docker run --name heliokos-mongo -d -v $(pwd)/heliokos-mongo-data:/data/db -p 23456:27017 mongo:6
```
The above will initialize and run a container based on DockerHub's `mongo:6` docker image, that is,
the latest `mongo` image with major version `6`. It maps your local port `23456` to the container's
port `27017` (what mongo exposes), and maps a local folder `heliokos-mongo-data` in your
current directory to the container's `/data/db` folder (where mongo stores its data). The folder
("volume") map is so that your mongo data can persist when stopping the docker container. The
container is called `heliokos-mongo`, and this process will detach (via `-d`) so that you don't need
to keep the terminal window open. You can check the status of the container with
```bash
docker ps -f name=heliokos-mongo
```
and stop and remove the container with
```bash
docker stop heliokos-mongo && docker remove heliokos-mongo
```
To re-initialize and run the container, recovering the last database state, re-run the `docker run` command above.

Before starting the Web server, ensure relevant environment variables (e.g. `MONGO_HOST`) are set in your shell session:
```bash
cp .env.example .env
# verify e.g. that a line `MONGO_HOST=localhost:23456` is present
export $(grep -v '^#' .env | xargs)
```

To start the Web server for development:
```bash
uvicorn heliokos.ui.main:app --reload
```

To load and step through the `heliokos_repl.ipynb` Jupyter notebook:
```bash
python -m ipykernel install --user --name heliokos
jupyter lab
# open `heliokos_repl.ipynb`, and ensure the kernel "Kernel > Change Kernel" is set to `heliokos`.
```

### Bill of Materials (BOM)

|name|description|website|origin|
|----|-----------|-------|------|
|fastapi|API framework|https://github.com/tiangolo/fastapi | https://pypi.org/project/fastapi |
|rdflib|RDF graph library|https://github.com/RDFLib/rdflib | https://pypi.org/project/rdflib |
|toolz|utility functions library|https://github.com/pytoolz/toolz | https://pypi.org/project/toolz |

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

### HTML

All UI interactions are either links (`<a href="...">`) or `<form>` elements that submit to the server.

Every `<form>` element should have a `method` attribute that defines the HTTP method, and an `action` attribute that defines the URL the `<form>` should submit to.

```html
<form method="post" action="/concept">
	<!-- Form fields... -->
</form>
```

### Web Components

The `app.js` file loads and initiates several Web Components that adds dynamic features and Ajax capabilities to interactive elements.

_**Note:** for readability, all of the required NASAWDS classes have been removed from the examples below._

#### `<hk-form>`

**Adds Ajax support to form submissions.**

Wrap `<form>` elements in the `<hk-form>` custom element to progressively add Ajax support.

By default, the `<hk-form>` element will add an accessible status notification element, show a `Submitting...` message, and prevent the user from submitting the form twice while waiting for a server response.

```html
<hk-form>
	<form method="post" action="/concept">
		<!-- Form fields... -->
	</form>
</hk-form>
```

##### Options & Settings

The `<hk-form>` element can also be customized with a handful of attributes...

- **`prevent-default`** - Stop the form from redirecting/reloading the page. Use this if you want to keep the user on the current page after the form submits.
- **`msg-submitting`** - Customize the "submitting" message. 
- **`msg-success`** - Customize the "success" message.
- **`msg-error`** - Customize the "error" message.
- **`target`** - If you want to update the current UI after the form successfully submits, provide one or more selector strings (comma-separated) for the element to update. Each selector should be identical in the current UI and the returned HTML from the server.

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

##### Custom Events

The `<hk-form>` element emits several custom events that you can hook into to extend functionality in your app.

- **`hk-form:submit`** is emitted when the form is submitting. An object of field names and values is assigned to the `event.detail` property.
- **`hk-form:success`** is emitted when the form is successfully submitted. The `event.detail` contains the response `html` and form field `data` as properties.
- **`hk-form:error`** is emitted when there's an error submitting the form. The `event.detail` contains the error object.

```js
document.addEventListener('hk-form:success', function (event) {

	// The submitted form web component
	let form = event.target;

	// The response HTML
	let html = event.detail.html;

	// The form data
	let data = event.detail.data;

});
```


#### `<hk-relationships>`

**Dynamically restricts certain scheme concept relationships.**

Wrap the `<select>` elements and radio buttons used for defining data relationships in the `<hk-relationships>` custom element to add a bit of extra functionality.

When the value of the `<select>` element changes, the `<hk-relationships>` component will disable that same value in the other `<select>` element. A `[key]` attribute is required.

```html
<hk-relationships key="scheme-relationships">
    <label for="subject_concept_id">Pick a Concept</label>
    <select id="subject_concept_id" name="subject_concept_id" required>
        <option value>- Select -</option>
        <!-- ... -->
    </select>

    <fieldset>
        <legend>Define how it's related</legend>

        <input id="relation_narrower" type="radio" name="relation" value="narrower" checked required>
        <label for="relation_narrower">is a broader concept than (<code>skos:narrower</code>)</label>
        
        <input id="relation_related" type="radio" name="relation" value="related" required>
        <label for="relation_related">is related to (<code>skos:related</code>)</label>
        
    </fieldset>

    <label for="object_concept_id">Pick another Concept</label>
    <select id="object_concept_id" name="object_concept_id" required>
        <option value>- Select -</option>
        <!-- ... -->
    </select>
</hk-relationships>
```

##### Options & Settings

The `<hk-relationships>` element can also be customized with two attributes...

- **`deny`** - An array of relationship combinations to disallow.
- **`key`** - A unique identified for the element. When the form is submitted, this is used to reset disabled fields and update the `[deny]` attribute.



#### `<hk-update-select>`

**Dynamically updates a `<select>` menu after form submission.**

Wrap the `<select>` element in the `<hk-update-select>` custom element to dynamically update it's `<option>` elements after the form is submitted. A `[key]` attribute is required.

```html
<hk-update-select key="add-concept">
    <label for="selected_concept">Pick a Concept</label>
    <select id="selected_concept" name="selected_concept" required>
        <option value>- Select -</option>
        <option value="earth">Earth</option>
        <option value="mars">Mars</option>
        <option value="jupiter">Jupiter</option>
    </select>
</hk-update-select>
```



#### `<hk-combo-box>`

**Convert an `input` into an API-driven type-ahead component.**

Wrap the `<input>` element in the `<hk-combo-box>` custom element, and provide an `[endpoint]` attribute that points to the data API. You can optionally set a `[delay]` attribute to specify how many milliseconds to wait before querying the API.

```html
<hk-combo-box endpoint="/concepts-search" delay="500">
  <label for="search">Text input label</label>
  <input id="search" name="search" required>
</hk-combo-box>
```

The component expects the API `endpoint` to return an array of objects. Each object should have an `id` and `value` that will be used to generate additional markup.

As the user types, a list of available options will be displayed in a `<datalist>`. A `[pattern]` attribute will be added to the `<input>` element with all of the available options for form validation purposes.

Additionally, a `type="hidden"` field will be added. It will have the same name as the `<input>`, with `-id` added to the end (ex `name="search-id"`). It's value will be dynamically set to the matching ID for the selected user text.



## Release Process

1. bump `version` in [pyproject.toml](/pyproject.toml).
2. git commit
3. git tag v$(pyproject.toml.version) # e.g. `git tag v0.0.5`.
4. python -m build
5. python -m twine upload dist/*
6. rm -rf dist
