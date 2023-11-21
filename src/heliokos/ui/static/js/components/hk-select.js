// JavaScript
customElements.define('hk-select', class extends HTMLElement {

	/**
	 * The class constructor object
	 */
	constructor () {

		// Always call super first in constructor
		super();

		// Set base properties
		this.select = this.querySelector('select');
		this.handler = this.createInputHandler();

		// Define options
		let disableMatch = this.getAttribute('disable-match');
		this.disableMatches = disableMatch ? disableMatch.split(',').map(match => match.trim()) : null;

	}

	/**
	 * Create an input handler with the instance bound to the callback
	 * @return {Function} The callback function
	 */
	createInputHandler () {
		return (event) => {
			for (let selector of this.disableMatches) {

				// Get the target element
				let target = document.querySelector(selector);
				if (!target) continue;

				// Toggle disabled attribute on each option
				for (let option of target.options) {
					if (option.value === event.target.value && event.target.value) {
						option.setAttribute('disabled', '');
					} else {
						option.removeAttribute('disabled');
					}
				}

			}
		};
	}

	/**
	 * Listen for form submissions when the form is attached in the DOM
	 */
	connectedCallback () {
		if (!this.disableMatches) return;
		this.select.addEventListener('input', this.handler);
	}

	/**
	 * Stop listening for form submissions when the form is attached in the DOM
	 */
	disconnectedCallback () {
		this.select.removeEventListener('input', this.handler);
	}

});