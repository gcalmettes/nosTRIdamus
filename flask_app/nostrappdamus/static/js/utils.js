const sendRequest = config => {
  const { url = '', args = {}, method = 'POST' } = config
  let request
  if (method == 'POST') {
    request = fetch(url, {
      method: 'POST', // *GET, POST, PUT, DELETE, etc.
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
      },
      body: JSON.stringify(args),
    })
  } else if (method == 'GET') {
    const queryString = `${url}?` + Object.entries(args)
      .map(([key,value]) => `${key}=${value}`)
      .join('&')

    request = fetch(queryString, {method: 'GET'})
  }
  return request.then(response => response.json())
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
