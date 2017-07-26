/* From CSE "Get the code", with MODifications */
function parseQueryFromUrl () {
	var queryParamName = "q";
	var search = window.location.search.substr(1);
	var parts = search.split('&');
	for (var i = 0; i < parts.length; i++) {
		var keyvaluepair = parts[i].split('=');
		if (decodeURIComponent(keyvaluepair[0]) == queryParamName) {
			var query = decodeURIComponent(keyvaluepair[1].replace(/\+/g, ' '));
			return query;
		}
	}
	return '';
}

google.load('search', '1', {'language' : (document.getElementsByTagName("html")[0].getAttribute("lang") == "en") ? "en" : "de"}); // MOD: switch language
google.setOnLoadCallback(function() {
	var customSearchOptions = {};
	var imageSearchOptions = {};
	// MOD: make as_sitesearch if chosen
	if (document.getElementById('sites_this').checked == true) {
        customSearchOptions[google.search.Search.RESTRICT_EXTENDED_ARGS] = {'as_sitesearch' : window.location.host};
	}
	// end
	imageSearchOptions['layout'] = google.search.ImageSearch.LAYOUT_POPUP;
	customSearchOptions['enableImageSearch'] = true;
	customSearchOptions['imageSearchOptions'] = imageSearchOptions;

	var customSearchControl = new google.search.CustomSearchControl('007464603711196986792:tm-egyeaeic', customSearchOptions);
	customSearchControl.setResultSetSize(google.search.Search.FILTERED_CSE_RESULTSET);
	customSearchControl.setLinkTarget(google.search.Search.LINK_TARGET_SELF);

	var options = new google.search.DrawOptions();
	options.enableSearchResultsOnly();
	customSearchControl.draw('cse', options);

	var imagesearch = customSearchControl.getImageSearcher();
	// MOD: make as_sitesearch if chosen
	if (document.getElementById('sites_this').checked == true) {
		imagesearch.setQueryAddition('site:'+window.location.host);
	}
	// end

	var queryFromUrl = parseQueryFromUrl();
	if (queryFromUrl) {
	  customSearchControl.execute(queryFromUrl);
	}

	// MOD: Auto-complete
	if (true) {
		var submitActorHolder = new Object();
		submitActorHolder.execute = document.getElementById('cseform_content').onsubmit;
		var autoCompletionOptions = {
			'maxCompletions' : 11,
			'styleOptions' : {
				'fixedWidth' : 444,
				'xAlign' : 'left'
			}
		};
//		google.search.CustomSearchControl.attachAutoCompletionWithOptions('007464603711196986792:tm-egyeaeic', document.getElementById('q'), submitActorHolder, autoCompletionOptions);
		google.search.CustomSearchControl.attachAutoCompletionWithOptions('007464603711196986792:tm-egyeaeic', document.getElementById('q'), null, autoCompletionOptions);
	}

}, true);

