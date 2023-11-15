import * as handlers from './components/handlers.js';

/**
 * Handle submit events
 * @param  {Event} event The event object
 */
async function submitHandler (event) {
	let fn = event.target.getAttribute('data-form');
	if (!fn || !handlers[fn]) return;
	handlers[fn](event);
}

// Listen for events
document.addEventListener('submit', submitHandler);