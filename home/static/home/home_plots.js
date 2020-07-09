// TODO: This objectively horrible, hacky, spaghetti code that must be refactored
// Function to plot daily and cumulative user growths
google.charts.load('current', {'packages':['bar', 'line', 'corechart']});
google.charts.setOnLoadCallback(plot);
function plot() {

    // --------------------------------- 1. Bar plot - All Signups ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Signups');
    data.addRows(daily_user_signups)
    var options = {
        height: 400,
        legend: { position: 'none' },
        bar: { groupWidth: '95%' },
        vAxis: {
            title: "Daily signups",
            viewWindow: { min: 0 }
        },
        colors: ["#E59866"]
      };
    var chart = new google.charts.Bar(document.getElementById('daily_signups'));
    chart.draw(data, google.charts.Bar.convertOptions(options));

    // --------------------------------- 2. Line Plot - All Signups ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Signups');
    data.addRows(cumu_user_signups)
      var options = {
        legend: { position: 'none' },
        height: 400,
        vAxis: {
            title: "Total signups",
            viewWindow: { min: 0 }
        },
        colors: ["#E59866"]
      };
    var chart = new google.charts.Line(document.getElementById('total_signups'));
    chart.draw(data, google.charts.Line.convertOptions(options));

    // --------------------------------- 3. Bar Plot - All Steps ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Steps');
    data.addRows(daily_step_count)
    var options = {
        height: 400,
        legend: { position: 'none' },
        bar: { groupWidth: '95%' },
        vAxis: {
            title: "Steps",
            viewWindow: { min: 0 }
        },
        colors: ["#2ECC71"]
      };
    var chart = new google.charts.Bar(document.getElementById('daily_steps'));
    chart.draw(data, google.charts.Bar.convertOptions(options));

    // --------------------------------- 4. Line Plot - All Steps ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Steps');
    data.addRows(cumu_step_count)
      var options = {
        legend: { position: 'none' },
        height: 400,
        vAxis: {
            title: "Steps",
            viewWindow: { min: 0 }
        },
        colors: ["#2ECC71"]
      };
    var chart = new google.charts.Line(document.getElementById('total_steps'));
    chart.draw(data, google.charts.Line.convertOptions(options));

    // --------------------------------- 5. Bar Plot - All Miles ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Miles');
    data.addRows(daily_mile_count)
    var options = {
        height: 400,
        legend: { position: 'none' },
        bar: { groupWidth: '95%' },
        vAxis: {
            title: "Miles",
            viewWindow: { min: 0 }
        },
        colors: ["#1ABC9C"]
      };
    var chart = new google.charts.Bar(document.getElementById('daily_miles'));
    chart.draw(data, google.charts.Bar.convertOptions(options));

    // --------------------------------- 6. Line Plot - All Miles ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Miles');
    data.addRows(cumu_mile_count)
      var options = {
        legend: { position: 'none' },
        height: 400,
        vAxis: {
            title: "Miles",
            viewWindow: { min: 0 }
        },
        colors: ["#1ABC9C"]
      };
    var chart = new google.charts.Line(document.getElementById('total_miles'));
    chart.draw(data, google.charts.Line.convertOptions(options));

    // --------------------------------- 7. Age histogram ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('number', 'Age');
    data.addRows(user_age_dist)
    var options = {
        legend: { position: 'none' },
        height: 600,
        colors: ["#AF7AC5"],
        histogram: { bucketSize: 5 },
        vAxis: {
            title: "Number of users",
            viewWindow: { min: 0 }
        },
        hAxis: {
            title: "Age",
        },
    };

    var chart = new google.visualization.Histogram(document.getElementById('user_age_dist'));
    chart.draw(data, options);

};