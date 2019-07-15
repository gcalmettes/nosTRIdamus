
// file specific variable
let raceslist


/***********************************/
/**** Activity profiles / info *****/
/***********************************/

const chartsConfig = {
  width: 450,
  height: 150,
  margins: {
    left: 50,
    top: 10,
    right: 10,
    bottom: 50
  }
}

const convert = {
  m2mile: 0.000621371,
  m2foot: 3.28
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
  .x(d => xScale(d.x*convert.m2mile))
  .y1(d => yScale(d.y*convert.m2foot))
  .curve(d3.curveBasis)

const drawChart = ({ activity, data }) => {
  xScale.domain(d3.extent(data, d => d.x*convert.m2mile))
  const [ yMin, yMax] = d3.extent(data, d => d.y*convert.m2foot)
  yScale.domain([yMin, yMax > yMin+500 ? yMax : yMin+500 ])
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

  g.selectAll('.axis-bottom-label')
    .data([null])
    .join(
      enter => enter.append('text')
        .attr('class', 'axis-bottom-label')
        .attr('transform', `translate(${(chartsConfig.width - chartsConfig.margins.left -  chartsConfig.margins.right)/2}, ${chartsConfig.height-chartsConfig.margins.top-chartsConfig.margins.bottom/2.5})`)
        .style("text-anchor", "middle")
        .style("font-size", 12)
        .text("Distance (mi)")
    )

  g.selectAll('.axis-left-label')
    .data([null])
    .join(
      enter => enter.append('text')
        .attr('class', 'axis-left-label')
        .attr('x', `${-(chartsConfig.height - chartsConfig.margins.top -  chartsConfig.margins.bottom)/2}`)
        .attr('y', `${-chartsConfig.margins.left/1.5}`)
        .attr('transform', `rotate(-90)`)
        .style("text-anchor", "middle")
        .style("text-align", "center")
        .style("font-size", 12)
        .text("Elevation (ft)")

    )
}

const addActivityInfo = ({ activity, data }) => {
  // elevation gain
  const activityInfo = document.getElementById(`${activity}-info`)
  activityInfo.textContent = `Elevation gain: ${(data.elevation*convert.m2foot).toFixed(0)} ft`

  // weather info
  const weatherInfo = document.getElementById(`weather-info`)
  weatherInfo.textContent = `${data.weatherSummary}`

  // by default, icons are black but you can color them
  // const skycons = new Skycons({"color": "pink"});

  // If you want to add more colors :
  // var skycons = new Skycons({"monochrome": false});
  // you can now customize the color of different parts
  // main, moon, fog, fogbank, cloud, snow, leaf, rain, sun
  const skycons = new Skycons({
   monochrome: false,
   colors: {
     cloud: '#C0C0C8',
     snow: '#1FBAD6',
     leaf: '#8EBA42',
     rain: '#1FBAD6', 
     sun: '#FBC15E',
     fog: '#C0C0C8',
     fogbank: 'fogbank',
   }
   });

  skycons.set("weather-icon", data.weatherIcon);
  // start animation!
  skycons.play();
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
  isSelection: isSelect,
  slots: d.wc_slots,
  fieldSize: d.entrants_count_avg,
  runScore: d.run_score,
  bikeScore: d.bike_score,
  bikeSinusoity: d.bike_sinusoity,
  attractiveness: d.attractivity_score,
  airport: convert.m2mile*1000*d.distance_to_nearest_airport,
  airportInternational: convert.m2mile*1000*d.distance_to_nearest_airport_international,
  hotels: d.n_hotels,
  food: d.n_restaurants, 
  entertainment: d.n_entertainment
})

const getKey = (obj,val) => Object.keys(obj).find(key => obj[key] === val)

/****************************/
/**** GET RECOMMENDATIONS ***/
/****************************/

// submit button
document.getElementById("get-recommendations-button")
  .addEventListener('click', () => {
    // Get the chosen race and trim it
    const pickedRace = document.getElementById('race-input').value.trim()
    showRecommendations(pickedRace)
  })

// change in filter options (all / full / half)
$('#races-filter').on('change', e => {
  const pickedRace = document.getElementById('race-input').value.trim()
  showRecommendations(pickedRace)
});

// race experience
$('input[data-slider-id=slider-raceexperience]').on('change', e => {
  const pickedRace = document.getElementById('race-input').value.trim()
  showRecommendations(pickedRace)
})
// race difficulty
$('input[data-slider-id=slider-racedifficulty]').on('change', e => {
  const pickedRace = document.getElementById('race-input').value.trim()
  showRecommendations(pickedRace)
})
// race size
$('input[data-slider-id=slider-racesize]').on('change', e => {
  const pickedRace = document.getElementById('race-input').value.trim()
  showRecommendations(pickedRace)
})



let isAdvancedChecked = false

function checkRaceValidity(pickedRace){
  if (pickedRace) {
    if (raceslist[pickedRace]) {
      return true
    } else {
      $('#empty-field-alert-text').text("Sorry we didn't find that race.")
      $('#empty-field-alert').css('display', 'block')
      $('#empty-field-alert').toggleClass('alert-warning', false)
      $('#empty-field-alert').toggleClass('warning-race', false);
      $('#empty-field-alert').toggleClass('alert-danger', true)
      $('#empty-field-alert').toggleClass('danger-race', true);
      return false
    }
  } else {
    $('#empty-field-alert-text').text('Please fill in a race!')
    $('#empty-field-alert').css('display', 'block')
    $('#empty-field-alert').toggleClass('alert-danger', false)
    $('#empty-field-alert').toggleClass('danger-race', false);
    $('#empty-field-alert').toggleClass('alert-warning', true)
    $('#empty-field-alert').toggleClass('warning-race', true);
    return false
  }
}

function getOptionsStatus(){
  const filterRace = document.querySelector('input[name="options"]:checked').value
  const raceExperience = document.querySelector('input[data-slider-id=slider-raceexperience]').value
  const raceDifficulty = document.querySelector('input[data-slider-id=slider-racedifficulty]').value
  const raceSize = document.querySelector('input[data-slider-id=slider-racesize]').value
  const months_range = shared['months_range']
  return {filterRace, raceExperience, raceDifficulty, raceSize, months_range}
}

async function showRecommendations(pickedRace){
  const isValidInput = checkRaceValidity(pickedRace)

  // don't go ahead if race input is not valid
  if (!isValidInput) return
  
  const {filterRace, raceExperience, raceDifficulty, 
         raceSize, months_range} = getOptionsStatus()

  const locations = await sendRequest({ 
    url: '/recommend', 
    args: {
      race: raceslist[pickedRace], 
      filterBy: filterRace,
      options: {
        raceExperience: raceExperience,
        raceDifficulty: raceDifficulty,
        raceSize: raceSize
      },
      model: Number(isAdvancedChecked),
      months_range
    }, 
    method: 'POST' 
  }).then(d => {
      const results = d.data

      tabulate({ 
        id: 'result-table', 
        columns: [
          {id: 'racename', name: 'Race'},
          {id: 'country_code', name: 'Country'},
          {id: 'region', name: 'Region'}
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
          shared.centerGlobeTo({lat: element.lat, lon: element.lon})

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
  // the last location is the reference point
  const [lon, lat] = newLocations[newLocations.length-1].coordinates
  shared.centerGlobeTo({lat: lat, lon: lon})
  
  // preload images
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
    drawChart({ activity: 'bike', data: json.data['bike_elevation_map'] })
    drawChart({ activity: 'run', data: json.data['run_elevation_map'] })
    addActivityInfo({ activity: 'bike', data: {
      elevation: json.data['bike_elevationGain'],
      weatherSummary: json.data['weather_summary']
    } })
    addActivityInfo({ activity: 'run', data:  {
      elevation: json.data['run_elevationGain'],
      weatherSummary: json.data['weather_summary'],
      weatherIcon: json.data['weather_icon']
    } })
    // console.log(json.data)
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
    {id: 'region', name: 'Region'}
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


/*******************************/
/*********** SLIDERS ***********/
/*******************************/

const slider = d3.select('#slider-months')
triggerOnResize(() => {
  // brush responsive on resize
  slider_snap({
    container: slider,
    margin: {
      top: 20,
      bottom: 20,
      left: 20,
      right: 20
    } 
  })
})

const sliderRaceDifficulty = new Slider("#slider-racedifficulty", {
  precision: 1,
  step: 0.5,
  value: 3,
  min: 1,
  max: 5
});

const sliderRaceSize = new Slider("#slider-racesize", {
  precision: 1,
  step: 0.5,
  value: 3,
  min: 1,
  max: 5
});

const screenDiv = document.getElementById('screen')
const switchLabel = document.getElementById('custom-switch-label')

document.getElementById('switchControls').addEventListener('change', function(e) {
  isAdvancedChecked = e.target.checked
  if (e.target.checked) {
    screenDiv.style.display='none'
    switchLabel.textContent = 'ON'
    switchLabel.style = 'color: #348ABD;'
  } else {
    screenDiv.style.display='block'
    switchLabel.textContent = 'OFF'
    switchLabel.style = 'color: #E24A33;'
  }
  const pickedRace = document.getElementById('race-input').value.trim()
  showRecommendations(pickedRace)
})