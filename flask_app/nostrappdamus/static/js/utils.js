const postData = (url = '', data = {}) => {
  return fetch(url, {
      method: 'POST', // *GET, POST, PUT, DELETE, etc.
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
      },
      body: JSON.stringify(data),
    })
    .then(response => response.json())
}

const createTableRow = data => {
  const row = document.createElement('tr')

  Object.values(data)
    .forEach(value => {
      // const value = data[key]
      const td = document.createElement('td')
      td.textContent = value
      row.appendChild(td)
    })

  return row
}

// const submit = (random=false) => {

//   // radio buttons selection
//   const selectedValue = document.querySelector('input[name="inlineRadioOptions"]:checked').value;

//   // input from text box
//   const text = document.getElementById('method').value

//   // result table
//   const resultTable = document.getElementById('result-table')

//   const url = random 
//     ? 'http://127.0.0.1:5000/data/random'
//     : 'http://127.0.0.1:5000/data'

//   return postData(url, {filterBy: text, selection: selectedValue})
//     .then(data => {
//       resultTable.querySelectorAll('tr')
//         .forEach((d, i) => i > 0 && d.remove())

//       const results = data.data ? data.data.slice(1, 10) : []
//       results
//         .forEach(d => {
//           const row = createTableRow({
//             'birth_month': d.birth_month,
//             'attendant': d.attendant,
//             'weight': d.birth_weight,
//             'year': d.birth_year
//           })
//           resultTable.appendChild(row)
//         })
//       return data
//     })
//     .catch(error => console.error(error))
//   }