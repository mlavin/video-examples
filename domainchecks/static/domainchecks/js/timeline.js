(function ($) {
    'use strict';

    var chartOptions = JSON.parse($('#chartOptions').text());

    function renderResponseTimes(elem, data) {
        var series = data.map(function (item) {
                return [
                    Date.parse(item['checked_on']),
                    item['response_time'] * 1000
                ];
            }),
            errors = data.map(function (item) {
                return [
                    Date.parse(item['checked_on']),
                    item['status_code'] > 299 ? item['response_time'] * 1000 || 0 : null
                ];
            });
        $.plot(elem, [
                {data: series},
                {data: errors, points: {show: true}, color: '#c30'}
            ], chartOptions);
    }

    $('.charts[data-url]').each(function (row) {
        var $row = $(this),
            url = $row.data('url'),
            responseTime = $row.find('.response-time');
        $.getJSON(url).done(function (data) {
            renderResponseTimes(responseTime, data.results);
        });
    });

})(jQuery);
