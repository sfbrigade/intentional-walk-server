import { useEffect, useRef } from "react";
import * as d3 from "d3";

function IntensityMap({
  data,
  map,
  onMouseOver,
  minColor,
  maxColor,
  width,
  height,
}) {
  const ref = useRef();

  useEffect(() => {
    if (data && map && width && height) {
      // set up map projection
      const projection = d3
        .geoMercator()
        .scale(120000)
        .center([-122.44, 37.76])
        .translate([width / 2, height / 2]);

      // set up color gradient
      const colorScale = d3
        .scaleLinear()
        .domain([1, Math.floor(Math.max(...Object.values(data)))])
        .range([minColor, maxColor]);

      // draw map
      const el = d3.select(ref.current);
      el.selectAll("*").remove();
      el.append("g")
        .selectAll("path")
        .data(map)
        .enter()
        .append("path")
        // draw each neighborhood
        .attr("d", d3.geoPath().projection(projection))
        .attr("stroke", "#f0f0f0")
        .attr("fill", (feature) => colorScale(data[feature.id] ?? 0))
        .on("mouseover", (_, feature) => onMouseOver(feature))
        .on("mouseout", () => onMouseOver());
    }
  }, [data, map, width, height]);

  return <svg ref={ref} width={width} height={height} />;
}

export default IntensityMap;
