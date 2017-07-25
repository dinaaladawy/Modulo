/**
 * Die Slides sollen immer den ganzen Rahmen ausfüllen und mittig platziert
 * sein, unabhängig von Bild- und Bildschirmgröße. Das ist am leichtesten
 * mit der CSS-Eigenschaft "background-size: cover" erreichbar. Deshalb
 * werden hier die Bildelemente (<img />) entfernt und die entsprechenden
 * Bildquellen fürs background-image verwendet.
 *
 * Das ließe sich gewiss auch lösen ohne die Bildelemente überhaupt erst zu
 * rendern (werden hier ja ohnehin wieder entfernt).
 */
function changeRoyalSlidesToBackgroundImages() {
	$('.royal-slider-element').each(function() {
		var link = $(this).find('.js-royal-slider-element-img');

		if (link) {
			var image = $(this).find('img');
			var imageSrc = image.attr('src');

			link.css('background-image', 'url(' + imageSrc + ')');
			link.removeClass('js-royal-slider-element-img');
			image.remove();
		}
	});
}

/**
 * Das mobile Hauptmenü soll nicht mehr auf Hover reagieren, sondern nur noch
 * per Klicks funktionieren. Der Hover-Effekt, der auf Desktops gebraucht wird,
 * würde die Toggle-Funktion von jQuery stören. Auf Desktops könnte so die
 * mobile Navigation nicht benutzt werden (z. B. für Testzwecke).
 */
enquire.register("only screen and (max-width: 799px)", {
	match: function() {
		$(".js-main-nav-item-1-level").removeClass("main-nav__item-1-level--hover");
	},
	unmatch: function() {
		$(".js-main-nav-item-1-level").addClass("main-nav__item-1-level--hover");
		$(".js-main-nav, .js-main-nav *").removeAttr('style').removeClass("main-nav__toggle--minus");
		$(".js-directory-nav-item, .js-directory-nav-item *").removeAttr('style').removeClass("directory-nav__item--is-active");
	}
});

(function($) {
	$(function() {
		/**************
		 *  FancyBox
		 *************/
		$('.fancybox').fancybox({
			hideOnContentClick: true,
			prevEffect: 'fade',
			nextEffect: 'fade'
		});
		$(".various").fancybox({
			maxWidth: 800,
			maxHeight: 600,
			fitToView: false,
			width: '70%',
			height: '70%',
			autoSize: false,
			closeClick: false,
			openEffect: 'none',
			closeEffect: 'none'
		});

		/**************
		 *  SEARCH
		 *************/
		if ($('.indexedsearch').val() == '') {
            $('.indexedsearch').addClass('watermark');
		}
        else {
            $('.indexedsearch').removeClass('watermark');
        }
		$('.indexedsearch').focus(function() {
			$(this).removeClass('watermark');
		});
		$('.indexedsearch').blur(function() {
			if (!$(this).val()) {
				$(this).addClass('watermark');
			} else {
                $(this).removeClass('watermark');
            }
		});

		// SEARCH DEFAULT
		// SEARCH MOBILE
		// change target of forms via JavaScript
		var searchTarget = $('.search_target').val();
		$('#indexedsearch, #indexedsearch_mobile').attr('action', searchTarget);

		// RESULTSPAGE: redirect on submit
		if ($('#container_type').val() == 'all') {
			$('#sites_all').attr('checked', 'checked');
		}
		if ($('#container_type').val() == 'this') {
			$('#sites_this').attr('checked', 'checked');
		}
		$('#cseform_content').submit(function(e) {
			e.preventDefault();

			var loc;
			loc = window.location.protocol + "//" + window.location.host;
			if (window.location.pathname.charAt(0) != '/') loc += '/';
			loc += window.location.pathname + "?";
			loc += "cx=007464603711196986792:tm-egyeaeic&ie=UTF-8"; // Our CSE
			loc += "&q=" + encodeURIComponent(document.forms['cseform_content'].elements['q'].value); // User's query input
			if (document.getElementById('sites_this').checked == true) {
				loc += "&sites=this";
			} else {
				loc += "&sites=all";
			}
			window.location = loc;
		});

		/*****************
		 *  MAIL FORM
		 ****************/
		var originalEmail = $('#mailformfrom_email').val();
		$('#mailform').submit(function() {
			var email = $.trim($('#mailformemail').val());
			var regex = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
			$('#mailformfrom_email').val(regex.test(email) ? email : originalEmail);
		});

		/*****************
		 *  SCROLL TO TOP LINKS
		 ****************/
		$('.scroll-to-top').click(function(e) {
			e.preventDefault();
			$("html, body").animate({scrollTop: 0}, 600);
		});

		// Fix for in2flexslider and control layout
		// Hide control navigation if it overlaps with the direction navigation
		var fcnav = $('.flex-control-nav');
		if ((fcnav.length && $(".flex-control-nav > li:last-child").position().top > 0) ||
				(fcnav.length && $(".flex-prev").is(":visible") &&
				$(".flex-control-nav > li:last-child").offset().left + $(".flex-control-nav > li:last-child").outerWidth(true) > $(".flex-prev").offset().left )) {
			$(".flex-control-nav").css("display", "none");
		}

		/*****************
		 *  DOUBLE TAP TO GO
		 ****************/
		$(".js-double-tap").doubleTapToGo();

		/*****************
		 *  Mobile Hauptnavigation
		 ****************/
		function fixMainNavLastItemBorder() {
			$(".js-main-nav-item-1-level").each(function() {
				$(this).find("li:visible:last").children(".js-main-nav-link").css("border-bottom", "none");
				//$(this).siblings("ul.js-main-nav-list").children("li:last-child").addClass("main-nav__item--lastelement");
			});
		}

		$(".js-main-nav-toggle").click(function() {
			var nav = $(".js-main-nav");

			nav.slideToggle();

			if (nav.is(":visible")) {
				nav.find(".main-nav__link--active").each(function() {
					$(this).siblings(".js-main-nav-sub-toggle").hide();
					$(this).siblings(".js-main-nav-list").attr("style", "display: block !important");
				});
			}

			fixMainNavLastItemBorder();
		});

		$(".js-main-nav-sub-toggle").click(function() {
			var link = $(this).siblings(".js-main-nav-link");
			var list = $(this).siblings(".js-main-nav-list");

			if (list.is(":visible")) {
				$(this).removeClass("main-nav__toggle--minus");

				if ($(this).parent().next('li').length === 0) {
					$(this).parent().removeClass("main-nav__item--lastelement");
				}

				$(this).closest("ul").parent().addClass("main-nav__item--lastelement");

			} else {
				$(this).addClass("main-nav__toggle--minus");
				$(this).closest('.main-nav__item--lastelement').removeClass('main-nav__item--lastelement');

				if ($(this).hasClass("main-nav__toggle--1-level")) {
					$(this).parent().addClass("main-nav__item--lastelement");
				}

				if ($(this).parent().next('li').length === 0) {
					var $thisLastChild = $(this).siblings("ul.js-main-nav-list").children("li:last-child");
					var $thisLastChildSubMenu = $thisLastChild.children("ul.js-main-nav-list");

					if ($thisLastChildSubMenu.css("display") === 'block') {
						$(this).parent().removeClass("main-nav__item--lastelement");
					} else {
						$(this).parent().addClass("main-nav__item--lastelement");
					}

				}

			}

			list.slideToggle();

			//fixMainNavLastItemBorder(link);
		});

		/*****************
		 *  Mobile Verzeichnisnavigation
		 ****************/
		$(".js-directory-nav-toggle").click(function() {
			var submenu = $(this).siblings(".js-directory-nav-submenu"),
					item = $(this).parent(".js-directory-nav-item");

			if ($(submenu).is(":visible")) {
				//$(submenu).css("display", "");
				$(item).removeClass("directory-nav__item--is-active");
			} else {
				//$(submenu).show();
				$(item).addClass("directory-nav__item--is-active");
			}

			submenu.slideToggle();

		});

		/*****************
		 *  RoyalSlider
		 ****************/
		var slider = $('#fullWidth');

		if (slider.length > 0) {
			// Slider für die Startseite
			slider.royalSlider({
				arrowsNavAutoHide: false,
				transitionType: 'fade',
				loop: true,
				keyboardNavEnabled: true,
				slidesSpacing: 0,
				navigateByClick: false
			});

			slider.data('royalSlider').ev.on('rsBeforeAnimStart', function() {
				changeRoyalSlidesToBackgroundImages();
			});

			$('.pid111 .rsArrow').wrapAll('<div class="rsArrows-outer" />').wrapAll('<div class="rsArrows-inner" />');
			$('.rsBullets').wrapAll('<div class="rsBullets-outer" />').wrapAll('<div class="rsBullets-inner" />');

			changeRoyalSlidesToBackgroundImages();
		}

		/*****************
		 *  Social-Share-Privacy
		 ****************/
		if ($('#socialshareprivacy').length > 0) {
			$('#socialshareprivacy').socialSharePrivacy({
				services: {
					facebook: {
						'perma_option': 'off'
					},
					twitter: {
						'perma_option': 'off'
					},
					gplus: {
						'perma_option': 'off'
					}
				},
				'cookie_domain': 'tum.de'
			});
		}

		/*****************
		 *  Suchleiste
		 ****************/
		function toggleSearchBar() {
			$(".js-service-bar").slideToggle();
			$(".js-search-bar").slideToggle();
		}

		$(".js-cse-form-button-close").click(function() {
			toggleSearchBar();
		});
		$(".js-cse-open").click(function(e) {
			e.preventDefault();
			toggleSearchBar();
			//$(".js-cse-form-text").val("").focus();
		});

		/*****************
		 *  Accordion
		 ****************/

		$(".js-accordion__headline").siblings().hide();
		var collapsed = 'accordion__headline--collapsed';
		var expanded = 'accordion__headline--expanded';

		$.each($(".js-accordion__headline"), function() {
			if ($(this).siblings().length !== 0) {
				$(this).addClass(collapsed);
			}
		});


		function toggleAccordion($element) {
			var $elementContent = $element.siblings();

			if ($element.hasClass(collapsed)) {
				$element.removeClass(collapsed).addClass(expanded);
			} else if ($element.hasClass(expanded)) {
				$element.removeClass(expanded).addClass(collapsed);
			}

			$elementContent.slideToggle();
		}

		$(".js-accordion__headline").click(function() {
			toggleAccordion($(this));
		});

		/*****************
		 *  Suche
		 ****************/
		if ($('input.js-googlecustomsearch').val()) {
			$('input.js-googlecustomsearch').removeClass('watermark');
		} else {
			$('input.js-googlecustomsearch').addClass('watermark');
		}

		$('.js-cse-open').removeClass('cse-open--no-js');
		$('.cseform_content').removeClass('cseform_content--no-js');

		$("table").wrap('<div class="table-responsive"></div>');
	});
}(jQuery));
