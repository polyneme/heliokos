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
		this.handler = this.createSubmitHandler();

		// Define options
		this.preventDefault = this.hasAttribute('prevent-default');
		this.msgSubmitting = this.getAttribute('msg-submitting') || 'Submitting...';
		this.msgSuccess = this.getAttribute('msg-success') || 'Success!';
		this.msgError = this.getAttribute('msg-error') || 'Something went wrong. Please try again.';
		let target = this.getAttribute('target');
		this.targets = target ? target.split(',').map(target => target.trim()) : null;

	}

	/**
	 * Create a submit handler with the instance bound to the callback
	 * @return {Function} The callback function
	 */
	createSubmitHandler () {
		let instance = this;
		return async function (event) {

			// If the form is already submitting,
			// OR if default should be prevented
			// Stop form from reloading the page
			if (instance.isDisabled() || instance.preventDefault) {
				event.preventDefault();
			}

			// If the form is already submitting, do nothing
			// Otherwise, disable future submissions
			if (instance.isDisabled()) return;
			instance.disable();

			try {

				// Show status message
				instance.showStatus(instance.msgSubmitting);

				// If not preventing default behavior, end early
				if (!instance.preventDefault) return;

				// Call the API
				let {action, method} = event.target;
				let response = await fetch(action, {
					method,
					body: instance.serialize(),
					headers: {
						'Content-type': 'application/x-www-form-urlencoded'
					}
				});

				// If there's an error, throw
				if (!response.ok) throw response;

				// If UI should be updated, do so
				if (instance.targets) {
					let str = await response.text();
					instance.render(str);
				}

				// Show success URL
				instance.showStatus(instance.msgSuccess);

				// Clear the form
				instance.reset();

			} catch (error) {
				console.warn(error);
				instance.showStatus(instance.msgError);
			} finally {
				instance.enable();
			}

		};
	}

	/**
	 * Listen for form submissions when the form is attached in the DOM
	 */
	connectedCallback () {
		this.form.addEventListener('submit', this.handler);
	}

	/**
	 * Stop listening for form submissions when the form is attached in the DOM
	 */
	disconnectedCallback () {
		this.form.removeEventListener('submit', this.handler);
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
	 * Render the updated UI into the DOM
	 * @param  {String} str The HTML string for the updated UI
	 */
	render (str) {

		// Parse returned string into HTML
		let parser = new DOMParser();
		let doc = parser.parseFromString(str, 'text/html');
		if (!doc.body) return;

		// Render each target
		for (let selector of this.targets) {

			// Find target element in the DOM
			let target = document.querySelector(selector);
			if (!target) continue;

			// Get the target element from the returned HTML
			let updated = doc.body.querySelector(selector);
			if (!updated) continue;

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

});