
// file specific variable
let raceslist

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
          shared.showInfo( {coordinates: [element.lon, element.lat], name: row.racename } )

        },
        mouseOut: (row, i, array) => {
          d3.select(array[i]).classed('highlighted', false)
          const newLocations = locations.map((d, i) => ({ 
            type: "Point", 
            coordinates: [d.lon, d.lat], 
            'id': d.race,
            'name': d.racename,
            isTarget: i == 0,
            isSelection: false
          })).reverse() 
    
          shared.setLocations({ cities: newLocations })
          shared.drawLocations()

          // hide tooltip
          const element = locations.filter(d => d.race == row.race)[0]
          shared.hideInfo( {coordinates: [element.lon, element.lat], name: row.racename } )
        }
      })

      return results
    })

    const newLocations = locations.map((d, i) => ({ 
      type: "Point", 
      coordinates: [d.lon, d.lat], 
      'id': d.race,
      'name': d.racename,
      isTarget: i == 0,
      isSelection: false
    })).reverse() 
    
    shared.setLocations({ cities: newLocations })

    shared.drawLocations()

}

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


// get the race list for text suggestion
sendRequest({ url: '/racelist', method: 'GET' })
  .then(json => {
    const races = json.data

    // update global variable racelist
    // swap key/values for fast lookup later
    raceslist = Object.keys(races)
      .reduce((obj, key) => ({ ...obj, [races[key]]: key }), {})

    autocomplete(document.getElementById("race-input"), Object.values(races))
  })