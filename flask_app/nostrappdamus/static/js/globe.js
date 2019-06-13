const container = document.getElementById('globe');

const tooltip = d3.select("body")
  .append("div") 
    .attr("class", "tooltip")       
    .style("opacity", 0);

// don't reload data on resize
let land,
    timer,
    context, 
    svg_,
    g_,
    width_, 
    height_, 
    path, 
    path_svg,
    backpath, 
    projection, 
    backprojection,
    locations = [],
    initialized = false

async function globeComponent(selection, props) {
  const { className, locations } = props;
  const { canvas, svg, g, width, height } = createCanvas({ selection, className })

  // keep as global variables
  width_ = width
  height_ = height
  svg_ = svg
  g_ = g

  context = canvas.node().getContext("2d");

  // retina display
  const devicePixelRatio = window.devicePixelRatio || 1;
  canvas.style('width', canvas.attr('width')+'px');
  canvas.style('height', canvas.attr('height')+'px');
  canvas.attr('width', canvas.attr('width') * devicePixelRatio);
  canvas.attr('height', canvas.attr('height') * devicePixelRatio);
  context.scale(devicePixelRatio,devicePixelRatio);

  // load world data
  if (!land) {
    land = await d3.json("https://unpkg.com/world-atlas/world/110m.json")
      .then(world => topojson.feature(world, world.objects.land))
      .catch(error => console.log(error))
  }
  
  const velocity = .01;

  if (!initialized) {
    initialized = true
    projection = d3.geoOrthographic()
      .scale(1)
      .translate([0, 0])
      .rotate([-10,-30])
    path = d3.geoPath()
      .projection(projection)
      .context(context)
  } else {
    projection
      .scale(1)
      .translate([0, 0])
      .rotate(projection.rotate())
    path
      .projection(projection)
      .context(context)
  }

  path_svg = d3.geoPath(projection)

  // Compute the bounds of the land, then derive scale & translate.
  const bounds = path.bounds(land),
        scale = .9 / Math.max((bounds[1][0] - bounds[0][0]) / width, (bounds[1][1] - bounds[0][1]) / height),
        translate = [(width - scale * (bounds[1][0] + bounds[0][0])) / 2, (height - scale * (bounds[1][1] + bounds[0][1])) / 2]

  // Update the projection to use computed scale & translate.
  projection
      .scale(scale)
      .translate(translate);

  backprojection = d3.geoProjection((a,b) => d3.geoOrthographicRaw(-a,b))
    .clipAngle(90)
    .translate(projection.translate())
    .scale(projection.scale())

  backpath = d3.geoPath()
    .projection(backprojection)
    .context(context)

  drawGlobe({ context, svg, g, width, height, path, path_svg, backpath, land, projection, backprojection, locations })

  // if (timer) timer.stop()
  // timer = d3.timer(elapsed => {
  //   const rotate = projection.rotate();
  //   rotate[0] += velocity * 20;
  //   projection.rotate(rotate);
  //   drawGlobe({ context, svg: svg_, g: g_, width: width_, height: height_, path, path_svg, backpath, land, projection, backprojection, locations })
  // });
  
  d3.geoInertiaDrag(svg, () => drawGlobe({ context, svg: svg_, g: g_, width: width_, height: height_, path, path_svg, backpath, land, projection, backprojection, locations }))
  canvas.style('cursor', 'move')
}

function drawGlobe({ context, svg, g, width, height, path, backpath, land, projection, backprojection, locations }) {
  const rotate = projection.rotate()
  backprojection.rotate([rotate[0] + 180, -rotate[1], -rotate[2]])
  
  const races = g.selectAll('.race-location')
    .data(locations)
    .join(
      enter => enter.append('path')
          .attr('class', 'race-location')
          .attr('d', path_svg)
          .attr('fill', d => d.istarget ? '#E24A33' :'white')
          .attr('stroke', 'black')
          .on('mouseover', d => {    
            tooltip.transition()
              .duration(200)    
              .style("opacity", .9);    
            tooltip.html(d.name)  
              .style("left", (d3.event.pageX) + "px")   
              .style("top", (d3.event.pageY - 28) + "px") 
          })
          .on('mouseout', d => {   
            tooltip.transition()    
              .duration(500)    
              .style("opacity", 0)
            }),
      update => update
          .attr('d', path_svg)
      )

  context.clearRect(0, 0, width, height)

  context.beginPath();
  path({type:"Sphere"});
  context.fillStyle = '#fcfcfc';
  context.fill();

  context.beginPath();
  backpath(land);
  context.fillStyle = '#d0ddfa';
  context.fill();
  context.beginPath();
  backpath(d3.geoGraticule()());
  context.lineWidth = .1;
  context.strokeStyle = '#97b3f6';
  context.stroke();
    

  context.beginPath();
  path(d3.geoGraticule()());
  context.lineWidth = .1;
  context.strokeStyle = '#1046c6';
  context.stroke();

  context.beginPath();
  path(land);
  context.lineWidth = 1;
  context.strokeStyle = '#1046c6';
  context.stroke();
  context.fillStyle = '#5c88ee';
  const alpha = context.globalAlpha;
  context.globalAlpha = 1;
  context.fill();
  context.globalAlpha = alpha;

  context.beginPath();
  path({type: "Sphere"});
  context.lineWidth = .1;
  context.strokeStyle = '#1046c6';
  context.stroke();

}


function renderScene({ locations }) {
  // component(s) to render
  globeComponent(d3.select(container), {
    className: 'globe',
    locations
  });
}

triggerOnResize(() => renderScene({ locations }))


/* --------------------------------------------- */
/* ----------------- FUNCTIONS ----------------- */
/* --------------------------------------------- */

function triggerOnResize(fn){
  fn();
  window.addEventListener('resize', fn);
}

function createCanvas({selection, className }){
  className = className || 'main'
  const { x, y, width, height } = selection.node().getBoundingClientRect()

  let canvas = selection.selectAll(`.${className}-canvas`)
    .data([null])
    .join('canvas')
      .style('position', 'absolute')
      .attr('class', `${className}-canvas`)
      .attr('width', width )
      .attr('height', height)

  let svg = selection.selectAll(`.${className}-svg`)
    .data([null])
    .join('svg')
        .style('position', 'absolute')
        .attr('class', `${className}-svg`)
        .attr('width', width )
        .attr('height', height )
      
  let g = svg.selectAll(`.${className}-svg-g`)
    .data([null])
    .join(
      enter => enter.append('g')
        .attr('class', `${className}-svg-g`)
        .attr('transform', `translate(${0}, ${0})`),
        update => update
          .attr('transform', `translate(${0}, ${0})`)
    )

  return { canvas, svg, g, width, height }
}