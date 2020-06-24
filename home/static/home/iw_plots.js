// TODO: This objectively horrible, hacky, spaghetti code that must be refactored
// Function to plot daily and cumulative user growths
google.charts.load('current', {'packages':['bar', 'line']});
google.charts.setOnLoadCallback(plot);
function plot() {

    // --------------------------------- 1. Bar Plot - Recorded walks count ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Recorded Walks');
    data.addRows(daily_recorded_walk_count)
    var options = {
        height: 400,
        legend: { position: 'none' },
        bar: { groupWidth: '95%' },
        vAxis: {
            title: "Recorded Walks",
            viewWindow: { min: 0 }
        },
        colors: ["#E59866"]
      };
    var chart = new google.charts.Bar(document.getElementById('daily_rw_count'));
    chart.draw(data, google.charts.Bar.convertOptions(options));

    // --------------------------------- 2. Line Plot - Recorded walks count ---------------------------------
    console.log(cumu_recorded_walk_count)
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Recorded Walks');
    data.addRows(cumu_recorded_walk_count)
      var options = {
        legend: { position: 'none' },
        height: 400,
        vAxis: {
            title: "Recorded Walks",
            viewWindow: { min: 0 }
        },
        colors: ["#E59866"]
      };
    var chart = new google.charts.Line(document.getElementById('total_rw_count'));
    chart.draw(data, google.charts.Line.convertOptions(options));


    // --------------------------------- 3. Bar Plot - Recorded walks Steps ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Steps');
    data.addRows(daily_recorded_walk_steps)
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
    var chart = new google.charts.Bar(document.getElementById('daily_rw_steps'));
    chart.draw(data, google.charts.Bar.convertOptions(options));

    // --------------------------------- 4. Line Plot - Recorded walks Steps ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Steps');
    data.addRows(cumu_recorded_walk_steps)
      var options = {
        legend: { position: 'none' },
        height: 400,
        vAxis: {
            title: "Steps",
            viewWindow: { min: 0 }
        },
        colors: ["#2ECC71"]
      };
    var chart = new google.charts.Line(document.getElementById('total_rw_steps'));
    chart.draw(data, google.charts.Line.convertOptions(options));


    // --------------------------------- 5. Bar Plot - Recorded walks Miles ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Miles');
    data.addRows(daily_recorded_walk_miles)
    var options = {
        height: 400,
        legend: { position: 'none' },
        bar: { groupWidth: '95%' },
        vAxis: {
            title: "Steps",
            viewWindow: { min: 0 }
        },
        colors: ["#1ABC9C"]
      };
    var chart = new google.charts.Bar(document.getElementById('daily_rw_miles'));
    chart.draw(data, google.charts.Bar.convertOptions(options));

    // --------------------------------- 6. Line Plot - Recorded walks Miles ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Miles');
    data.addRows(cumu_recorded_walk_miles)
      var options = {
        legend: { position: 'none' },
        height: 400,
        vAxis: {
            title: "Steps",
            viewWindow: { min: 0 }
        },
        colors: ["#1ABC9C"]
      };
    var chart = new google.charts.Line(document.getElementById('total_rw_miles'));
    chart.draw(data, google.charts.Line.convertOptions(options));


    // --------------------------------- 7. Bar Plot - Recorded walks Time ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Minutes');
    data.addRows(daily_recorded_walk_time)
    var options = {
        height: 400,
        legend: { position: 'none' },
        bar: { groupWidth: '95%' },
        vAxis: {
            title: "Minutes",
            viewWindow: { min: 0 }
        },
        colors: ["#5DADE2"]
      };
    var chart = new google.charts.Bar(document.getElementById('daily_rw_time'));
    chart.draw(data, google.charts.Bar.convertOptions(options));

    // --------------------------------- 8. Line Plot - Recorded walks Steps ---------------------------------
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Minutes');
    data.addRows(cumu_recorded_walk_time)
      var options = {
        legend: { position: 'none' },
        height: 400,
        vAxis: {
            title: "Minutes",
            viewWindow: { min: 0 }
        },
        colors: ["#5DADE2"]
      };
    var chart = new google.charts.Line(document.getElementById('total_rw_time'));
    chart.draw(data, google.charts.Line.convertOptions(options));

};






