(function($) {
    'use strict';
    $(function() {
        var body = $('body');
        var contentWrapper = $('.content-wrapper');
        var scroller = $('.container-scroller');
        var footer = $('.footer');
        var sidebar = $('.sidebar');

        //Add active class to nav-link based on url dynamically
        //Active class can be hard coded directly in html file also as required

        function addActiveClass(element) {
            var current = location.pathname.split("/").slice(-1)[0].replace(/^\/|\/$/g, '');
            if (current === "") {
                //for root url
                if (element.attr('href').indexOf("index.html") !== -1) {
                    element.parents('.nav-item').last().addClass('active');
                    if (element.parents('.sub-menu').length) {
                        element.closest('.collapse').addClass('show');
                        element.addClass('active');
                    }
                }
            } else {
                //for other url
                if (element.attr('href').indexOf(current) !== -1) {
                    element.parents('.nav-item').last().addClass('active');
                    if (element.parents('.sub-menu').length) {
                        element.closest('.collapse').addClass('show');
                        element.addClass('active');
                    }
                    if (element.parents('.submenu-item').length) {
                        element.addClass('active');
                    }
                }
            }
        }

        $('.nav li a', sidebar).each(function() {
            var $this = $(this);
            addActiveClass($this);
        });

        //Close other submenu in sidebar on opening any

        sidebar.on('show.bs.collapse', '.collapse', function() {
            sidebar.find('.collapse.show').collapse('hide');
        });


        //Change sidebar

        $('[data-toggle="minimize"]').on("click", function() {
            body.toggleClass('sidebar-icon-only');
        });

        //checkbox and radios
        $(".form-check label,.form-radio label").append('<i class="input-helper"></i>');

        // Remove pro banner on close
        document.addEventListener('DOMContentLoaded', function() {
            if ($.cookie('majestic-free-banner') != "true") {
                var proBanner = document.querySelector('#proBanner');
                if (proBanner) {
                    proBanner.classList.add('d-flex');
                } else {
                    console.error('#proBanner element not found');
                }
            } else {
                var proBanner = document.querySelector('#proBanner');
                if (proBanner) {
                    proBanner.classList.add('d-none');
                } else {
                    console.error('#proBanner element not found');
                }
            }

            var bannerCloseButton = document.querySelector('#bannerClose');
            if (bannerCloseButton) {
                bannerCloseButton.addEventListener('click', bannerCloseHandler);
            } else {
                console.error('#bannerClose element not found');
            }
        });

        var bannerCloseHandler = function() {
            var proBanner = document.querySelector('#proBanner');
            if (proBanner) {
                proBanner.classList.add('d-none');
                proBanner.classList.remove('d-flex');
                var date = new Date();
                date.setTime(date.getTime() + 24 * 60 * 60 * 1000);
                $.cookie('majestic-free-banner', "true", { expires: date });
            } else {
                console.error('#proBanner element not found');
            }
        };
    });
})(jQuery);
