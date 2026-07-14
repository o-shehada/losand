// The Wiki app renders as an SPA and never sets `dir`/`lang` on <html>, so
// its layout (sidebar, table of contents, list markers, breadcrumbs) stays
// mirrored for LTR even though our manual is Arabic. Force RTL for the
// wiki routes this app owns.
(function () {
	if (window.location.pathname.indexOf("/wiki") === 0) {
		document.documentElement.setAttribute("dir", "rtl");
		document.documentElement.setAttribute("lang", "ar");
	}
})();
