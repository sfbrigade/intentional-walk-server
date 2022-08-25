/**
 *
 * The following Javascript call is meant to demonstrate passing
 * a Jinja2 context variables to bootstrapUserBar.
 *
 * bootstrapUserBar(
 *     "#my-user-bar-div",
 *     {{ cnt_users }},
 *     {{ cnt_signups }}
 * );
 *
 **/
function bootstrapUserBar(id, title, cnt_users, cnt_signups) {
    // Configurable constants

    // The previous bar color is meant to be the Intentional Walk
    // primary color, at #702B84.
    const PREVIOUS_BAR_COLOR = "rgb(112, 43, 132)";

    // The new user bar color is meant to be a 35% transparent
    // version of PREVIOUS_BAR_COLOR (100 - 35 = 65).
    const NEW_BAR_COLOR = "rgba(112, 43, 132, 0.65)";

    const cnt_delta = cnt_users - cnt_signups;
    const data = [
        {label: "Previous", value: cnt_delta},
        {label: "New", value: cnt_signups}
    ];

    const groups_domain = data.reduce(function(total, e) {
        total.push(e.label);
        return total;
    }, []);

    const domain = [0, cnt_users];

    const margin = {
        left: 60,
        top: 80,
        right: 30,
        bottom: 70
    };

    const width = 400 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    let svg = d3.select(id)
        .append("svg")
        .attr("width", 400)
        .attr("height", 400);

    let chart = svg.append("g")
        .attr(
            "transform",
            "translate(" + margin.left + ", " + margin.top + ")"
        );

    let x = d3.scaleBand()
        .range([ 0, width ])
        .domain(groups_domain)
        .padding(0.3);

    chart.append("g")
        .attr("transform", "translate(0, " + height + ")")
        .call(d3.axisBottom(x));

    const cnt_max = Math.max(cnt_delta, cnt_signups);
    let y = d3.scaleLinear()
        .domain([0, cnt_max])
        .range([height, 0]);

    chart.append("g")
        .call(d3.axisLeft(y));

    let color = d3.scaleOrdinal()
        .domain(groups_domain)
        .range([PREVIOUS_BAR_COLOR, NEW_BAR_COLOR]);

    let i = 0;
    let groups = chart.selectAll()
        .data(data)
        .enter()
        .append("g");

    groups.append("rect")
        .attr("x", function(e) { return x(e.label); })
        .attr("y", function(e) { return y(e.value); })
        .attr("width", x.bandwidth())
        .attr("height", function(e) { return (height - y(e.value)) + "px"; })
        .attr("fill", function(e) { return color(e.label); });

    svg.append("text")
      .attr("class", "graph-title")
      .attr("x", width / 2 + margin.left)
      .attr("y", 40)
      .attr("text-anchor", "middle")
      .text(title);

    svg.append("g")
        .attr("class", "tooltip")
        .append("text")
        .text("Test!")
        .attr("class", "tooltip-text");

    let tooltip = d3.select(id + " .tooltip")
        .style("opacity", 0);

    chart.append("text")
      .attr("class", "label")
      .attr("x", x(data[0].label) + 47)
      .attr("y", y(data[0].value) - 10)
      .attr("text-anchor", "middle")
      .attr("color", "#444444")
      .text(cnt_delta + "");

    chart.append("text")
      .attr("class", "label")
      .attr("x", x(data[1].label) + 47)
      .attr("y", y(data[1].value) - 10)
      .attr("text-anchor", "middle")
      .attr("color", "#444444")
      .text(cnt_signups + "");

    const mouseover = function(event, d) {
        tooltip.style("opacity", 1);
    };

    const mouseleave = function(event, d) {
        tooltip.style("opacity", 0);
    };

    const mousemove = function(event, d) {
        console.log(id + " .tooltip > .tooltip-text");
        const text = d3.select(id + " .tooltip > .tooltip-text");
        text.text(title + ": " + cnt_users);
        const [x, y] = d3.mouse(this);
        tooltip.attr("transform", "translate(" + x + ", " + y + ")");
    };

    svg.on("mouseover", mouseover)
        .on("mouseleave", mouseleave)
        .on("mousemove", mousemove);

}
