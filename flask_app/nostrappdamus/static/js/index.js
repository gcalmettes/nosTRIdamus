
// global variable
let raceslist

async function redraw(){

  const pickedRace = document.getElementById('race-input').value
  const filterRace = document.querySelector('input[name="options"]:checked').value

  const locations = await sendRequest({ 
    url: '/recommend', 
    args: {
      race: raceslist[pickedRace], 
      filterBy: filterRace
    }, 
    method: 'POST' 
  }).then(d => {
      const results = d.data

      // add results to table
      const resultTable = document.getElementById('result-table')
      // remove old results
      resultTable.querySelectorAll('tr')
        .forEach((d, i) => i > 0 && d.remove())

      results.forEach((d, i) => {
        if (i > 0) {
          // skip the first row at it is the target race
          const row = createTableRow({
            'race': d.racename,
            'location': d.country_code,
            'distance': d.similarity
          })
          resultTable.appendChild(row)
        }
      })
      return results
    })

    const newLocations = locations.map((d, i) => ({ 
      type: "Point", 
      coordinates: [d.lon, d.lat], 
      'name': d.racename, 
      istarget: i == 0 
    })).reverse() 
    
    setLocations({ cities: newLocations })

    drawLocations()
}


// get the race list for text suggestion
sendRequest({ url: '/racelist', method: 'GET' })
  .then(json => {
    const races = json.data

    // swap key/values for fast lookup later
    raceslist = Object.keys(races)
      .reduce((obj, key) => ({ ...obj, [races[key]]: key }), {})

    autocomplete(document.getElementById("race-input"), Object.values(races))
  })