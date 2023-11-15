import Form from './form.js';


/**
 * Add new concept items to scheme list
 * @param {String} id    The concept ID
 * @param {String} label The concept label
 */
function addConceptToSchemeList (id, label) {

	// Get the list
	let list = document.querySelector('[data-list="scheme-concepts"]');
	if (!list) return;

	// Create list items
	let dt = document.createElement('dt');
	dt.textContent = 'concept';
	let dd = document.createElement('dd');
	dd.innerHTML = `<a href="/concept/${id}">${label}</a>`;

	// Append new items to the UI
	list.append(dt, dd);

}

/**
 * Add a new concept list item to the UI
 * @param {String} label The item label
 * @param {String} url   The item URL
 */
function addConceptItem (label, url) {

	// Get the list
	let list = document.querySelector('[data-list="concepts"]');
	if (!list) return;

	// Create the list item
	let item = document.createElement('li');
	item.innerHTML = `<li><a href="${url}">${label}</a></li>`;

	// Inject it into the UI
	list.prepend(item);

	// Check for "no concepts yet" message
	// If it exists, hide it
	let noMessage = document.querySelector('[data-message="no-concepts"]');
	if (!noMessage) return;
	noMessage.remove();

}

/**
 * Add a concept
 * @param  {Event} event The event object
 */
async function addConcept (event) {

	// Stop the form from reloading the page
	event.preventDefault();

	// Create a new form object
	let form = new Form(event.target);

	// If the form is already submitting, do nothing
	// Otherwise, disable future submissions
	if (form.isDisabled()) return;
	form.disable();

	try {

		// Show status message
		form.showStatus('Creating your concept...');

		// Call the API
		let {action, method} = event.target;
		let response = await fetch(action, {
			method,
			body: form.serialize(),
			headers: {
				'Content-type': 'application/x-www-form-urlencoded'
			}
		});

		// If there's an error, throw
		if (!response.ok) throw response;

		// Append the new concept to the list
		addConceptItem(event.target.pref_label.value, response.url);

		// Show success URL
		form.showStatus(`The "${event.target.pref_label.value}" concept was added.`);

		// Clear the form
		form.reset();

	} catch (error) {
		console.warn(error);
		form.showStatus('Something went wrong. Please try again.');
	} finally {
		form.enable();
	}

}

/**
 * Add a scheme
 * @param  {Event} event The event object
 */
async function addScheme (event) {

	// Create a new form object
	let form = new Form(event.target);

	// If the form is already submitting, do nothing
	// Otherwise, disable future submissions
	if (form.isDisabled()) {
		event.preventDefault();
		return;
	}
	form.disable();

	// Show status message
	form.showStatus('Creating a new scheme...');

}

/**
 * Add a concept to a scheme
 * @param  {Event} event The event object
 */
async function addConceptToScheme (event) {

	// Stop the form from reloading the page
	event.preventDefault();

	// Create a new form object
	let form = new Form(event.target);

	// If the form is already submitting, do nothing
	// Otherwise, disable future submissions
	if (form.isDisabled()) return;
	form.disable();

	try {

		// Get selected item
		let selected = event.target.selected_concept.options[event.target.selected_concept.selectedIndex];

		// Show status message
		form.showStatus(`Adding the "${selected.textContent}" concept...`);

		// Call the API
		let {action, method} = event.target;
		let response = await fetch(action, {
			method,
			body: form.serialize(),
			headers: {
				'Content-type': 'application/x-www-form-urlencoded'
			}
		});

		// If there's an error, throw
		if (!response.ok) throw response;

		// Append the new concept to the scheme list
		addConceptToSchemeList(selected.value, selected.textContent);

		// Show success URL
		form.showStatus(`The "${selected.textContent}" concept was added to the scheme.`);

		// Clear the form
		form.reset();

	} catch (error) {
		console.warn(error);
		form.showStatus('Something went wrong. Please try again.');
	} finally {
		form.enable();
	}

}


export {addConcept, addScheme, addConceptToScheme};