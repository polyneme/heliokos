// JavaScript
customElements.define('hk-restrict-select', class extends HTMLElement {

	/**
	 * The class constructor object
	 */
	constructor () {

		// Always call super first in constructor
		super();

		// Set base properties
		this.select = this.querySelector('select');
		this.key = this.getAttribute('key');

	}

	/**
	 * Handle event listeners
	 * @param  {Event} event The event object
	 */
	handleEvent (event) {
		if (event.type === 'hk-form:success') {
			this.onFormSuccess(event.detail.html);
		} else {
			this[`on${event.type}`](event);
		}
	}

	/**
	 * Run callback when parent form submits successfully
	 * @param  {Element}  html The returned HTML
	 */
	onFormSuccess (html) {
		if (!html) return;
		let updated = html.querySelector(`hk-restrict-select[key="${this.key}"] select`);
		if (!updated) return;
		this.select.innerHTML = updated.innerHTML;
	}

	/**
	 * Listen for form submissions when the form is attached in the DOM
	 */
	connectedCallback () {
		let form = this.closest('hk-form');
		if (!form) return;
		form.addEventListener('hk-form:success', this);
	}

	/**
	 * Stop listening for form submissions when the form is attached in the DOM
	 */
	disconnectedCallback () {
		let form = this.closest('hk-form');
		if (!form) return;
		form.removeEventListener('hk-form:success', this);
	}

});