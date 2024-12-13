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
    if (data && map && width && height && minColor && maxColor && onMouseOver) {
      // set up map projection
      const projection = d3
        .geoMercator()
        .scale(120000)
        .center([-122.44, 37.76])
        .translate([width / 2, height / 2]);

      // The largest value could still be 0 ...
      const maxDataValue = Math.floor(Math.max(...Object.values(data)));

      // Ensure the upperLimit is at least greater than 0,
      // so that we don't have a scale of [0, 0]
      const upperLimit = Math.max(maxDataValue, 1);
      // set up color gradient
      const colorScale = d3
        .scaleLinear()
        .domain([0, upperLimit])
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
        // use a dark stroke so that even when the value for a region is empty (0), there
        // is still a visible outline of the neighborhood.
        .attr("stroke", "#000000")
        .attr("fill", (feature) => colorScale(data[feature.id] ?? 0))
        .on("mouseover", (_, feature) => onMouseOver(feature))
        .on("mouseout", () => onMouseOver());
    }
  }, [data, map, width, height, minColor, maxColor, onMouseOver]);

  return <svg ref={ref} width={width} height={height} />;
}

export default IntensityMap;
