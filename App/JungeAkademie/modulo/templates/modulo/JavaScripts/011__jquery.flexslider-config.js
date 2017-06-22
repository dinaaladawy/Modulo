jQuery(document).ready(function ($) {
	$('.tx-in2flexslider').each(function() {
		var ceuid = $(this).attr('id');
		var options = new Array();

		// Defaults
		options['reverse'] = false;
		options['initDelay'] = 5000;
		options['slideshowSpeed'] = 12000;
		options['animationSpeed'] = 2000;

		// Individual configuration
		if ($('#' + ceuid + ' .settings_additional_animation').html()) {
			options['animation'] = $('#' + ceuid + ' .settings_additional_animation').html();
		}
		if ($('#' + ceuid + ' .settings_additional_controlNav').html()) {
			options['controlNav'] = ($('#' + ceuid + ' .settings_additional_controlNav').html() === "true");
		}
		if ($('#' + ceuid + ' .settings_additional_animationLoop').html()) {
			options['animationLoop'] = ($('#' + ceuid + ' .settings_additional_animationLoop').html() === "true");
		}
		if ($('#' + ceuid + ' .settings_additional_slideshow').html()) {
			options['slideshow'] = ($('#' + ceuid + ' .settings_additional_slideshow').html() === "true");
		}
		if (parseInt($('#' + ceuid + ' .settings_additional_itemWidth').html()) > 0) {
			options['itemWidth'] = parseInt($('#' + ceuid + ' .settings_additional_itemWidth').html());
		}
		if (parseInt($('#' + ceuid + ' .settings_additional_itemMargin').html()) > 0) {
			options['itemMargin'] = parseInt($('#' + ceuid + ' .settings_additional_itemMargin').html());
		}
		if (parseInt($('#' + ceuid + ' .settings_additional_minItems').html()) > 0) {
			options['minItems'] = parseInt($('#' + ceuid + ' .settings_additional_minItems').html());
		}
		if (parseInt($('#' + ceuid + ' .settings_additional_maxItems').html()) > 0) {
			options['maxItems'] = parseInt($('#' + ceuid + ' .settings_additional_maxItems').html());
		}
		if (parseInt($('#' + ceuid + ' .settings_additional_initDelay').html()) > 0) {
			options['initDelay'] = parseInt($('#' + ceuid + ' .settings_additional_initDelay').html());
		}
		if (parseInt($('#' + ceuid + ' .settings_additional_slideshowSpeed').html()) > 0) {
			options['slideshowSpeed'] = parseInt($('#' + ceuid + ' .settings_additional_slideshowSpeed').html());
		}
		if (parseInt($('#' + ceuid + ' .settings_additional_animationSpeed').html()) > 0) {
			options['animationSpeed'] = parseInt($('#' + ceuid + ' .settings_additional_animationSpeed').html());
		}

		// TODO: Remove this hack if it's fixed in the FlexSlider plugin
		/* Part of a hack to avoid fade-in effect on first slide (visit
		https://github.com/woothemes/FlexSlider/issues/848#issuecomment-42573918). */
		options['start'] = function(slider) {
			slider.removeClass('loading');
		};

		$('#' + ceuid + ' .flexslider').flexslider(options);

		$('#' + ceuid + ' .flexslider_carousel').flexslider( {
			animation: $('#' + ceuid + ' .settings_additional_animation').html(),
			useCSS: true,
			controlNav: false,
			animationLoop: false,
			slideshow: false,
			itemWidth: parseInt($('#' + ceuid + ' .settings_additional_itemWidth').html()),
			itemMargin: parseInt($('#' + ceuid + ' .settings_additional_itemMargin').html()),
			asNavFor: '#' + ceuid + ' .flexslider_slider'
		} );

		$('#' + ceuid + ' .flexslider_slider').flexslider( {
			animation: $('#' + ceuid + ' .settings_additional_animation').html(),
			useCSS: true,
			controlNav: false,
			animationLoop: false,
			slideshow: false,
			sync:'#' + ceuid + ' .flexslider_carousel'
		} );
	} )
} );
