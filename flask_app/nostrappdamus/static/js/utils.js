const triggerOnResize = fn => {
  fn();
  window.addEventListener('resize', fn);
}

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

const tabulate = ({ id, columns = [], data = [],
                    onMouseOver = (d) => {}, onMouseOut = (d) => {},
                    onClick = (d) => {}
                  }) => {
  const table = d3.select(`#${id}`)
  const thead = table.selectAll('thead')
    .data([null])
    .join(enter => enter.append('thead'))

  const tbody = table.selectAll('tbody')
    .data([null])
    .join(enter => enter.append('tbody'))

  // append the header row
  thead.selectAll('tr')
      .data([null])
      .join(enter => enter.append('tr'))
    .selectAll('th')
      .data(columns)
      .join(
        enter => enter
          .append('th')
          .text(col => col.name ),
        update => update
          .text(col => col.name )
      )

  // create a row for each object in the data
  const rows = tbody.selectAll('tr')
      .data(data)
      .join(enter => enter.append('tr'))
      .on('mouseover', (d, i, k) => onMouseOver(d, i, k))
      .on('mouseout', (d, i, k) => onMouseOut(d, i, k))
      .on('click', (d, i, k) => onClick(d, i, k))
  
  rows.selectAll('td')
      .data(row => columns.map(
        col => ({ column: col.id, value: row[col.id] })
      ))
      .join(
        enter => enter
          .append('td')
          .text(d => d.value ),
        update => update
          .text(d => d.value )
      )
  }
