import { useEffect, useRef } from "react";
import * as d3 from "d3";

function BarChart({ data, width, height, minColor, maxColor }) {
  const ref = useRef();

  useEffect(() => {
    if (data && width && height && minColor && maxColor) {
      const margin = {
        left: 40,
        top: 30,
        right: 0,
        bottom: 30,
      };
      const content = {
        width: width - margin.left - margin.right,
        height: height - margin.top - margin.bottom,
      };
      const groups_domain = data.map((e) => e.label);

      const el = d3.select(ref.current);
      el.selectAll("*").remove();

      const chart = el
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

      // x-axis
      const x = d3
        .scaleBand()
        .domain(groups_domain)
        .range([0, content.width])
        .padding(0.3);

      chart
        .append("g")
        .attr("transform", `translate(0, ${content.height})`)
        .call(d3.axisBottom(x));

      // y-axis
      const y = d3
        .scaleLinear()
        .domain([0, data.reduce((max, e) => Math.max(max, e.value), 0)])
        .range([content.height, 0]);

      chart.append("g").call(d3.axisLeft(y));

      // data bars
      const color = d3
        .scaleOrdinal()
        .domain(groups_domain)
        .range([minColor, maxColor]);

      chart
        .selectAll()
        .data(data)
        .enter()
        .append("g")
        .append("rect")
        .attr("x", (e) => x(e.label))
        .attr("y", (e) => y(e.value))
        .attr("width", x.bandwidth())
        .attr("height", (e) => content.height - y(e.value) + "px")
        .attr("fill", (e) => color(e.label));

      // labels under the bars
      for (const e of data) {
        chart
          .append("text")
          .attr("class", "h6")
          .attr("x", x(e.label) + x.bandwidth() / 2)
          .attr("y", y(e.value) - 10)
          .attr("text-anchor", "middle")
          .attr("color", "#444444")
          .text(e.value + "");
      }
    }
  }, [data, width, height, minColor, maxColor]);

  return <svg ref={ref} width={width} height={height} />;
}

export default BarChart;
