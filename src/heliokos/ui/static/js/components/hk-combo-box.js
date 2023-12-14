// JavaScript
customElements.define('hk-combo-box', class extends HTMLElement {

	/**
	 * The class constructor object
	 */
	constructor () {

		// Always call super first in constructor
		super();

		// Set base properties
		this.input = this.querySelector('input');
		this.list = this.querySelector('ul');

		// Render UI
		this.init();

	}

	/**
	 * Initialize the UI
	 */
	init () {
		let wrapper = document.createElement('div');
		wrapper.className = 'hk-combo-box';
		wrapper.innerHTML =
			`<span class="usa-combo-box__input-button-separator">&nbsp;</span>
			<span class="usa-combo-box__toggle-list__wrapper" tabindex="-1"><button type="button" tabindex="-1" class="usa-combo-box__toggle-list" aria-label="Toggle the dropdown list">&nbsp;</button></span>`;
		this.append(wrapper);
		wrapper.prepend(this.input);
		wrapper.append(this.list);
		this.toggle = wrapper.querySelector('button');
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

});