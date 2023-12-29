// JavaScript
customElements.define('hk-form', class extends HTMLElement {

	/**
	 * The class constructor object
	 */
	constructor () {

		// Always call super first in constructor
		super();

		// Add a form status element
		let announce = document.createElement('div');
		announce.setAttribute('role', 'status');
		this.append(announce);

		// Set base properties
		this.announce = announce;
		this.form = this.querySelector('form');

		// Define options
		this.preventDefault = this.hasAttribute('prevent-default');
		this.msgSubmitting = this.getAttribute('msg-submitting') || 'Submitting...';
		this.msgSuccess = this.getAttribute('msg-success') || 'Success!';
		this.msgError = this.getAttribute('msg-error') || 'Something went wrong. Please try again.';
		let target = this.getAttribute('target');
		this.targets = target ? target.split(',').map(target => target.trim()) : null;

	}

	/**
	 * Handle event listeners
	 * @param  {Event} event The event object
	 */
	handleEvent (event) {
		this[`on${event.type}`](event);
	}

	/**
	 * Handle submit events
	 * @param {Event} The event object
	 */
	async onsubmit (event) {

		// If the form is already submitting,
		// OR if default should be prevented
		// Stop form from reloading the page
		if (this.isDisabled() || this.preventDefault) {
			event.preventDefault();
		}

		// If the form is already submitting, do nothing
		if (this.isDisabled()) return;

		// Emit a submit event (useful for validations)
		let data = this.getData();
		if (!this.emit('submit', data)) return;

		// Disable future submissions
		this.disable();

		try {

			// Show status message
			this.showStatus(this.msgSubmitting);

			// If not preventing default behavior, end early
			if (!this.preventDefault) return;

			// Call the API
			let {action, method} = event.target;
			let response = await fetch(action, {
				method,
				body: this.serialize(),
				headers: {
					'Content-type': 'application/x-www-form-urlencoded'
				}
			});

			// If there's an error, throw
			if (!response.ok) throw response;

			// Get HTML response
			let str = await response.text();
			let html = this.stringToHTML(str);

			// If UI should be updated, do so
			this.render(html);

			// Show success URL
			this.showStatus(this.msgSuccess);

			// Emit event
			this.emit('success', {html, data});

			// Clear the form
			this.reset();

		} catch (error) {
			console.warn(error);
			this.showStatus((await error.json()).detail || this.msgError);
			this.emit('error', error);
		} finally {
			this.enable();
		}

	}

	/**
	 * Listen for form submissions when the form is attached in the DOM
	 */
	connectedCallback () {
		this.form.addEventListener('submit', this);
	}

	/**
	 * Stop listening for form submissions when the form is attached in the DOM
	 */
	disconnectedCallback () {
		this.form.removeEventListener('submit', this);
	}

	/**
	 * Disable a form so I can't be submitted while waiting for the API
	 */
	disable () {
		this.setAttribute('form-submitting', '');
	}

	/**
	 * Enable a form after the API returns
	 */
	enable () {
		this.removeAttribute('form-submitting');
	}

	/**
	 * Check if a form is submitting to the API
	 * @return {Boolean} If true, the form is submitting
	 */
	isDisabled () {
		return this.hasAttribute('form-submitting');
	}

	/**
	 * Get the value of a form field by its [name]
	 * @param  {String} id The field name
	 * @return {String}    The value
	 */
	getFieldValue (id) {

		// Get the field
		let field = this.form.querySelector(`[name="${id}"]`);
		if (!field) return;

		// If select element, get selected element text
		if (field.tagName.toLowerCase() === 'select') {
			return field.options[field.selectedIndex].textContent;
		}

		// Otherwise, return value
		return field.value;

	}

	/**
	 * Replace placeholders in message with field values
	 * @param  {String} msg The message text
	 * @return {String}     The message text with placeholders replaced
	 */
	getMessageText (msg) {
		let instance = this;
		return msg.replace(/\$\{([^}]+)\}/g, function (match) {

			// Remove the wrapping curly braces
			match = match.slice(2, -1);

			// Get the field value
			let value = instance.getFieldValue(match);

			// Return the string
			if (!value) return '{{' + match + '}}';
			return value;

		});
	}

	/**
	 * Update the form status in a field
	 * @param  {String} msg The message to display
	 */
	showStatus (msg) {
		this.announce.innerHTML = this.getMessageText(msg);
	}

	/**
	 * Serialize all form data into an object
	 * @return {Object} The serialized form data
	 */
	serialize () {
		let data = new FormData(this.form);
		let params = new URLSearchParams();
		for (let [key, val] of data) {
			params.append(key, val);
		}
		return params.toString();
	}

	/**
	 * Serialize all form data into an object
	 * @return {Object} The serialized form data
	 */
	getData () {
	    let data = new FormData(this.form);
	    let obj = {};
	    for (let [key, value] of data) {
	        if (obj[key] !== undefined) {
	            if (!Array.isArray(obj[key])) {
	                obj[key] = [obj[key]];
	            }
	            obj[key].push(value);
	        } else {
	            obj[key] = value;
	        }
	    }
	    return obj;
	}

	/**
	 * Convert an HTML string into DOM nodes
	 * @param  {String}  str The HTML string
	 * @return {Element}     A document.body with the HTML nodes
	 */
	stringToHTML (str) {
		let parser = new DOMParser();
		let doc = parser.parseFromString(str, 'text/html');
		return doc.body ? doc.body : document.createElement('body');
	}

	/**
	 * Render the updated UI into the DOM
	 * @param {Element} html The response HTML
	 */
	render (html) {

		if (!this.targets || !html) return;

		// Update each target
		for (let selector of this.targets) {

			// Get the target element from the returned HTML
			let updated = html.querySelector(selector);
			if (!updated) continue;

			// Find target element in the DOM
			let target = document.querySelector(selector);
			if (!target) continue;

			// Update the UI
			target.replaceWith(updated);

		}

	}

	/**
	 * Reset the form element values
	 */
	reset () {
		this.form.reset();
	}

	/**
	 * Emit a custom event
	 * @param  {String} type   The event type
	 * @param  {Object} detail Any details to pass along with the event
	 */
	emit (type, detail = {}) {

		// Create a new event
		let event = new CustomEvent(`hk-form:${type}`, {
			bubbles: true,
			cancelable: true,
			detail: detail
		});

		// Dispatch the event
		return this.dispatchEvent(event);

	}

});