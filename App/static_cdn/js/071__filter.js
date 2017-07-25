function removeParam(key, sourceURL) {
	'use strict';

	var rtn = sourceURL.split('?')[0];
	var param;
	var paramsArr = [];
	var queryString = (sourceURL.indexOf('?') !== -1) ? sourceURL.split('?')[1] : '';
	if ('' !== queryString) {
		paramsArr = queryString.split('&');
		for (var i = paramsArr.length - 1; i >= 0; i -= 1) {
			param = paramsArr[i].split('=')[0];
			if (param === key) {
				paramsArr.splice(i, 1);
			}
		}
		rtn = rtn + '?' + paramsArr.join('&');
	}
	return rtn;
}

if ($('#js-studienberater-filter').length) {
	var readFilterFromUrl = true;
	var studyCourseFilter;

	studyCourseFilter = {
		enableLoading: function() {
			'use strict';

			$('#studienberater').addClass('loading');
		},
		disbaleLoading: function() {
			'use strict';

			$('#studienberater').removeClass('loading');
		},
		filterChanged: function(paginationPage) {
			'use strict';

			var studienBeraterForm = $('#studienberater_filter_form');
			var url = removeParam('cHash', studienBeraterForm.attr('action'));
			if (paginationPage) {
				url += '&tx_tumstudycourses_pi2%5B%40widget_0%5D%5BcurrentPage%5D=' + paginationPage;
			}
			$.ajax({
				type: 'POST',
				url: url,
				data: studienBeraterForm.serialize(),
				beforeSend: function() {
					studyCourseFilter.enableLoading();
				},
				success: function(data) {
					$('#studienberater').html($(data).find('#studienberater').html());
					studyCourseFilter.saveSelectedOptionsToUrl(paginationPage);
				},
				error: function() {
					var lang = $('html').attr('lang');
					if ('de' === lang) {
						alert('Ihre abgespeicherte Suche kann nicht mehr ausgeführt werden. Bitte wählen sie ihr Filter erneut');
					} else {
						alert('This results page is not available any more. Please search again');
					}
				},
				complete: function() {
					studyCourseFilter.disbaleLoading();
					FE.init();
					FE.openPreviouslyOpenedFilterOptions();
				},
				cache: false
			});
		},
		filterOptionAbbreviations: {
			degreeType: 1,
			formOfStudy: 2,
			courseLanguages: 3,
			registrationType: 4,
			studyAreas: 5,
			studyEntries: 6,
			topLocations: 7
		},
		reverseFilterOptionAbbreviations: {
			1: 'degreeType',
			2: 'formOfStudy',
			3: 'courseLanguages',
			4: 'registrationType',
			5: 'studyAreas',
			6: 'studyEntries',
			7: 'topLocations'
		},
		saveSelectedOptionsToUrl: function(paginationPage) {
			'use strict';

			var selectionValues = [];
			var selectionString = '';
			var selectedOptions = $('#studienberater_filter_form').find('input.checkbox-option:checked');
			$(selectedOptions).each(function() {
				var filterGroupAbbreviation = studyCourseFilter.filterOptionAbbreviations[$(this).data('filtergroup')];
				if (undefined === selectionValues[filterGroupAbbreviation]) {
					selectionValues[filterGroupAbbreviation] = [];
				}
				selectionValues[filterGroupAbbreviation].push($(this).attr('value'));
			});
			$(selectionValues).each(function(key, values) {
				if (key > 0 && undefined !== values && values.length > 0) {
					selectionString += key + 'x';
					$(values).each(function(key, value) {
						selectionString += value + 'e';
					});
					selectionString = selectionString.replace(/[e]$/, '');
					selectionString += 'k';
				}
			});
			selectionString = selectionString.replace(/[k]$/, '');
			if (paginationPage) {
				selectionString += 'p' + paginationPage;
			}
			window.location = location.protocol +
					'//' +
					location.host +
					location.pathname +
					(location.search ? location.search : '') +
					'#' +
					selectionString;
		},

		urlToFilterSelection: function() {
			'use strict';

			var filterHash = window.location.hash.split('#');
			if (1 in filterHash) {
				filterHash = filterHash[1];
				var paginationPage;

				if (filterHash.indexOf('p') !== -1) {
					paginationPage = filterHash.split('p')[1];
					filterHash = filterHash.split('p')[0];
				}
				var filterParts = filterHash.split('k');
				$(filterParts).each(function(key, values) {
					var selections = values.split('x');
					var filterGroup = studyCourseFilter.reverseFilterOptionAbbreviations[selections[0]];
					if (2 <= $(selections).length) {
						var selectedOptions = selections[1].split('e');
						$(selectedOptions).each(function(key, value) {
							$('#' + filterGroup + '_' + value).prop('checked', true);
						});
					}
				});
				studyCourseFilter.filterChanged(paginationPage);
			}
		}
	};

	var FE;
	FE = {
		init: function() {
			'use strict';

			this.initiateQuickSelectHandling();
			this.activateChosen();
			this.checkboxHandling();
			this.paginationHandling();
			if (readFilterFromUrl) {
				readFilterFromUrl = false;
				studyCourseFilter.urlToFilterSelection();
			}
		},
		initiateQuickSelectHandling: function() {
			'use strict';

			$('#js-studienberater-filter').on('submit', function(event) {
				event.preventDefault();
				var action = $(this).attr('action');
				var studyCourseUid = $(this).find('option:selected').attr('value');
				window.location.href = action + studyCourseUid;
			});
		},
		activateChosen: function() {
			'use strict';

			// Chosen für Select der Studiengänge
			$('#js-studienberater-filter').children('select').chosen({
				no_results_text: 'Keine Treffer',
				search_contains: true
			}).on('change', function() {
				$(this).parent('form').submit();
			});
		},
		checkboxHandling: function() {
			'use strict';

			// Optionen ein-/ausblenden
			$('.studienberater_optionsheader_show').on('click', function() {
				$(this).toggleClass('hide');
				$(this).siblings().toggleClass('hide');
				$(this).parent().siblings('fieldset').toggleClass('hide');
			});
			$('.studienberater_optionsheader_hide').on('click', function() {
				$.each($('.checkbox-option'), function() {
					$(this).prop('checked', false);
				});
				$.each($('.checkbox-all'), function() {
					$(this).prop('checked', false);
				});
				studyCourseFilter.filterChanged();
			});
			// Accordionfunktion für die einzelnen Optionenbereiche
			$('.studienberater_optiontitle').on('click', function() {
				$(this).toggleClass('opened').siblings('.studienberater_accordion').slideToggle('fast');
				FE.setopenedfieldsets();
			});
			// "Alle" Checkbox unchecken wenn eine andere geklickt wird
			// und wieder checken, wenn keine mehr markiert ist
			$('.checkbox-option').change(function() {
				if ($(this).prop('checked')) {
					$(this).siblings('.checkbox-all').prop('checked', false).prop('disabled', false);
				} else {
					if (0 === $(this).siblings('.checkbox-option:checkbox:checked').length) {
						$(this).siblings('.checkbox-all').prop('checked', true).prop('disabled', true);
					}
				}
				studyCourseFilter.filterChanged();
			});

			// alle Checkboxen unchecken, wenn "Alle" geklickt wird
			$('.checkbox-all').change(function() {
				if ($(this).prop('checked')) {
					$(this).siblings('.checkbox-option:checkbox:checked').each(function() {
						$(this).prop('checked', false);
					});
					$(this).prop('disabled', true);
				}
				studyCourseFilter.filterChanged();
			});
		},
		paginationHandling: function() {
			'use strict';

			$('.js-get-by-ajax').on('click', function(e) {
				e.preventDefault();
				var link = $(this);
				var destination = removeParam('cHash', link.attr('href'));
				var targetPage = 1;
				destination.split('&').forEach(function(value) {
					if (value.match(/tx_tumstudycourses_pi2%5B%40widget_0%5D%5BcurrentPage%5D=/)) {
						targetPage = value.replace('tx_tumstudycourses_pi2%5B%40widget_0%5D%5BcurrentPage%5D=', '');
					}
				});
				$.ajax({
					type: 'GET',
					url: destination,
					beforeSend: function() {
						studyCourseFilter.enableLoading();
						studyCourseFilter.saveSelectedOptionsToUrl(targetPage);
					},
					success: function(data) {
						$('#studienberater').html($(data).find('#studienberater'));
						window.scrollTo(0, 0);
					},
					error: function() {
						alert('fail');
					},
					complete: function() {
						studyCourseFilter.disbaleLoading();
						FE.init();
						FE.openPreviouslyOpenedFilterOptions();
					},
					cache: false

				});
			});
		},
		openPreviouslyOpenedFilterOptions: function() {
			'use strict';

			var filtered = false;
			var studienberater = $('#studienberater').parent('div');
			$('#studienberater_filter_form').find('input[type=checkbox]:checked:enabled').each(function() {
				$(this).siblings('.checkbox-all').prop('checked', false).prop('disabled', false);
				var parent = $(this).parents('.studienberater_optionsection').children('.studienberater_optiontitle');
				if (!parent.hasClass('opened')) {
					parent.addClass('opened');
					parent.siblings('.studienberater_accordion').show();
					filtered = true;
				}
			});
			if (filtered) {
				$('.studienberater_optionsheader_show').click();
			}
			if (studienberater.attr('data-openedfields')) {
				var fieldsetstoopen = studienberater.attr('data-openedfields').split(',');
				$.each(fieldsetstoopen, function(index, value) {
					$('#studienberater_filter_form')
							.children()
							.eq(value)
							.children('legend')
							.addClass('opened')
							.siblings('.studienberater_accordion')
							.show();
				});
			}
		},
		setopenedfieldsets: function() {
			'use strict';

			var studienberater = $('#studienberater').parent('div');
			studienberater.removeAttr('data-openedfields').removeData('openedfields');
			var openedfieldset = '';
			$('.studienberater_optionsection').each(function() {
				if ($(this).children('.studienberater_optiontitle').hasClass('opened')) {
					openedfieldset = openedfieldset + ',' + ($(this).index());
				}
			});
			studienberater.attr('data-openedfields', openedfieldset.substring(1));
		}
	};

	FE.init();
}

if ($('.studienberater_detail').length) {
	$('.js-scroll').on('click', function(e) {
		'use strict';

		e.preventDefault();
		var hash = $(this).attr('href').replace(/^.*?(#|$)/, '#');
		var pattern = /#top/;
		var exists = pattern.test(hash);

		if (exists) {
			$('html, body').animate({
				scrollTop: 0
			}, 1);
		} else {
			$('html, body').animate({
				scrollTop: $(hash).offset().top
			}, 1);
		}
	});
}
