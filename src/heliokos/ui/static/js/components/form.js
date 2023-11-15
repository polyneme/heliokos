class Form {

	/**
	 * The Constructor object
	 * @param  {Element} form The form element
	 */
	constructor (form) {
		this.form = form;
	}

	/**
	 * Update the form status in a field
	 * @param  {String} msg The message to display
	 */
	showStatus (msg) {
		let elem = this.form.querySelector('[role="status"]');
		if (!elem) return;
		elem.innerHTML = msg;
	}

	/**
	 * Disable a form so I can't be submitted while waiting for the API
	 */
	disable () {
		this.form.setAttribute('data-submitting', '');
	}

	/**
	 * Enable a form after the API returns
	 */
	enable () {
		this.form.removeAttribute('data-submitting');
	}

	/**
	 * Reset the form element values
	 */
	reset () {
		this.form.reset();
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
	 * Check if a form is submitting to the API
	 * @return {Boolean} If true, the form is submitting
	 */
	isDisabled () {
		return this.form.hasAttribute('data-attribute');
	}

}


export default Form;