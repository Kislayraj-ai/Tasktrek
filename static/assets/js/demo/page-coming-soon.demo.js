/*
Template Name: STUDIO DJANGO - Responsive Bootstrap 5 Admin Template
Version: 5.0.0
Author: Sean Ngu
Website: http://www.seantheme.com/studio/
*/

var handleRenderCountdownTimer = function() {
	var newYear = new Date();
	newYear = new Date(newYear.getFullYear() + 1, 1 - 1, 1);
	$('#timer').countdown({until: newYear});
};


/* Controller
------------------------------------------------ */
$(document).ready(function() {
	handleRenderCountdownTimer();
});