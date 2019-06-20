
// file specific variable
let raceslist

const chartsConfig = {
  width: 400,
  height: 150,
  margins: {
    left: 50,
    top: 10,
    right: 10,
    bottom: 50
  }
}

const xScale = d3.scaleLinear()
  .range([0, chartsConfig.width - chartsConfig.margins.left - chartsConfig.margins.right ])
const yScale = d3.scaleLinear()
  .range([chartsConfig.height - chartsConfig.margins.top - chartsConfig.margins.bottom, 0])

const axisLeft = d3.axisLeft()
  .scale(yScale)
  .ticks(5)
const axisBottom = d3.axisBottom()
  .scale(xScale)
  .ticks(5)

const activityLine = d3.area()
  .x(d => xScale(d.x))
  .y1(d => yScale(d.y))
  .curve(d3.curveCatmullRom.alpha(0.5))

const drawChart = ({ activity, data }) => {
  xScale.domain(d3.extent(data, d => d.x))
  const [ yMin, yMax] = d3.extent(data, d => d.y)
  yScale.domain([yMin, yMax > 300 ? yMax : 300 ])
  activityLine
    .y0(d => yScale(yMin))

  let svg = d3.select(`#${activity}-elevation-chart`).selectAll(`.activity-svg`)
    .data([null])
    .join('svg')
        .attr('class', `activity-svg`)
        .attr('width', chartsConfig.width )
        .attr('height', chartsConfig.height )
      
  let g = svg.selectAll('.activity-chart')
    .data([null])
    .join(
      enter => enter.append('g')
        .attr('class', 'activity-chart')
        .attr('transform', `translate(${chartsConfig.margins.left}, ${chartsConfig.margins.top})`),
    )

  g.selectAll('path')
    .data([data])
    .join(
      enter => enter.append('path')
        .attr("d", activityLine),
      update => update
        .attr("d", activityLine)
    )

  g.selectAll('.axis-left')
    .data([null])
    .join(
      enter => enter.append('g')
        .attr('class', 'axis-left')
        .attr('transform', `translate(${0}, ${0})`)
        .call(axisLeft),
      update => update
        .call(axisLeft)
    )

  g.selectAll('.axis-bottom')
    .data([null])
    .join(
      enter => enter.append('g')
        .attr('class', 'axis-bottom')
        .attr('transform', `translate(${0}, ${chartsConfig.height-chartsConfig.margins.top-chartsConfig.margins.bottom})`)
        .call(axisBottom),
      update => update
        .call(axisBottom)
    )
    
}


/****************************/
/********** UTILS ***********/
/****************************/


const makePoint = (d, isTarget, isSelect) => ({
  type: "Point", 
  coordinates: [d.lon, d.lat], 
  id: d.race,
  name: d.racename,
  img: d.image_url || 'https://s3-us-west-2.amazonaws.com/obstri/defaultim.jpg',
  url: d.imlink,
  countryCode: d.country_code,
  city: d.city,
  date: d.date,
  isTarget: isTarget,
  isSelection: isSelect
})

const getKey = (obj,val) => Object.keys(obj).find(key => obj[key] === val)

/****************************/
/**** GET RECOMMENDATIONS ***/
/****************************/

async function showRecommendations(){

  const pickedRace = document.getElementById('race-input').value
  const filterRace = document.querySelector('input[name="options"]:checked').value
  const pickedModel = document.getElementById('modelSelect').value

  const locations = await sendRequest({ 
    url: '/recommend', 
    args: {
      race: raceslist[pickedRace], 
      filterBy: filterRace,
      model: pickedModel
    }, 
    method: 'POST' 
  }).then(d => {
      const results = d.data

      tabulate({ 
        id: 'result-table', 
        columns: [
          {id: 'racename', name: 'Race'},
          {id: 'country_code', name: 'Country'},
          {id: 'similarity', name: 'Metric'}
        ],
        data: results.slice(1, results.length), // remove first row since it's the race itself,
        mouseOver: (row, i, array) => {
          d3.select(array[i]).classed('highlighted', true)
          const newLocations = locations.map((d, i) => ({ 
            type: "Point", 
            coordinates: [d.lon, d.lat], 
            'id': d.race,
            'name': d.racename,
            isTarget: i == 0,
            isSelection: d.race == row.race
          })).reverse() 
    
          shared.setLocations({ cities: newLocations })
          shared.drawLocations()
          // show tooltip
          const element = locations.filter(d => d.race == row.race)[0]
          shared.showInfo( makePoint(element, false, true))

        },
        mouseOut: (row, i, array) => {
          d3.select(array[i]).classed('highlighted', false)
          const newLocations = locations.map((d, i) => makePoint(d, i==0, false)).reverse() 
    
          shared.setLocations({ cities: newLocations })
          shared.drawLocations()
          shared.showInfo( null ) // hide tooltip
        }
      })

      return results
    })

    const newLocations = locations.map((d, i) => makePoint(d, i==0, false)).reverse()
    shared.resetInfo() 
    shared.setLocations({ cities: newLocations })
    shared.drawLocations()

    // pre-load the images
    const imgs = {}
    for (const loc of newLocations ){
      imgs[loc.race] = new Image()
      imgs[loc.race].src = loc.img
    }
}


/****************************/
/******* GET MAP INFO *******/
/****************************/

async function showMaps(){

  const pickedRace = document.getElementById('info-raceid').getAttribute('value')
  const racename = getKey(raceslist, pickedRace)

  document.getElementById('moreInfoLabel').textContent = `More info about ${racename}`

  // get map data
  const maps = await sendRequest({ 
    url: '/racemap', 
    args: {
      race: pickedRace
    }, 
    method: 'POST' 
  })
  .then(json => {
    drawChart({activity: 'bike', data: json.data['bike_elevation_map']})
    drawChart({activity: 'run', data: json.data['run_elevation_map']})
    console.log(json.data)
    // console.log(JSON.parse(json.data['run_elevation_map']))
    // console.log(JSON.parse(json.data))
  })
}


/*******************************/
/**** INITIALIZATION ON PAGE ***/
/*******************************/

// initialize table
tabulate({ 
  id: 'result-table', 
  columns: [
    {id: 'racename', name: 'Race'},
    {id: 'country_code', name: 'Country'},
    {id: 'similarity', name: 'Metric'}
  ],
  data: []
})

// get the race list for text suggestion autocompletion
sendRequest({ url: '/racelist', method: 'GET' })
  .then(json => {
    const races = json.data

    // update global variable racelist
    // swap key/values for fast lookup later
    raceslist = Object.keys(races)
      .reduce((obj, key) => ({ ...obj, [races[key]]: key }), {})

    autocomplete(document.getElementById("race-input"), Object.values(races))
  })


// // Without JQuery
// var slider = new Slider("#ex6");
// slider.on("slide", function(sliderValue) {
//   document.getElementById("ex6SliderVal").textContent = sliderValue;
// });
