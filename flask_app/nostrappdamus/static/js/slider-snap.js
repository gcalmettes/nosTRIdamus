// Those will be global variables shared between the different
// js files

shared['months_range'] = [0, 12]

function slider_snap({ 
    container,
    margin = {
      top: 50,
      bottom: 50,
      left: 40,
      right: 40
    } 
  }) {

  let {width, height} = container.node().getBoundingClientRect()

  height = height == 0 ? 70 : height

  // dimensions of slider bar
  const w = width - margin.left - margin.right;
  const h = height - margin.top - margin.bottom;

  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const data = [...monthNames.map((d,i) => ({'name': d, idx: i})), {name: '', idx: monthNames.length}]
  
  // create x scale
  var x = d3.scaleLinear()
    .domain(d3.extent(data, d=>d.idx))  // data space
    .range([0, w]);  // display space

  // create svg and translated g
  const svg = container.selectAll('svg')
    .data([null])
    .join(enter => enter
      .append('svg')
      .attr('width', width)
      .attr('height', height)
    )
  const g = svg.selectAll('.g-slider')
    .data([null])
    .join(enter => enter
      .append('g')
      .attr('class', 'g-slider')
      .attr('transform', `translate(${margin.left}, ${margin.top})`)
    )

  // draw background lines
  g.selectAll('line')
    .data(data)
    .join(enter => enter.append('line')
      .attr('x1', d => x(d.idx))
      .attr('x2', d => x(d.idx))
      .attr('y1', 0)
      .attr('y2', h)
      .style('stroke', '#ccc'),
      update => update
        .attr('x1', d => x(d.idx))
        .attr('x2', d => x(d.idx))
    )
  
  // labels
  const labelL = g.selectAll('.labelLeft')
    .data([null])
    .join(enter => enter
      .append('text')
      .attr('class', 'labelLeft')
      .attr('id', 'labelleft')
      .attr('x', 0)
      .attr('y', h + 15)
      .text(data[0].name)
    )
  const labelR = g.selectAll('.labelRight')
    .data([null])
    .join(enter => enter
      .append('text')
      .attr('class', 'labelRight')
      .attr('id', 'labelright')
      .attr('x', w)
      .attr('y', -5)
      .text(data[data.length-2].name)
    )


  // define brush
  const brush = d3.brushX()
    .extent([[0,0], [w, h]])
    .on('brush', function() {
      const s = d3.event.selection;
      // update and move labels
      labelL
        .attr('x', s[0]-(x(1)-x(0))/2)
        .text(data[Math.round(x.invert(s[0]))].name)
      labelR
        .attr('x', s[1]-(x(1)-x(0))/2)
        .text(data[Math.round(x.invert(s[1])) - 1].name)
      // move brush handles      
      handle.attr("display", null)
        .attr("transform", function(d, i) { return "translate(" + [ s[i], - h / 4] + ")"; });
      // update view
      // if the view should only be updated after brushing is over, 
      // move these two lines into the on('end') part below
      // svg.node().value = s.map(d => Math.round(x.invert(d)));
      // svg.node().dispatchEvent(new CustomEvent("input"));
    })
    .on('end', function() {
      if (!d3.event.sourceEvent) return;
      const d0 = d3.event.selection.map(x.invert);
      const d1 = d0.map(Math.round)
      d3.select(this)
        .transition()
        .call(d3.event.target.move, d1.map(x))

      // reflect selection in global variable
      shared['months_range'] = d1
    })

  // append brush to g
  const gBrush = g.selectAll('.brush')
    .data([null])
    .join(enter => enter.append("g")
      .attr("class", "brush")
      .call(brush)
    )

  // add brush handles (from https://bl.ocks.org/Fil/2d43867ba1f36a05459c7113c7f6f98a)
  const brushResizePath = function(d) {
      var e = +(d.type == "e"),
          x = e ? 1 : -1,
          y = h / 2;
      return "M" + (.5 * x) + "," + y + "A6,6 0 0 " + e + " " + (6.5 * x) + "," + (y + 6) + "V" + (2 * y - 6) +
        "A6,6 0 0 " + e + " " + (.5 * x) + "," + (2 * y) + "Z" + "M" + (2.5 * x) + "," + (y + 8) + "V" + (2 * y - 8) +
        "M" + (4.5 * x) + "," + (y + 8) + "V" + (2 * y - 8);
  }

  const handle = gBrush.selectAll(".handle--custom")
    .data([{type: "w"}, {type: "e"}])
    .join(enter => enter.append("path")
      .attr("class", "handle--custom")
      .attr("stroke", "#000")
      .attr("fill", '#eee')
      .attr("cursor", "ew-resize")
      .attr("d", brushResizePath)
    )

  // override default behaviour - clicking outside of the selected area 
  // will select a small piece there rather than deselecting everything
  // https://bl.ocks.org/mbostock/6498000
  gBrush.selectAll(".overlay")
    .each(function(d) { d.type = "selection"; })
    .on("mousedown touchstart", brushcentered)

  function brushcentered() {
    const dx = x(1) - x(0), // Use a fixed width when recentering.
    cx = d3.mouse(this)[0],
    x0 = cx - dx / 2,
    x1 = cx + dx / 2;
    d3.select(this.parentNode)
      .call(brush.move, x1 > width ? [width - dx, width] : x0 < 0 ? [0, dx] : [x0, x1]);
  }
  
  // select entire range
  gBrush
    // .call(brush.move, [data[0], data[data.length-1]].map(d => x(d.idx)))
    .call(brush.move, shared['months_range'].map(d => x(d)))

}