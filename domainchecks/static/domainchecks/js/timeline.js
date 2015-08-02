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

    function dateString(date) {
        return date.toISOString()
            .replace('T', ' ')
            .replace(/\.\d+Z$/, ' ');
    }

    $('.charts[data-url]').each(function (row) {
        var $row = $(this),
            url = $row.data('url'),
            responseTime = $row.find('.response-time'),
            timeFrame = $row.find(':input[name="timeframe"]');
        timeFrame.on('change', function (e) {
            var choice = $(this).val(),
                now = new Date(),
                start = new Date(),
                offset = parseInt(choice, 10),
                params = {
                    end: dateString(now),
                };
            start.setHours(now.getHours() - offset);
            params.start = dateString(start);
            $.getJSON(url, params).done(function (data) {
                renderResponseTimes(responseTime, data.results);
            });
        });
        timeFrame.change();
    });

})(jQuery);
