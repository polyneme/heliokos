// JavaScript
customElements.define('hk-relationships', class extends HTMLElement {

	/**
	 * The class constructor object
	 */
	constructor () {

		// Always call super first in constructor
		super();

		// Set base properties
		this.denyList = JSON.parse(this.getAttribute('deny')) || [];

		// Connect to parent <hk-form>
		let form = this.closest('hk-form');
		if (form) {
			form.components.push(this);
		}

	}

	/**
	 * Handle event listeners
	 * @param  {Event} event The event object
	 */
	handleEvent (event) {
		this[`on${event.type}`](event);
	}

	/**
	 * Handle input events
	 * @param  {Event} event The event object
	 */
	oninput (event) {

		// If field isn't a select menu, ignore it
		if (!event.target.matches('select')) return;

		// Get all of the properties
		let selectors = Array.from(this.querySelectorAll('select'));
		let index = selectors.findIndex(field => field === event.target);
		let field = selectors[index];
		let otherIndex = index === 0 ? 1 : 0;
		let otherField = selectors[otherIndex];

		// Get disallowed values
		let disallow = this.denyList.filter(denyVals => {
			return denyVals[index] === field.value;
		}).map(vals => vals[otherIndex]);

		// Add currently selected value
		disallow.push(field.value);

		// Toggle disabled attribute on all applicable options
		for (let option of otherField.options) {
			if (field.value &&  disallow.includes(option.value)) {
				option.setAttribute('disabled', '');
			} else {
				option.removeAttribute('disabled');
			}
		}

	}

	/**
	 * Update the [deny] attribute
	 * @param  {Document} doc  The returned HTML
	 */
	updateDeny (doc) {
		if (!doc.body) return;
		let updated = doc.body.querySelector(`#${this.id}`);
		if (!updated) return;
		this.setAttribute('deny', updated.getAttribute('deny'));
	}

	/**
	 * Remove disabled attributes from all select options
	 */
	resetOptions () {
		for (let option of this.querySelectorAll('option:disabled')) {
			option.removeAttribute('disabled');
		}
	}

	/**
	 * Run callback when parent form submits successfully
	 * @param  {Element}  form The parent <hk-form> element
	 * @param  {Document} doc  The returned HTML
	 */
	onFormSuccess (form, doc) {
		this.updateDeny(doc);
		this.resetOptions();
	}

	/**
	 * Listen for form submissions when the form is attached in the DOM
	 */
	connectedCallback () {
		this.addEventListener('input', this);
	}

	/**
	 * Stop listening for form submissions when the form is attached in the DOM
	 */
	disconnectedCallback () {
		this.removeEventListener('input', this);
	}

	/**
	 * Runs when the value of an attribute is changed on the component
	 * @requires observedAttributes() method
	 * @param  {String} name     The attribute name
	 * @param  {String} oldValue The old attribute value
	 * @param  {String} newValue The new attribute value
	 */
	attributeChangedCallback (name, oldValue, newValue) {
		this.denyList = JSON.parse(newValue) || [];
	}

	/**
	 * Create a list of attributes to observe
	 * @return  {Array} The attributes to observe
	 */
	static get observedAttributes () {
		return ['deny'];
	}

});