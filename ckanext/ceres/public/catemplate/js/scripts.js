/*
State of California
Version 2013.xx.xx
*/

var serpLocation = "/serp.html"; // Location of your search engine results page (SERP)

// addLoadEvent by Simon Willison
// Adds a handler to an event without over-riding other handlers
function addLoadEvent(func) {
	var oldonload = window.onload;
	if (typeof window.onload != 'function') {
		window.onload = func;
	} else {
		window.onload = function() {
			if (oldonload) {
				oldonload();
			}
			func();
		}
	}
}

/* http://www.dustindiaz.com/getelementsbyclass/ */
function getElementsByClass(searchClass,node,tag) {
	var classElements = new Array();
	if ( node == null )
		node = document;
	if ( tag == null )
		tag = '*';
	var els = node.getElementsByTagName(tag);
	var elsLen = els.length;
	var pattern = new RegExp("(^|\\s)"+searchClass+"(\\s|$)");
	for (i = 0, j = 0; i < elsLen; i++) {
		if ( pattern.test(els[i].className) ) {
			classElements[j] = els[i];
			j++;
		}
	}
	return classElements;
}

var counterC = 0;
var navRoot;

initNavigation = function() {

	var useNavFolderMatch = true; // Use new folder matching method to highlight the current navigation tab?
	var disableNavFade = false; // Disable navigation fade effects?
	var ignoreNavMouseover = false;
	setTimeout(function(){ignoreNavMouseover = false;},500); // Prevent nav from opening on page load if mouse is already positioned over nav
	navRoot = document.getElementById("nav_list");

	// Touchscreens - If user taps outside of nav, close nav panels
	if (Modernizr.touch){
		document.body.addEventListener('touchstart', function(ev) {
			navRoot.className = "";
			closeAllPanels();
		}, false);
	}
	
	if (document.querySelectorAll) { // Does the browser support the querySelectorAll method?

		var arrCurrentURL=location.href.split("/");

		arrayNavLI = document.querySelectorAll("#nav_list > li");

		var reMainNav = "";
		if (typeof defaultMainList!="undefined")
			reMainNav = new RegExp("^" + defaultMainList + "$", "i"); // Regex for finding the index of the default main list item
		

		for (var i=0; i<arrayNavLI.length; i++) { // Loop over main list items
			var node = arrayNavLI[i];

			////// Highlight the default main nav item //////
			if (reMainNav) {
				if (node.firstChild.innerHTML.match(reMainNav)) { // Found default main nav item
					node.className += " highlighted_nav_item"; // add class to this li
				}
			} else if (useNavFolderMatch && node.childNodes[0] && node.childNodes[0].href) {
				arrNavLink = node.childNodes[0].href.split("/");
				if ((arrNavLink.length > 4) && (arrCurrentURL[3] == arrNavLink[3])) { // folder of current URL matches this nav link
					node.className += " highlighted_nav_item"; // add class to this li
				}
			}


			if (Modernizr.touch) {
				if (node.querySelector(".nav_panel")) {
					node.querySelector(".nav_level1_link").level1Link = node.querySelector(".nav_level1_link").href;
					node.querySelector(".nav_level1_link").removeAttribute("href");

					node.addEventListener('touchstart', function(ev) {
						// keeps tabpanel from closing when clicking inside of it
						ev.stopPropagation();
					},false);
				}


				node.querySelector(".nav_level1_link").addEventListener('click', function(ev) {
					ev.stopPropagation();
					counterC++;

					var navigPanel = this.parentNode.querySelector(".nav_panel");

					if ((navigPanel && navigPanel.className.match(/mo_display/)) || (this.offsetWidth == navRoot.offsetWidth)) {// is panel already open, or mobile layout

						window.location = this.level1Link;
	
					} else {

						closeAllPanels(); // hide all other panels
						
						// show panel
						navRoot.className = "unhighlight_nav_item";
		
						if (!ignoreNavMouseover && navigPanel) { // does this nav item have a navpanel?
							if (!disableNavFade) {
								if (navigPanel.outTimerID) // are we fading after a mouseout?
									clearTimeout(navigPanel.outTimerID); // cancel it
								
								navigPanel.className += " mo_display"; // display:block
								navigPanel.overOTimerID = setTimeout(function(){navigPanel.className += " mo_opacity";},10); // set opacity:1
								
							} else {
								navigPanel.style.display = "block";
							}
							// set position of down arrow
							var arrayDownArrow = getElementsByClass("nav_d_arrow_container",this.parentNode);
							if (arrayDownArrow.length == 1) {
								arrayDownArrow[0].style.left = this.offsetLeft + this.offsetWidth / 2 + "px";
							}
						}
	
					}
				},false);

			} else {

				////// Apply onmouseover and onmouseout event handlers to each main list item //////
				node.onmouseover = function(e) {
					if (!e) var e = window.event;
	
					var reltg = (e.relatedTarget) ? e.relatedTarget : e.fromElement;
					while (reltg && reltg != this && reltg.nodeName != 'BODY')
						reltg = reltg.parentNode;
					if (reltg == this) return; // mouse was already inside li
					
					navRoot.className = "unhighlight_nav_item";
	
					var arrayNavPanel = getElementsByClass("nav_panel", this);
					if (!ignoreNavMouseover && (arrayNavPanel.length == 1) && this.offsetWidth < navRoot.offsetWidth) { // does this nav item have a navpanel, and desktop layout?
						if (!disableNavFade) {
							if (arrayNavPanel[0].outTimerID) // are we fading after a mouseout?
								clearTimeout(arrayNavPanel[0].outTimerID); // cancel it
	
							arrayNavPanel[0].overDTimerID = setTimeout(function(){arrayNavPanel[0].className += " mo_display";},100);
							arrayNavPanel[0].overOTimerID = setTimeout(function(){arrayNavPanel[0].className += " mo_opacity";},120);
							
						} else {
							arrayNavPanel[0].style.display = "block";
						}
						// set position of down arrow
						var arrayDownArrow = getElementsByClass("nav_d_arrow_container",this);
						if (arrayDownArrow.length == 1) {
							arrayDownArrow[0].style.left = this.offsetLeft + this.offsetWidth / 2 + "px";
						}
					}
				}
				node.onmouseout = function(e) {
	
					if (!e) var e = window.event;
	
					// We're not sure if the mouse left the layer or entered a link within the layer.
					// Therefore we're going to check the relatedTarget/toElement of the event, ie. the element the mouse moved to.
					var reltg = (e.relatedTarget) ? e.relatedTarget : e.toElement;
	
					//We read out this element, and then we're going to move upwards through the DOM tree
					//until we either encounter the target of the event (ie. the LI), or the body element.
					//If we encounter the target the mouse moves towards a child element of the layer,
					//so the mouse has not actually left the layer. We stop the function.
					while (reltg && reltg != this && reltg.nodeName != 'BODY')
						reltg = reltg.parentNode;
					if (reltg == this) return; // mouse is still inside li
	
					navRoot.className = "";
	
					var arrayNavPanel = getElementsByClass("nav_panel", this);
					if (arrayNavPanel.length == 1) {
						if (!disableNavFade) {
							if (arrayNavPanel[0].overDTimerID) // pausing for a mouseover? cancel it.
								clearTimeout(arrayNavPanel[0].overDTimerID);
							if (arrayNavPanel[0].overOTimerID)
								clearTimeout(arrayNavPanel[0].overOTimerID);
	
							arrayNavPanel[0].outTimerID = setTimeout(function(){arrayNavPanel[0].className = arrayNavPanel[0].className.replace(/mo_display/g, "");},300);
							arrayNavPanel[0].className = arrayNavPanel[0].className.replace(/mo_opacity/g, "");
													
						} else {
							arrayNavPanel[0].style.display = "none";
						}
					}
				}
			}
		}

		// Create styles for phone nav
		var dynStylesheet = document.createElement('style');
		dynStylesheet.type="text/css";
		dynStylesheet.media="";
		dynSSRules = "#navigation.phone_show_nav {	height:" + (arrayNavLI[0].offsetHeight + 2) * (arrayNavLI.length-1) + "px;}";

		document.getElementsByTagName('head')[0].appendChild(dynStylesheet);
		if (dynStylesheet.styleSheet) { // IE
			dynStylesheet.styleSheet.cssText = dynSSRules;
		} else { // proper browsers
			dynSSTextNode = document.createTextNode(dynSSRules);
			dynStylesheet.appendChild(dynSSTextNode);
		}
	}
}

function closeAllPanels() {
	var arrayPanel = document.getElementById("nav_list").querySelectorAll(".mo_display, .mo_opacity");
	for (var counterA = 0; counterA < arrayPanel.length; counterA++) {
		arrayPanel[counterA].className = arrayPanel[counterA].className.replace(/mo_opacity/g, "");
		arrayPanel[counterA].outTimerID = setTimeout(removeDisplay,200,arrayPanel[counterA]);
	}
}

function removeDisplay(obj) {
	obj.className = obj.className.replace(/mo_display/g, "");
}

function toggle_menu() {
	// we are not using the search container - JM
	//var searchContainer = document.getElementById("head_search");
	var navContainer = document.getElementById("navigation");
	var menuButton = getElementsByClass("p_h_menu");
	var searchButton = getElementsByClass("p_h_search");

	if (navContainer.className.indexOf("phone_show_nav") < 0) { // is nav hidden?
		// apply class "phone_show_nav" to nav
		navContainer.className += " phone_show_nav";
		//searchContainer.className = searchContainer.className.replace("phone_show_search","");
		if (menuButton.length == 1) menuButton[0].style.backgroundPosition = "0 -50px";
		//if (searchButton.length == 1) searchButton[0].style.backgroundPosition = "-150px 0";
	} else {
		// remove class
		navContainer.className = navContainer.className.replace("phone_show_nav","");
		if (menuButton.length == 1) menuButton[0].style.backgroundPosition = "0 0";
	}
}

function toggle_search() {
	var searchContainer = document.getElementById("head_search");
	var navContainer = document.getElementById("navigation");
	var menuButton = getElementsByClass("p_h_menu");
	var searchButton = getElementsByClass("p_h_search");

	if (searchContainer.className.indexOf("phone_show_search") < 0) { // is search form hidden?
		// apply class "phone_show_search" to nav
		searchContainer.className += " phone_show_search";
		document.getElementById("search_local_textfield").focus();
		navContainer.className = navContainer.className.replace("phone_show_nav","");
		if (searchButton.length == 1) searchButton[0].style.backgroundPosition = "-150px -50px";
		if (menuButton.length == 1) menuButton[0].style.backgroundPosition = "0 0";
	} else {
		// remove class
		searchContainer.className = searchContainer.className.replace("phone_show_search","");
		if (searchButton.length == 1) searchButton[0].style.backgroundPosition = "-150px 0";
	}
}

var prepareSearchForm = {
	init: function() {
		elemSearchForm = document.getElementById("local_form");
		if (elemSearchForm) {
			elemSearchForm.action = serpLocation;
			elemSearchForm.cof.value = "FORID:10";
		}

		if ((navigator.appVersion.indexOf("MSIE 7.") != -1)||(navigator.appVersion.indexOf("MSIE 8.") != -1)) { /* Fix Google Autocomplete and IE7/8 issue where default text doesn't clear */
			document.getElementById("search_local_textfield").value="";
		}

	}
}

// this is not app friendly at all
// just using jquery
//function initPage() {
//  initNavigation();
//  prepareSearchForm.init();
//}
//addLoadEvent(initPage);
$(window).on('load', function(){
    initNavigation();
    //prepareSearchForm.init();
});
