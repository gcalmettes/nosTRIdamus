const container = d3.select('#globe')

// div to be used to put info when mouseover
const tooltip = d3.select("body")
  .append("div") 
    .attr("class", "tooltip")       
    .style("opacity", 0)

let updateWorld, 
    drawWorld, 
    drawLocations,
    setLocations,
    timerWorld,
    runTimerWorld = true


d3.json("https://unpkg.com/world-atlas/world/110m.json")
    .then(worldData => {
      const world = topojson.feature(worldData, worldData.objects.land)
      const { updateScene, drawGlobeOnCanvas, drawLocationOnSVG, updateLocations } = renderWorld({ world })

      // update global variables
      updateWorld = updateScene
      drawWorld = drawGlobeOnCanvas
      drawLocations = drawLocationOnSVG
      setLocations = updateLocations

      triggerOnResize(() => updateWorld())

    })
    .catch(error => console.log(error))


function renderWorld({ world }) {

  let { canvas, svg, g, width, height } = createCanvasSvgLayers({ selection: container, className: 'globe' })

  context = canvas.node().getContext("2d");

  // retina display
  const devicePixelRatio = window.devicePixelRatio || 1
  canvas.style('width', canvas.attr('width')+'px')
  canvas.style('height', canvas.attr('height')+'px')
  canvas.attr('width', canvas.attr('width') * devicePixelRatio)
  canvas.attr('height', canvas.attr('height') * devicePixelRatio)
  context.scale(devicePixelRatio,devicePixelRatio)

  // projections
  const projection = d3.geoOrthographic()
      .scale(1)
      .translate([0, 0])
      .rotate([-10,-30])
  const backprojection = d3.geoProjection((a,b) => d3.geoOrthographicRaw(-a,b))
      .clipAngle(90)
      .translate(projection.translate())
      .scale(projection.scale())
  const pathCanvas = d3.geoPath()
      .projection(projection)
      .context(context)
  const backpathCanvas = d3.geoPath()
      .projection(backprojection)
      .context(context)
  const pathSvg = d3.geoPath()
      .projection(projection)


  // initial setup
  let locations = [] // no city locations
  updateScene()

  // rotating earth
  const velocity = .01
  if (runTimerWorld) {
    timerWorld = d3.timer(elapsed => {
      const rotate = projection.rotate()
      rotate[0] += velocity * 20
      projection.rotate(rotate)

      drawGlobeOnCanvas()
      drawLocationOnSVG()
    })
  }

  // Set up Fil's d3-geoInertia
   const inertia = d3.geoInertiaDrag(svg, () => {
    runTimerWorld = false
    timerWorld.stop();
    drawGlobeOnCanvas()
    drawLocationOnSVG()
  }, projection)


  // FUNCTIONS

  function updateLocations({ cities }) {
    locations = cities
  }

  function updateScene(){
    const containerInfo = container.node().getBoundingClientRect()
    width = containerInfo.width
    height = containerInfo.height
    updateProjection()
    drawGlobeOnCanvas()
    drawLocationOnSVG()
  }

  function updateProjection(){
    // Compute the bounds of the land, then derive scale & translate.
    const bounds = [[-1, -1], [1, 1]] //path.bounds(world),
          scale = 1 / Math.max((bounds[1][0] - bounds[0][0]) / width, (bounds[1][1] - bounds[0][1]) / height),
          translate = [(width - scale * (bounds[1][0] + bounds[0][0])) / 2, (height - scale * (bounds[1][1] + bounds[0][1])) / 2]

    // Update the projection to use computed scale & translate.
    projection
        .scale(scale)
        .translate(translate);

    // update corresponding backprojection
    backprojection
        .translate(projection.translate())
        .scale(projection.scale())
  }

  function drawGlobeOnCanvas() {

    // update backprojection
    const rotate = projection.rotate()
    backprojection
        .rotate([rotate[0] + 180, -rotate[1], -rotate[2]])

    // drawing commands
    context.clearRect(0, 0, width, height)

    context.beginPath();
    pathCanvas({type:"Sphere"});
    context.fillStyle = '#fcfcfc';
    context.fill();

    context.beginPath();
    backpathCanvas(world);
    context.fillStyle = '#d0ddfa';
    context.fill();
    context.beginPath();
    backpathCanvas(d3.geoGraticule()());
    context.lineWidth = .1;
    context.strokeStyle = '#97b3f6';
    context.stroke();
      

    context.beginPath();
    pathCanvas(d3.geoGraticule()());
    context.lineWidth = .1;
    context.strokeStyle = '#1046c6';
    context.stroke();

    context.beginPath();
    pathCanvas(world);
    context.lineWidth = 1;
    context.strokeStyle = '#1046c6';
    context.stroke();
    context.fillStyle = '#5c88ee';
    const alpha = context.globalAlpha;
    context.globalAlpha = 1;
    context.fill();
    context.globalAlpha = alpha;

    context.beginPath();
    pathCanvas({type: "Sphere"});
    context.lineWidth = .1;
    context.strokeStyle = '#1046c6';
    context.stroke();
  } // drawGlobeOnCanvas

  function drawLocationOnSVG() {
    const className = 'race-location'
    const races = svg.selectAll(`.${className}`)
      .data(locations)
      .join(
        enter => enter.append('path')
            .attr('class', className)
            .attr('d', pathSvg)
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
        update => update.attr('d', pathSvg)
      )
  } // drawLocationOnSVG

  return { updateScene, drawGlobeOnCanvas, drawLocationOnSVG, updateLocations }
}


/* --------------------------------------------- */
/* ----------------- FUNCTIONS ----------------- */
/* --------------------------------------------- */

function triggerOnResize(fn){
  fn();
  window.addEventListener('resize', fn);
}

function createCanvasSvgLayers({selection, className = 'main' }){
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
