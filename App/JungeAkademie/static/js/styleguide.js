/**
 * Created by scheibo on 03.02.2015.
 */
(function ($, window, document, undefined) {

	var theLocation = window.location.pathname.substring(1);

	// ---- F U N C T I O N S -----
	function toggleNavigationLevel2() {
		$("a[href*='" + theLocation + "']").next('ul').show();
	}
	// ---- F U N C T I O N S -----
	function setActiveNav() {
		$("a[href*='" + theLocation + "']").addClass('styleguide__navigation__item--active');
	}

	function toggleMarkup() {
		$('.styleguide__example__markup__button').click(function() {
			if($(this).parent().hasClass('styleguide__example__markup--open')) {
				$(this).parent().removeClass('styleguide__example__markup--open');
			} else {
				$(this).parent().addClass('styleguide__example__markup--open');
			}
		});
	}

	function toggleNavigation() {
		$('#styleguide__navigation__toggle').click(function() {
			if($.cookie('styleguidenavigation')) {
				$.removeCookie('styleguidenavigation');
				$('.flex-container').removeClass('styleguide__navigation--hide');
			} else {
				$.cookie('styleguidenavigation', 1);
				$('.flex-container').addClass('styleguide__navigation--hide');
			}
		});
	}

	// ---- O N   D O M   R E A D Y ---

	$(function () {
		// ----- init functions -----
		toggleNavigationLevel2();
		toggleMarkup();
		setActiveNav();
		toggleNavigation();

    prettyPrint();

		if($.cookie('styleguidenavigation')) {
			$('.flex-container').addClass('styleguide__navigation--hide');
		} else {
			$('.flex-container').removeClass('styleguide__navigation--hide');
		}
	});

}(jQuery, window, document));